import sys

# TODO: remove this hack later
sys.path.append("/home/chaoqiy2/github/PyHealth-OMOP")
from pyhealth.data import Patient, Visit
from pyhealth.tasks.utils import (
    get_code_from_list_of_event,
    datetime_string_to_datetime,
)


def readmission_prediction_mimic3_fn(patient: Patient, time_window=15):
    """
    Readmission prediction aims at predicting whether the patient will be readmitted into hospital within time_window days \
        based on the clinical information from current visit (e.g., conditions and procedures).

    Process a single patient for the readmission prediction task.

    Args:
        patient: a Patient object
        time_window: the time window threshold (gap < time_window means label=1 for the task)
        
    Returns:
        samples: a list of samples, each sample is a dict with patient_id, visit_id, and other task-specific
         attributes as key

    Note that we define the task as a binary classification task.
    """

    samples = []

    # we will drop the last visit
    for i in range(len(patient) - 1):
        visit: Visit = patient[i]
        next_visit: Visit = patient[i + 1]

        # get time difference between current visit and next visit
        time_diff = (
            (
                datetime_string_to_datetime(next_visit.encounter_time).timestamp()
                - datetime_string_to_datetime(visit.encounter_time).timestamp()
            )
            / 3600
            / 24
        )
        readmission_label = 1 if time_diff < time_window else 0

        conditions = get_code_from_list_of_event(
            visit.get_event_list(event_type="DIAGNOSES_ICD")
        )
        procedures = get_code_from_list_of_event(
            visit.get_event_list(event_type="PROCEDURES_ICD")
        )
        drugs = get_code_from_list_of_event(
            visit.get_event_list(event_type="PRESCRIPTIONS")
        )
        # exclude: visits without (condition and procedure) or drug code
        if len(conditions) + len(procedures) + len(drugs) == 0:
            continue
        # TODO: should also exclude visit with age < 18
        samples.append(
            {
                "visit_id": visit.visit_id,
                "patient_id": patient.patient_id,
                "conditions": [conditions],
                "procedures": [procedures],
                "drugs": [drugs],
                "label": readmission_label,
            }
        )
    # no cohort selection
    return samples


def readmission_prediction_mimic4_fn(patient: Patient, time_window=15):
    """
    Readmission prediction aims at predicting whether the patient will be readmitted into hospital within time_window days \
        based on the clinical information from current visit (e.g., conditions and procedures).
        
    Process a single patient for the readmission prediction task.

    Args:
        patient: a Patient object
        time_window: the time window threshold (gap < time_window means label=1 for the task)
        
    Returns:
        samples: a list of samples, each sample is a dict with patient_id, visit_id, and other task-specific
         attributes as key

    Note that we define the task as a binary classification task.
    """

    samples = []

    # we will drop the last visit
    for i in range(len(patient) - 1):
        visit: Visit = patient[i]
        next_visit: Visit = patient[i + 1]

        # get time difference between current visit and next visit
        time_diff = (
            (
                datetime_string_to_datetime(next_visit.encounter_time).timestamp()
                - datetime_string_to_datetime(visit.encounter_time).timestamp()
            )
            / 3600
            / 24
        )
        readmission_label = 1 if time_diff < time_window else 0

        conditions = get_code_from_list_of_event(
            visit.get_event_list(event_type="diagnoses_icd")
        )
        procedures = get_code_from_list_of_event(
            visit.get_event_list(event_type="procedures_icd")
        )
        drugs = get_code_from_list_of_event(
            visit.get_event_list(event_type="prescriptions")
        )
        # exclude: visits without (condition and procedure) or drug code
        if len(conditions) + len(procedures) + len(drugs) == 0:
            continue
        # TODO: should also exclude visit with age < 18
        samples.append(
            {
                "visit_id": visit.visit_id,
                "patient_id": patient.patient_id,
                "conditions": [conditions],
                "procedures": [procedures],
                "drugs": [drugs],
                "label": readmission_label,
            }
        )
    # no cohort selection
    return samples


def readmission_prediction_eicu_fn(patient: Patient, time_window=5):
    """
    Readmission prediction aims at predicting whether the patient will be readmitted into hospital within time_window days \
        based on the clinical information from current visit (e.g., conditions and procedures).

    Process a single patient for the readmission prediction task.

    Args:
        patient: a Patient object
        time_window: the time window threshold (gap < time_window means label=1 for the task)
        
    Returns:
        samples: a list of samples, each sample is a dict with patient_id, visit_id, and other task-specific
         attributes as key

    Note that we define the task as a binary classification task.
    """

    samples = []
    # we will drop the last visit
    for i in range(len(patient) - 1):
        visit: Visit = patient[i]
        next_visit: Visit = patient[i + 1]
        # get time difference between current visit and next visit
        time_diff = (-next_visit.encounter_time + visit.encounter_time) / 60 / 24
        readmission_label = 1 if time_diff < time_window else 0

        conditions = get_code_from_list_of_event(
            visit.get_event_list(event_type="diagnosis")
        )
        procedures = get_code_from_list_of_event(
            visit.get_event_list(event_type="physicalExam")
        )
        drugs = get_code_from_list_of_event(
            visit.get_event_list(event_type="medication")
        )
        # exclude: visits without (condition and procedure) or drug code
        if len(conditions) + len(procedures) + len(drugs) == 0:
            continue
        # TODO: should also exclude visit with age < 18
        samples.append(
            {
                "visit_id": visit.visit_id,
                "patient_id": patient.patient_id,
                "conditions": [conditions],
                "procedures": [procedures],
                "drugs": [drugs],
                "label": readmission_label,
            }
        )
    # no cohort selection
    return samples


