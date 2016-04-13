from collections import deque

from recover.models import *
from recover.patient_data import *
from datetime import datetime


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


def check(window, operation, data):
    vals = deque()
    times = deque()
    begin_time = ''
    total = 0
    size = 0
    for key, value in data.iteritems():
        if begin_time == '':  # first iteration only
            begin_time = key
        diff = datetime.strptime(key, '%y-%m-%d %h:%m:%s').date()
        diff -= datetime.strptime(begin_time, '%y-%m-%d %h:%m:%s').date()
        if diff.min < window:
            vals.append(value)
            times.append(key)
            total += value
            size += 1
        else:
            average = float(total) / size
            if operation(average):
                return begin_time, average
            total -= vals.popleft()
            size -= 1
            times.popleft()
            try:
                new_front = times.popleft()
                begin_time = new_front
                times.appendleft(begin_time)
            except IndexError:
                return '', 0

    return '', 0


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
            last_synced = patient.date_last_synced
            data.get_heart_rate_data_for_date_range(last_synced)
            data.get_activity_data_for_date_range(last_synced)
            patient.date_last_synced = datetime.datetime.now().isoformat()[0:10]
            patient.save()

        # update alerts
        configurations = physician.patient_config
        for config in configurations:
            patient = config.patient

            for day in patient.health_data_per_day:
                if not day.checked:
                    # check min hr
                    val = config.minHR.value
                    window = config.minHR.window
                    actual_value, timestamp = check(window, lambda x: x > val, day.heart_rate)
                    trigger = {'class': 'HR', 'operation': 'MIN'}
                    new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp)
                    physician.alerts.append(new_alert)

                    # check max hr
                    val = config.maxHR.value
                    window = config.maxHR.window
                    actual_value, timestamp = check(window, lambda x: x < val, day.heart_rate)
                    trigger = {'class': 'HR', 'operation': 'MAX'}
                    new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp)
                    physician.alerts.append(new_alert)

                    # check min steps
                    val = config.minSteps.value
                    window = config.minSteps.window
                    actual_value, timestamp = check(window, lambda x: x > val, day.activity_data)
                    trigger = {'class': 'STEP', 'operation': 'MIN'}
                    new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp)
                    physician.alerts.append(new_alert)

                    val = config.maxSteps.value
                    window = config.maxSteps.window
                    actual_value, timestamp = check(window, lambda x: x < val, day.activity_data)
                    trigger = {'class': 'STEP', 'operation': 'MAX'}
                    new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp)
                    physician.alerts.append(new_alert)

                    day.checked = True

            patient.save()

        physician.save()
