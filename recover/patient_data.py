from fitbit import Fitbit
from recover.models import Patient
from dateutil import rrule, parser

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
        """ Set up this object with the patient's Fitbit access tokens.
        :type patient: Patient
        """
        self.patient = patient
        self.token = dict()
        self.token['access_token'] = patient.token
        self.token['refresh_token'] = patient.refresh

    def get_heart_rate_data_for_day(self, date='today', detail_level='1min'):
        """
        Retrieves and saves a patient's heart-rate data (daily average and time-series data) for a given day.
        :type detail_level: string
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
        except (KeyError, TypeError):
            pass
        return False


    def get_heart_rate_data_for_date_range(self, start_date, end_date):
        """
        Helper function to retrieve heart rate data for a date range
        :param start_date: start date of range in yyyy-MM-dd string format
        :param end_date: end date of range in yyyy-MM-dd string format
        """
        dates = list(rrule.rrule(rrule.DAILY,
                         dtstart=parser.parse(start_date),
                         until=parser.parse(end_date)))

        for day in dates:
            self.get_heart_rate_data_for_day(day.strftime("%Y-%m-%d"))

