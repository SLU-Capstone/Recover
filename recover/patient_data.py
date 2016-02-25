import logging
from time import mktime

from fitbit import Fitbit
from recover.models import Patient

fitbit = Fitbit()


# time is HH:MM:SS
# date is yyyy-MM-dd
def time2sec(time, date):
    hour, minute, sec = time.split(':')
    year, month, day = date.split('-')
    y = int(year)
    mo = int(month)
    d = int(day)
    h = int(hour)
    mi = int(minute)
    s = int(sec)
    time = date(y, mo, d, h, mi, s)
    return int(mktime(time.timetuple()))


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
                seconds = time2sec(info['time'], data['date'])
                data['heart_rate'][seconds] = info['value']
            self.patient.save()
            return True
        except (KeyError, TypeError):
            pass
        return False

    def get_heart_rate_data_for_X_days(self, Xdays):
        from recover import app
        app.logger.addHandler(logging.FileHandler('log/log.txt'))
        app.logger.info('started fun')

        from datetime import date, timedelta
        today = date.today()
        day = ''
        try:
            response = []
            for i in range(0,Xdays + 1):
                day = (today - timedelta(days=i)).isoformat()
                response.append(fitbit.api_call(self.token, '/1/user/-/activities/heart/date/%s/1d/1min.json' % day))
        except Exception as e:
            app.logger.info('call: /1/user/-/activities/heart/date/%s/1min.json' % day)
            app.logger.info(e.message)
            return False

        try:
            for resp in response:
                data = self.patient.stats(resp['activities-heart'][0]['dateTime'].encode('ascii', 'ignore'))
                data['resting_heart_rate'] = resp['activities-heart'][0]['value']['restingHeartRate']
                app.logger.info('got resting')
                for info in resp['activities-heart-intraday']['dataset']:
                    seconds = time2sec(info['time'], data['date'])
                    app.logger.info('got secs')
                    data['heart_rate'][seconds] = info['value']
                    app.logger.info('got val')
                self.patient.save()
                return True
        except (KeyError, TypeError) as e:
            app.logger.info(e.message)
            app.logger.info(response[0])
            pass
        return False

    def get_heart_rate_data_for_date_range(self, start_date, end_date='today', detail_level='1min'):
        """
        Helper function to retrieve heart rate data for a date range
        :param start_date: start date of range in yyyy-MM-dd string format
        :param end_date: end date of range in yyyy-MM-dd string format
        """
        try:
            response = fitbit.api_call(self.token,
                                       '/1/user/-/activities/heart/date/%s/%s/%s.json'
                                       % (start_date, end_date, detail_level))
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
