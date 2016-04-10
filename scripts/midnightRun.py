from recover.models import *
from recover.patient_data import *
import datetime


def new_patient_alert(actual_val, val, window, trigger, patient, time):
    alert = Alert()
    alert.recorded_value = actual_val
    alert.threshold_value = val
    alert.time_window = window
    alert.trigger_info = trigger
    alert.patient = patient
    alert.incident_time = time
    alert.read = False
    alert.save()
    return alert


def check_max_hr(val, window, patient):
    return check(val, window, 1, 0, patient)


def check_min_hr(val, window, patient):
    return check(val, window, 0, 0, patient)


def check_max_steps(val, window, patient):
    return check(val, window, 1, 1, patient)


def check_min_steps(val, window, patient):
    return check(val, window, 0, 1, patient)


def check(val, window, operation, option, patient):
    actual = 0
    timestamp = datetime.date.today()
    return actual, timestamp


def midnight_run():
    """
    This function will fetch all patient data. After all patients are updated,
    a series of checks will be performed to ensure that the patient is within
    the physicians configurations. If a check shows that the patient is outside
    of the threshold, an alert for the patient will be made with the actual
    value of the event and a timestamp for reference.

    """
    physicians = User.objects()
    for physician in physicians:
        patients = physician.patients
        # fetch all patient data
        for patient in patients:
            data = PatientData(patient)
            last_synced = patient.date_last_synced.isoformat()
            last_synced = last_synced[0:10]
            data.get_heart_rate_data_for_date_range(last_synced)
            data.get_activity_data_for_date_range(last_synced)
            patient.date_last_synced = datetime.datetime.now()
            patient.save()

        # update alerts
        configurations = physician.patient_config
        for config in configurations:
            patient = config.patient

            val = config.minHR.value
            window = config.minHR.window
            actual_value, timestamp = check_min_hr(val, window, patient)
            trigger = {'class': 'HR', 'operation': 'MIN'}
            new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp)
            physician.alerts.append(new_alert)

            val = config.maxHR.value
            window = config.maxHR.window
            actual_value, timestamp = check_max_hr(val, window, patient)
            trigger = {'class': 'HR', 'operation': 'MAX'}
            new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp)
            physician.alerts.append(new_alert)

            val = config.minSteps.value
            window = config.minSteps.window
            actual_value, timestamp = check_min_steps(val, window, patient)
            trigger = {'class': 'STEP', 'operation': 'MIN'}
            new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp)
            physician.alerts.append(new_alert)

            val = config.maxSteps.value
            window = config.maxSteps.window
            actual_value, timestamp = check_max_steps(val, window, patient)
            trigger = {'class': 'STEP', 'operation': 'MAX'}
            new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp)
            physician.alerts.append(new_alert)

        physician.save()
