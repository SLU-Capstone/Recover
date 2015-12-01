from fitbit import Fitbit
from recover.models import Patient

fitbit = Fitbit()

def time2sec(time):
    hour, minute, sec = time.split(':')
    h = int(hour)
    m = int(minute) + 60 * h
    return str(int(sec) + 60 * m)


# noinspection PyBroadException
class PatientData:
    """ A wrapper class to allow for easier API usage for an individual patient. """

    def __init__(self, patient):
        """ Set up this object with the patients tokens.
        :type patient: Patient
        """
        self.patient = patient
        self.token = dict()
        self.token['access_token'] = patient.token
        self.token['refresh_token'] = patient.refresh

    def get_heart_rate_data_for_day(self, date='today', detail_level='1min'):
        """
        Grabs the heart-rate data for the patient
        :type detail_level: str
        :param date: date of interest in yyyy-MM-dd format as a string
        :param detail_level: detail level is a string. either 1min or 1sec
        """
        try:
            response = fitbit.api_call(self.token,
                                       '/1/user/-/activities/heart/date/%s/1d/%s.json' % (date, detail_level))
        except Exception:
            return False
        try:
            data = self.patient.stats(response['activities-heart'][0]['dateTime'].encode('ascii', 'ignore'))
            data['resting_heart_rate'] = response['activities-heart'][0]['value']['restingHeartRate']
            for info in response['activities-heart-intraday']['dataset']:
                seconds = time2sec(info['time'])
                data['heart_rate'][seconds] = info['value']
            self.patient.save()
            return True
        except KeyError:
            pass
        return False

    def get_heart_rate_data_for_date_range(self, date_range):
        pass
