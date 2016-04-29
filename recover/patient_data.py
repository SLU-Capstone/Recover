from datetime import date
from mongoengine import ValidationError
from fitbit import Fitbit
from recover.models import Patient, PatientHealthData

fitbit = Fitbit()


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

    def get_heart_rate_data_for_day(self, day='today'):
        """
        Retrieves and saves a patient's heart-rate data (daily average and time-series data) for a given day.

        :param day: date of interest in yyyy-MM-dd format as a string
        :returns True or False whether or not the fetch was successful
        """
        return self.get_heart_rate_data_for_x_days(1, end_date=day)

    def get_heart_rate_data_for_x_days(self, x_days, end_date='today'):
        """
        Retrieves and saves a patient's heart-rate data (daily average and time-series data) for X days, with
        a specified end date which defaults to the current day.

        :param x_days:
        :param end_date:
        :returns True or False whether or not the fetch was successful
        """

        from datetime import date, timedelta, datetime
        if end_date == 'today':
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        day = ''
        try:
            for i in range(x_days + 1):
                day = (end_date - timedelta(days=x_days - i)).isoformat()
                response, token = fitbit.api_call(self.token, '/1/user/%s/activities/heart/date/%s/1d/1min.json' % (
                    self.patient.slug, day))
                self.patient.token = token['access_token']
                self.patient.refresh = token['refresh_token']
                self.patient.save()
                try:
                    data = PatientHealthData(date=day)
                    all_data = self.patient.health_data_per_day
                    found = False
                    for d in all_data:
                        if d.date == day:
                            data = d
                            found = True
                            break
                    if not found:
                        self.patient.health_data_per_day.append(data)

                    data['resting_heart_rate'] = response['activities-heart'][0]['value']['restingHeartRate']
                    for info in response['activities-heart-intraday']['dataset']:
                        day_str = data.date
                        day_str += ' ' + info['time']
                        data['heart_rate'][day_str] = info['value']
                    self.patient.save()
                except (KeyError, TypeError, ValidationError, AttributeError) as e:
                    pass

        except Exception as e:
            return False
        self.patient.date_last_data_fetch = day
        return True

    def get_heart_rate_data_for_date_range(self, start_date, end_date='today'):
        """
        Helper function to retrieve heart rate data for a given date range.

        :param start_date: start date of range in yyyy-MM-dd string format
        :param end_date: end date of range in yyyy-MM-dd string format
        :returns True or False whether or not the fetch was successful
        """
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:  # end_date == 'today'
            end = date.today()

        x = (end - start).days
        return self.get_heart_rate_data_for_x_days(x, end_date)

    def get_activity_data_for_x_days(self, x_days, end_date='today'):
        """
        Helper function to retrieve activity (step) data for X days with a specified end date that
        defaults to the current day.

        :param x_days: The number of days to pull
        :param end_date: end date of range in yyyy-MM-dd string format
        :returns True or False whether or not the fetch was successful
        """

        from datetime import date, timedelta, datetime
        if end_date == 'today':
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        day = ''
        try:
            for i in range(x_days + 1):
                day = (end_date - timedelta(days=x_days - i)).isoformat()
                response, token = fitbit.api_call(self.token, '/1/user/%s/activities/steps/date/%s/1d/15min.json' % (
                    self.patient.slug, day))
                self.patient.token = token['access_token']
                self.patient.refresh = token['refresh_token']
                self.patient.save()
                try:
                    data = PatientHealthData(date=day)
                    all_data = self.patient.health_data_per_day
                    found = False
                    for d in all_data:
                        if d.date == day:
                            data = d
                            found = True
                            break
                    if not found:
                        self.patient.health_data_per_day.append(data)

                    data['total_steps'] = response['activities-steps'][0]['value']
                    for info in response['activities-steps-intraday']['dataset']:
                        day_str = data.date
                        day_str += ' ' + info['time']
                        data['activity_data'][day_str] = info['value']
                    self.patient.save()
                except (KeyError, TypeError, ValidationError, AttributeError) as e:
                    pass

        except Exception as e:
            return False
        self.patient.date_last_data_fetch = day
        return True

    def get_activity_data_for_date_range(self, start_date, end_date='today'):
        """
        Helper function to retrieve activity (step) data for a given date range.

        :param start_date: start date of range in yyyy-MM-dd string format
        :param end_date: end date of range in yyyy-MM-dd string format
        :returns True or False whether or not the fetch was successful
        """
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:  # end_date == 'today'
            end = date.today()
        x = (end - start).days
        return self.get_activity_data_for_x_days(x, end_date)
