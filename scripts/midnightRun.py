from collections import deque

from recover.models import *
from recover.patient_data import *
from datetime import datetime


def new_patient_alert(actual_val, val, window, trigger, patient, time, duration):
    """
    Helper function to set up a new Alert document

    :param actual_val: Value that triggered alert
    :param val: Value that the configuration had
    :param window: time window from configuration
    :param trigger: dict with keys 'class' and 'operation' to distinguish HR/STEP and MIN/MAX
    :param patient: Patient reference
    :param time: timestamp of the alert
    :param duration: int minutes of incident length
    :return: A new alert object
    """
    alert = Alert()
    alert.recorded_value = actual_val
    alert.threshold_value = val
    alert.time_window = window
    alert.trigger_info = trigger
    alert.patient = patient
    alert.incident_time = time
    alert.incident_length = duration
    alert.read = False
    return alert


def check(window, operation, data):
    """
    A moving average algorithm to determine whether an alert should be triggered

    :param window: time window to check
    :param operation: function to do the check
    :param data: Health data to parse
    :return: Returns a dict with the value that triggered an alert, timestamp, and duration
    """
    alert_value = 0
    problems = []
    vals = deque()
    times = deque()
    begin_time = ''
    total = 0
    size = 0
    flag = False
    alert_begin = ''
    for key, value in data.iteritems():
        if begin_time == '':  # first iteration only
            begin_time = key
        diff = datetime.strptime(key, '%Y-%m-%d %H:%M:%S').date()
        diff -= datetime.strptime(begin_time, '%Y-%m-%d %H:%M:%S').date()
        if (diff.seconds / 60) < window:
            vals.append(value)
            times.append(key)
            total += value
            size += 1
        else:
            average = float(total) / size
            if operation(average):
                if not flag:
                    flag = True
                    alert_begin = datetime.strptime(begin_time, '%Y-%m-%d %H:%M:%S').date()
                    alert_value = value
            elif flag and not operation(average):
                flag = False
                diff = datetime.strptime(key, '%Y-%m-%d %H:%M:%S').date()
                diff -= datetime.strptime(alert_begin, '%Y-%m-%d %H:%M:%S').date()
                problems.append({
                    'value': alert_value,
                    'timestamp': alert_begin,
                    'length': diff.seconds / 60
                })

            total -= vals.popleft()
            size -= 1
            times.popleft()
            try:
                new_front = times.popleft()
                begin_time = new_front
                times.appendleft(begin_time)
            except IndexError:
                return problems

    return problems


def pull_all():
    """
    Go through every patient in our system and pull data.
    """
    physicians = User.objects()
    for physician in physicians:
        patients = physician.patients
        # fetch all patient data
        for patient in patients:
            data = PatientData(patient)
            last_synced = patient.date_last_data_fetch
            data.get_heart_rate_data_for_date_range(last_synced)
            data.get_activity_data_for_date_range(last_synced)
            patient.date_last_data_fetch = date.today().isoformat()[0:10]
            patient.save()


def check_all():
    """
    Goes through all physician to check the patients and whether or not to trigger alerts
    """
    physicians = User.objects()
    for physician in physicians:
        # update alerts
        configurations = physician.patient_config
        for config in configurations:
            patient = config.patient

            for day in patient.health_data_per_day:
                if not day.checked:
                    # check min hr
                    val = config.minHR['value']
                    window = config.minHR['window']
                    trigger = {'class': 'HR', 'operation': 'MIN'}
                    problems = check(window, lambda x: x > val, day.heart_rate)
                    if len(problems) > 0:
                        for p in problems:
                            actual_value = p['value']
                            timestamp = p['timestamp']
                            length = p['length']
                            new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp, length)
                            physician.alerts.append(new_alert)
                            config = [c for c in physician.patient_config if c.patient.slug == patient.slug][0]
                            config.add_note(timestamp, str(new_alert))

                    # check max hr
                    val = config.maxHR['value']
                    window = config.maxHR['window']
                    trigger = {'class': 'HR', 'operation': 'MAX'}
                    problems = check(window, lambda x: x < val, day.heart_rate)
                    if len(problems) > 0:
                        for p in problems:
                            actual_value = p['value']
                            timestamp = p['timestamp']
                            length = p['length']
                            new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp, length)
                            physician.alerts.append(new_alert)
                            config = [c for c in physician.patient_config if c.patient.slug == patient.slug][0]
                            config.add_note(timestamp, str(new_alert))

                    # check min steps
                    val = config.minSteps['value']
                    window = config.minSteps['window']
                    trigger = {'class': 'STEP', 'operation': 'MIN'}
                    problems = check(window, lambda x: x > val, day.activity_data)
                    if len(problems) > 0:
                        for p in problems:
                            actual_value = p['value']
                            timestamp = p['timestamp']
                            length = p['length']
                            new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp, length)
                            physician.alerts.append(new_alert)
                            config = [c for c in physician.patient_config if c.patient.slug == patient.slug][0]
                            config.add_note(timestamp, str(new_alert))

                    # check max steps
                    val = config.maxSteps['value']
                    window = config.maxSteps['window']
                    trigger = {'class': 'STEP', 'operation': 'MAX'}
                    problems = check(window, lambda x: x < val, day.activity_data)
                    if len(problems) > 0:
                        for p in problems:
                            actual_value = p['value']
                            timestamp = p['timestamp']
                            length = p['length']
                            new_alert = new_patient_alert(actual_value, val, window, trigger, patient, timestamp, length)
                            physician.alerts.append(new_alert)
                            config = [c for c in physician.patient_config if c.patient.slug == patient.slug][0]
                            config.add_note(timestamp, str(new_alert))

                    day.checked = True

        physician.save()


def midnight_run():
    """
    This function will fetch all patient data. After all patients are updated,
    a series of checks will be performed to ensure that the patient is within
    the physicians configurations. If a check shows that the patient is outside
    of the threshold, an alert for the patient will be made with the actual
    value of the event and a timestamp for reference.
    """
    pull_all()
    check_all()
