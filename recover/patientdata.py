from fitbit import Fitbit
from recover.models import Patient

fitbit = Fitbit()


class PatientData:
    """ A wrapper class to allow for easier API usage for an individual patient. """
    def __init__(self, patient):
        """ Set up this object with the patients tokens. """
        self.token = dict()
        self.token['access_token'] = patient.token
        self.token['refresh_token'] = patient.refresh

    def get_resting_heart_rate(self):
        """ Returns the resting heart rate of the patient today. """
        try:
            response = self.fitbit.api_call(self.token, '/1/user/-/activities/heart/date/today/1d.json')
        except Exception as e:
            return e
        resting = str(response['activities-heart'][0]['value']['restingHeartRate'])
        return resting
