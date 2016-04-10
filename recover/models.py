from recover import db
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
    A physician has exactly one such object per patient.
    Each of the 4 dictionaries below have "value" and "window" fields that represent preferred thresholds.
    Also holds a "notes" field in which the physician can append notes over time.
    """
    minHR = db.DictField()
    maxHR = db.DictField()
    minSteps = db.DictField()
    maxSteps = db.DictField()
    notes = db.StringField(max_length=10000)
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
    read = db.BooleanField(default=False)


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
    heart_rate = db.DictField()
    day_complete = db.BooleanField()


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
    # Fitbit Access Token
    token = db.StringField(max_length=511, required=True)
    # Fitbit Refresh Token
    refresh = db.StringField(max_length=511, required=True)
    health_data_per_day = db.EmbeddedDocumentListField('PatientHealthData')
    date_last_synced = db.DateTimeField()

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
