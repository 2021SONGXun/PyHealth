from typing import List, Optional
from tokenize import Token
import numpy as np
from collections import defaultdict
from urllib import request
import os
import pandas as pd
from pathlib import Path
from pyhealth.data import Patient, TaskDataset
from pyhealth.models.tokenizer import Tokenizer

from tqdm import tqdm


class DrugRecVisit:
    """Contains information about a single visit (for drug recommendation task)"""

    def __init__(
        self,
        visit_id: str,
        patient_id: str,
        conditions: List[str] = [],
        procedures: List[str] = [],
        drugs: List[str] = [],
        labs: List[str] = [],
        physicalExams: List[str] = [],
        admission_time: float = 0.0,
    ):
        self.visit_id = visit_id
        self.patient_id = patient_id
        self.conditions = conditions
        self.procedures = procedures
        self.drugs = drugs
        self.labs = labs
        self.physicalExams = physicalExams
        self.admission_time = admission_time

    def __str__(self):
        return f"Visit {self.visit_id} of patient {self.patient_id}"


class DrugRecDataset(TaskDataset):
    """
    Dataset for drug recommendation task
    Transform the <BaseDataset> object to <TaskDataset> object
    """

    @staticmethod
    def remove_nan_from_list(list_with_nan):
        """
        e.g., [1, 2, nan, 3] -> [1, 2, 3]
        e.g., [1, 2, 3] -> [1, 2, 3]
        e.g., np.array([1, 2, nan, 3]) -> [1, 2, 3]
        """
        if (type(list_with_nan) != type([0, 1, 2])) and (
            type(list_with_nan) != type(np.array([0, 1, 2]))
        ):
            return []
        return [i for i in list_with_nan if not i != i]

    def get_code_from_list_of_Event(self, list_of_Event):
        """
        INPUT
            - list_of_Event: List[Event]
        OUTPUT
            - list_of_code: List[str]
        """
        list_of_code = [event.code for event in list_of_Event]
        list_of_code = np.unique(list_of_code)
        list_of_code = self.remove_nan_from_list(list_of_code)
        return list_of_code

    def preprocess(self):
        """clean the data for drug recommendation task"""

        # ---------- for drug coding ------
        from MedCode import CodeMapping

        tool = CodeMapping("RxNorm", "ATC4")
        tool.load()

        def get_atc3(x):
            # one rxnorm maps to one or more ATC3
            result = []
            for rxnorm in x:
                if rxnorm in tool.RxNorm_to_ATC4:
                    result += tool.RxNorm_to_ATC4[rxnorm]
            result = np.unique([item[:-1] for item in result]).tolist()
            return result

        # ---------------------

        processed_patients = {}
        for patient_id, patient_obj in tqdm(self.base_dataset.patients.items()):
            processed_visits = {}
            for visit_id, visit_obj in patient_obj.visits.items():
                conditions = self.get_code_from_list_of_Event(visit_obj.conditions)
                procedures = self.get_code_from_list_of_Event(visit_obj.procedures)
                drugs = self.get_code_from_list_of_Event(visit_obj.drugs)
                drugs = get_atc3(
                    ["{:011}".format(int(med)) for med in drugs]
                )  # drug coding
                # exclude: visits without condition, procedure, or drug code
                if (len(conditions) + len(procedures)) * len(drugs) == 0:
                    continue
                cur_visit = DrugRecVisit(
                    visit_id=visit_id,
                    patient_id=patient_id,
                    conditions=conditions,
                    procedures=procedures,
                    drugs=drugs,
                    admission_time=visit_obj.encounter_time,
                )

                processed_visits[visit_id] = cur_visit

            # exclude: patients with less than 2 visit
            if len(processed_visits) < 2:
                continue

            cur_pat = Patient(
                patient_id=patient_id,
                visits=[
                    v
                    for _, v in sorted(
                        processed_visits.items(),
                        key=lambda item: item[1].admission_time,
                    )
                ],  # sort the visits and change into a list
            )
            processed_patients[patient_id] = cur_pat

        print("1. finish cleaning the dataset for drug recommendation task")
        self.patients = processed_patients

        # get (0, N-1) to (patients, visit_pos) map
        self.index_map = {}
        self.index_group = []
        t = 0
        for patient_id, patient_obj in self.patients.items():
            group = []
            for pos in range(len(patient_obj.visits)):
                self.index_map[t] = (patient_id, pos)
                group.append(t)
                t += 1
            self.index_group.append(group)
        self.params = None

    def set_all_tokens(self):
        """tokenize by medical codes"""
        conditions = []
        procedures = []
        drugs = []
        for patient_id, patient_obj in self.patients.items():
            for visit_obj in patient_obj.visits:
                conditions.extend(visit_obj.conditions)
                procedures.extend(visit_obj.procedures)
                drugs.extend(visit_obj.drugs)
        conditions = list(set(conditions))
        procedures = list(set(procedures))
        drugs = list(set(drugs))
        self.all_tokens = {
            "conditions": conditions,
            "procedures": procedures,
            "drugs": drugs,
        }

        # store the tokenizer
        condition_tokenizer = Tokenizer(conditions)
        procedures_tokenizer = Tokenizer(procedures)
        drugs_tokenizer = Tokenizer(drugs)
        self.tokenizers = (
            condition_tokenizer,
            procedures_tokenizer,
            drugs_tokenizer,
        )
        self.voc_size = [item.get_vocabulary_size() for item in self.tokenizers]
        print("2. tokenized the medical codes")

    def get_ddi_matrix(self):
        """get drug-drug interaction (DDI)"""
        cid2atc_dic = defaultdict(set)
        med_voc_size = self.voc_size[2]

        vocab_to_index = self.tokenizers[2].vocabulary.word2idx

        # load cid2atc
        if not os.path.exists(
            os.path.join(str(Path.home()), ".cache/pyhealth/cid_to_ATC6.csv")
        ):
            cid_to_ATC6 = request.urlopen(
                "https://drive.google.com/uc?id=1CVfa91nDu3S_NTxnn5GT93o-UfZGyewI"
            ).readlines()
            with open(
                os.path.join(str(Path.home()), ".cache/pyhealth/cid_to_ATC6.csv"), "w"
            ) as outfile:
                for line in cid_to_ATC6:
                    print(str(line[:-1]), file=outfile)
        else:
            cid_to_ATC6 = open(
                os.path.join(str(Path.home()), ".cache/pyhealth/cid_to_ATC6.csv"), "r"
            ).readlines()

        # map cid to atc
        for line in cid_to_ATC6:
            line_ls = str(line[:-1]).split(",")
            cid = line_ls[0]
            atcs = line_ls[1:]
            for atc in atcs:
                if atc[:4] in vocab_to_index:
                    cid2atc_dic[cid[2:]].add(atc[:4])

        # ddi on (cid, cid)
        if not os.path.exists(
            os.path.join(str(Path.home()), ".cache/pyhealth/drug-DDI-TOP40.csv")
        ):
            ddi_df = pd.read_csv(
                request.urlopen(
                    "https://drive.google.com/uc?id=1R88OIhn-DbOYmtmVYICmjBSOIsEljJMh"
                )
            )
            ddi_df.to_csv(
                os.path.join(str(Path.home()), ".cache/pyhealth/drug-DDI-TOP40.csv"),
                index=False,
            )
        else:
            ddi_df = pd.read_csv(
                os.path.join(str(Path.home()), ".cache/pyhealth/drug-DDI-TOP40.csv")
            )

        # map to ddi on (atc, atc)
        ddi_adj = np.zeros((med_voc_size, med_voc_size))
        for index, row in ddi_df.iterrows():
            # ddi
            cid1 = row["STITCH 1"]
            cid2 = row["STITCH 2"]

            # cid -> atc_level3
            for atc_i in cid2atc_dic[cid1]:
                for atc_j in cid2atc_dic[cid2]:
                    ddi_adj[
                        vocab_to_index.get(atc_i, 0), vocab_to_index.get(atc_j, 0)
                    ] = 1
                    ddi_adj[
                        vocab_to_index.get(atc_j, 0), vocab_to_index.get(atc_i, 0)
                    ] = 1

        self.ddi_adj = ddi_adj
        return ddi_adj

    def generate_ehr_adj_for_GAMENet(self, visit_ls):
        """
        generate the ehr graph adj for GAMENet model input
        - loop over the training data to check whether any med pair appear
        """
        ehr_adj = np.zeros((self.voc_size[2], self.voc_size[2]))
        for visit_index in visit_ls:
            patient_id, visit_pos = self.index_map[visit_index]
            patient = self.patients[patient_id]
            visit = patient.visits[visit_pos]
            encoded_drugs = self.tokenizers[2]([visit.drugs])[0]
            for idx1, med1 in enumerate(encoded_drugs):
                for idx2, med2 in enumerate(encoded_drugs):
                    if idx1 >= idx2:
                        continue
                    ehr_adj[med1, med2] = 1
                    ehr_adj[med2, med1] = 1
        return ehr_adj

    def __len__(self):
        return len(self.patients)

    def __getitem__(self, index):
        patient_id, visit_pos = self.index_map[index]
        patient = self.patients[patient_id]

        conditions, procedures, drugs = [], [], []
        # locate all previous visits
        for visit in patient.visits[: visit_pos + 1]:
            conditions.append(visit.conditions)
            procedures.append(visit.procedures)
            drugs.append(visit.drugs)
        return {"conditions": conditions, "procedures": procedures, "drugs": drugs}

    def info(self):
        info = """
        ----- Output Data Structure -----
        TaskDataset.patients dict[str, Patient]
            - key: patient_id
            - value: <Patient> object
        
        <Patient>
            - patient_id: str
            - visits: dict[str, Visit]
                - key: visit_id
                - value: <DrugRecVisit> object
        
        <DrugRecVisit>
            - visit_id: str
            - patient_id: str
            - conditions: List = [],
            - procedures: List = [],
            - drugs: List = [],
            - labs: List = [],
            - physicalExams: List = []
        """
        print(info)


if __name__ == "__main__":
    from pyhealth.datasets import MIMIC3BaseDataset

    base_dataset = MIMIC3BaseDataset(
        root="/srv/local/data/physionet.org/files/mimiciii/1.4"
    )
    drug_rec_dataloader = DrugRecDataset(base_dataset)
    print(len(drug_rec_dataloader))
    print(drug_rec_dataloader[0])
