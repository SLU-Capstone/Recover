from recover.models import *
from recover.patient_data import *
from datetime import date

def midnightRun():
    physicians = User.objects()
    for physician in physicians:
        patients = physician.patients
        for patient in patients:
            data = PatientData(patient)
            last_synced = patient.date_last_synced.isoformat()
            last_synced = last_synced[0:10]
            data.get_heart_rate_data_for_date_range(last_synced)
            data.get_activity_data_for_date_range(last_synced)
