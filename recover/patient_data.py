import logging
from recover import app
from mongoengine import ValidationError

from fitbit import Fitbit
from recover.models import Patient, PatientHealthData

fitbit = Fitbit()

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
                                       '/1/user/%s/activities/heart/date/%s/1d/%s.json' % (self.patient.slug, date, detail_level))
        except Exception:
            return False
        try:
            data = PatientHealthData()
            data['date'] = response['activities-heart'][0]['dateTime'].encode('ascii', 'ignore')
            data['resting_heart_rate'] = response['activities-heart'][0]['value']['restingHeartRate']
            for info in response['activities-heart-intraday']['dataset']:
                dayStr = data.date
                dayStr += ' ' + info['time']
                data['heart_rate'][dayStr] = info['value']
            self.patient.health_data_per_day.append(data)
            self.patient.save()
            return True
        except (KeyError, TypeError):
            pass
        return False

    def get_heart_rate_data_for_X_days(self, Xdays):
        app.logger.addHandler(logging.FileHandler('log/log.txt'))

        from datetime import date, timedelta
        today = date.today()
        day = ''
        try:
            response = []
            for i in range(Xdays + 1):
                day = (today - timedelta(days=Xdays-i)).isoformat()
                app.logger.info('getting day %s' % i)
                response = fitbit.api_call(self.token, '/1/user/%s/activities/heart/date/%s/1d/1min.json' % (self.patient.slug, day))
                try:
                    data = PatientHealthData()
                    app.logger.info('day %s collected out of %s' % (i, len(response)))
                    data['date'] = response['activities-heart'][0]['dateTime'].encode('ascii', 'ignore')
                    data['resting_heart_rate'] = response['activities-heart'][0]['value']['restingHeartRate']
                    app.logger.info('got resting')
                    for info in response['activities-heart-intraday']['dataset']:
                        dayStr = data.date
                        dayStr += ' ' + info['time']
                        data['heart_rate'][dayStr] = info['value']
                    self.patient.health_data_per_day.append(data)
                    self.patient.save()
                except (KeyError, TypeError, ValidationError, AttributeError) as e:
                    app.logger.info(e.message)
                    app.logger.info(response[0])
                    pass

        except Exception as e:
            app.logger.info('call: /1/user/-/activities/heart/date/%s/1min.json' % day)
            app.logger.info(e.message)
            return False
        return True

    # TODO: Fix this. make it good.
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
        except Exception as e:
            app.logger.info(e.message)
            return False

        try:
            data = self.patient.stats(response['activities-heart'][0]['dateTime'].encode('ascii', 'ignore'))
            data['resting_heart_rate'] = response['activities-heart'][0]['value']['restingHeartRate']
            for info in response['activities-heart-intraday']['dataset']:
                dayStr = data.date
                dayStr += ' ' + info['time']
                data['heart_rate'][dayStr] = info['value']
            self.patient.save()
            return True
        except (KeyError, TypeError):
            pass
        return False

    def get_activity_data_for_date_range(self, start_date, end_date='today', detail_level='15min'):
        """
        Helper function to retrieve activity (step) data for a date range
        :param start_date: start date of range in yyyy-MM-dd string format
        :param end_date: end date of range in yyyy-MM-dd string format
        """

        # TODO: Check to see if we already have this data before fetching it.

        app.logger.addHandler(logging.FileHandler('log/log.txt'))
        app.logger.info("### LOGGING FETCHED ACTIVITY DATA ")

        try:
            response = fitbit.api_call(self.token,
                                       '/1/user/-/activities/steps/date/%s/%s/%s.json'
                                       % (start_date, end_date, detail_level))
            app.logger.info(response)
        except Exception as e:
            app.logger.info(e.message)
            return False
        try:
            # data = self.patient.stats(response['activities-log-steps-intraday']['dataset'].encode('ascii', 'ignore'))

            app.logger.addHandler(logging.FileHandler('log/log.txt'))
            app.logger.info("### I got to this point!")
            app.logger.info(response)

            # data['resting_heart_rate'] = response['activities-heart'][0]['value']['restingHeartRate']
            # for info in response['activities-heart-intraday']['dataset']:
            #     dayStr = data.date
            #     dayStr += ' ' + info['time']
            #     data['heart_rate'][dayStr] = info['value']
            # self.patient.save()
            return True
        except (KeyError, TypeError):
            pass
        return False
