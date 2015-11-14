from fitbit import Fitbit
from recover.models import Patient


class PatientData:
    def __init__(self, patient):
        self.fitbit = Fitbit()
        self.token = dict()
        self.token['access_token'] = patient.token
        self.token['refresh_token'] = patient.refresh

    def get_resting_heart_rate(self):
        try:
            response = self.fitbit.api_call(self.token, '/1/user/-/activities/heart/data/today/1d.json')
        except Exception as e:
            return e
        resting = str(response['activities-heart'][0]['value']['restingHeartRate'])
        return resting
