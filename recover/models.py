from datetime import datetime
from recover import db, app
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Document):
    """
    A User object represents an entity with the ability to log-in, i.e. physicians.
    """
    username = db.StringField(max_length=25, required=True, unique=True)
    email = db.EmailField(required=True, unique=True)
    full_name = db.StringField(max_length=70, required=True)
    password = db.StringField()
    confirmed = db.BooleanField()
    last_login = db.DateTimeField()
    last_active = db.DateTimeField()
    patients = db.ListField(db.ReferenceField('Patient'))
    patient_config = db.EmbeddedDocumentListField('PatientConfig')
    alerts = db.EmbeddedDocumentListField('Alert')

    def set_password(self, password):
        """

        :type password: str
        """
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """

        :type password: str
        """
        return check_password_hash(self.password, password)

    def __unicode__(self):
        """
        String representation of a Patient

        :rtype: str
        """
        return self.email

    # Below 4 methods are required for app-wide Login Manager.
    @staticmethod
    def is_active():
        return True

    def get_id(self):
        return str(self.id)

    @staticmethod
    def is_anonymous():
        return False

    @staticmethod
    def is_authenticated():
        return True


class PatientConfig(db.EmbeddedDocument):
    """
    Model to represent a physician's custom data thresholds for a given patient.
    A physician has exactly *ONE* such object per patient.
    Each of the 4 dictionaries below have "value" and "window" fields that represent preferred thresholds.
    Also holds a "notes" field in which the physician can append notes over time.
    """
    minHR = db.DictField()
    maxHR = db.DictField()
    minSteps = db.DictField()
    maxSteps = db.DictField()
    notes = db.StringField(max_length=10000, default="")
    patient = db.ReferenceField('Patient', required=True, unique=True)


class Alert(db.EmbeddedDocument):
    """
    Model to represent an instance of when a patient's data deviated from the physician's
    pre-defined Heart Rate or Activity thresholds as defined in PatientConfig.
    A given physician has Alert object(s).
    'trigger_info' is a dictionary that represents the threshold conditions that triggered the alert, and
    is of the following format: { 'class'='HR' / 'STEP' , operation = "MIN" / "MAX" }
    """
    recorded_value = db.IntField()
    threshold_value = db.IntField()
    time_window = db.IntField()
    trigger_info = db.DictField()
    patient = db.ReferenceField('Patient', required=True)
    incident_time = db.DateTimeField(required=True)
    incident_length = db.IntField()
    read = db.BooleanField(default=False)

    def __unicode__(self):
        """ String representation of an Alert """
        info = self.patient.first_name + ' ' + self.patient.last_name + ' '
        if self.trigger_info['operation'] == 'MAX':
            info += 'exceeded '
        else:
            info += 'was below '
        info += 'the set value of ' + str(self.threshold_value) + ' '
        if self.trigger_info['class'] == 'HR':
            'beats per minute '
        else:
            info += 'steps '
        info += 'over a time period of ' + str(self.time_window) + ' minutes. ' + \
                'The recorded value was ' + str(self.recorded_value) + ' starting at ' + \
                self.incident_time.strftime('%b %-d, %Y at %I:%M %p') + ' and lasting ' + str(
            self.incident_length) + ' minutes.'
        return info


class PatientInvite(db.Document):
    """
    Model to represent the state of a Physician's invitation to add a new Patient.
    Persists the relationship between an invited patient and the physician who added them, for the
    "pending acceptance" phase until the Patient object is formally created upon granting of Fitbit access.
    """
    inviting_physician = db.ReferenceField('User')
    accepted = db.BooleanField()
    email = db.StringField(max_length=35)
    first_name = db.StringField(max_length=32)
    last_name = db.StringField(max_length=32)


class PatientHealthData(db.EmbeddedDocument):
    """
    Model to encapsulate a single day's worth of Fitbit health activity for a patient.
    Each instance represents the data of a single date, keyed by a date string of format "YYYY-MM-DD".
    'heart_rate' is a dictionary of heart rate measurement values keyed by the number of seconds into the day,
    and is of the form {'10800' : '88', ... }
    'day_complete' represents whether the objects contains ALL data for the given day.
    """
    date = db.StringField(primary_key=True)
    resting_heart_rate = db.IntField()
    total_steps = db.IntField()
    heart_rate = db.DictField()
    activity_data = db.DictField()
    day_complete = db.BooleanField()
    checked = db.BooleanField()

    meta = {
        'ordering': ['date'],
    }


class Patient(db.Document):
    """
    Patient model for storage in our Database.
    Currently, we are only storing the name and tokens of the patient. If we
    need the data for the patient, we make an api call for it.
    """
    slug = db.StringField(primary_key=True)  # same as their Fitbit Profile ID
    first_name = db.StringField(max_length=32, required=True)
    last_name = db.StringField(max_length=32, required=True)
    email = db.EmailField(required=True)
    date_joined = db.DateTimeField()
    # Fitbit Access Token
    token = db.StringField(max_length=511, required=True)
    # Fitbit Refresh Token
    refresh = db.StringField(max_length=511, required=True)
    health_data_per_day = db.EmbeddedDocumentListField('PatientHealthData')
    date_last_data_fetch = db.StringField(max_length=10)

    def steps_today(self):
        return self.health_data_per_day[-1].total_steps

    def steps_average(self):
        days = 0
        total = 0
        for data in self.health_data_per_day:
            days += 1
            for key, value in data.activity_data.iteritems():
                total += value
        return total / days

    def date_last_worn(self):
        """

        :return: str of date last worn.
        """
        date = "No data"
        for data in self.health_data_per_day:
            if data.heart_rate:
                date = data.date
        if date == "No data":
            raise Exception("No data")
        return date

    def export_data_as_json(self, begin, end):
        """
        This function exports the patient's health data to a JSON file named
        "FIRSTNAME_LASTNAME_recover_data.json" in the directory of the
        applications JSON_FOLDER.

        :param begin: string of date to begin in YYYY-MM-DD format
        :param end: string of date to end in YYYY-MM-DD format
        :return: JSON file path as string
        """
        hr_data = {}
        step_data = {}
        for i in range(len(self.health_data_per_day)):
            if datetime.strptime(begin, '%Y-%m-%d') <= \
                    datetime.strptime(self.health_data_per_day[i].date, '%Y-%m-%d') <= \
                    datetime.strptime(end, '%Y-%m-%d'):
                hr_data.update(self.health_data_per_day[i].heart_rate)
                step_data.update(self.health_data_per_day[i].activity_data)

        exporting_data = {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'patient_health_data': {
                'heart_rate': hr_data,
                'activity': step_data
            }
        }
        import json
        fn = self.first_name + '_' + self.last_name + '_recover_data.json'
        file_name = app.config['JSON_FOLDER'] + fn
        with open(file_name, 'w') as outfile:
            json.dump(exporting_data, outfile, separators=(',', ': '), indent=4, sort_keys=True)
        return file_name

    def get_url(self):
        """ Returns the appropriate url for the patients unique ID. """
        return url_for('post', kwargs={'slug': self.slug})

    def __unicode__(self):
        """ String representation of a Patient """
        return self.first_name + ' ' + self.last_name

    meta = {
        'ordering': ['last_name'],
        'indexes': ['first_name', 'slug']
    }