def readmission_prediction_omop_fn(patient: Patient, time_window=15):
    """
    Readmission prediction aims at predicting whether the patient will be readmitted into hospital within time_window days \
        based on the clinical information from current visit (e.g., conditions and procedures).

    Process a single patient for the readmission prediction task.

    Args:
        patient: a Patient object
        time_window: the time window threshold (gap < time_window means label=1 for the task)
        
    Returns:
        samples: a list of samples, each sample is a dict with patient_id, visit_id, and other task-specific
         attributes as key

    Note that we define the task as a binary classification task.
    """

    samples = []
    # we will drop the last visit
    for i in range(len(patient) - 1):
        visit: Visit = patient[i]
        next_visit: Visit = patient[i + 1]
        # get time difference between current visit and next visit
        time_diff = (
            (
                datetime_string_to_datetime(next_visit.encounter_time).timestamp()
                - datetime_string_to_datetime(visit.encounter_time).timestamp()
            )
            / 3600
            / 24
        )
        readmission_label = 1 if time_diff < time_window else 0

        conditions = get_code_from_list_of_event(
            visit.get_event_list(event_type="condition_occurrence")
        )
        procedures = get_code_from_list_of_event(
            visit.get_event_list(event_type="procedure_occurrence")
        )
        drugs = get_code_from_list_of_event(
            visit.get_event_list(event_type="drug_exposure")
        )
        # labs = get_code_from_list_of_event(
        #     visit.get_event_list(event_type="measurement")
        # )

        # exclude: visits without (condition and procedure and drug code)
        if len(conditions) + len(procedures) + len(drugs) == 0:
            continue
        # TODO: should also exclude visit with age < 18
        samples.append(
            {
                "visit_id": visit.visit_id,
                "patient_id": patient.patient_id,
                "conditions": [conditions],
                "procedures": [procedures],
                "drugs": [drugs],
                "label": readmission_label,
            }
        )
    # no cohort selection
    return samples


def readmission_prediction(dataset_name: str, patient: Patient):
    if dataset_name == "MIMIC-III":
        return readmission_prediction_mimic3_fn(patient)
    elif dataset_name == "MIMIC-IV":
        return readmission_prediction_mimic4_fn(patient)
    elif dataset_name == "eICU":
        return readmission_prediction_eicu_fn(patient)
    elif dataset_name == "OMOP":
        return readmission_prediction_omop_fn(patient)
    else:
        raise ValueError(f"Unknown dataset name: {dataset_name}")


if __name__ == "__main__":
    from pyhealth.datasets import MIMIC3Dataset, MIMIC4Dataset, eICUDataset, OMOPDataset

    # mimic3dataset = MIMIC3Dataset(
    #     root="/srv/local/data/physionet.org/files/mimiciii/1.4",
    #     tables=["DIAGNOSES_ICD", "PROCEDURES_ICD", "PRESCRIPTIONS"],
    #     dev=True,
    #     refresh_cache=False,
    # )
    # mimic3dataset.stat()
    # mimic3dataset.set_task(readmission_prediction)
    # mimic3dataset.stat()

    # mimic4dataset = MIMIC4Dataset(
    #     root="/srv/local/data/physionet.org/files/mimiciv/2.0/hosp",
    #     tables=["diagnoses_icd", "procedures_icd", "prescriptions"],
    #     dev=True,
    #     code_mapping={"prescriptions": "ATC3"},
    #     refresh_cache=False,
    # )
    # mimic4dataset.stat()
    # mimic4dataset.set_task(task_fn=readmission_prediction)
    # mimic4dataset.stat()

    # eicudataset = eICUDataset(
    #     root="/srv/local/data/physionet.org/files/eicu-crd/2.0",
    #     tables=["diagnosis", "medication", "physicalExam"],
    #     dev=True,
    #     refresh_cache=False,
    # )
    # eicudataset.stat()
    # eicudataset.set_task(task_fn=readmission_prediction)
    # eicudataset.stat()

    omopdataset = OMOPDataset(
        root="/srv/local/data/zw12/pyhealth/raw_data/synpuf1k_omop_cdm_5.2.2",
        tables=[
            "condition_occurrence",
            "procedure_occurrence",
            "drug_exposure",
            "measurement",
        ],
        dev=False,
        refresh_cache=False,
    )
    omopdataset.stat()
    omopdataset.set_task(task_fn=readmission_prediction)
    omopdataset.stat()
