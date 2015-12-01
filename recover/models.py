from recover import db
from flask import url_for


class PatientHealthData(db.EmbeddedDocument):
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
    slug = db.StringField(primary_key=True)  # unique id
    first_name = db.StringField(max_length=32, required=True)
    last_name = db.StringField(max_length=32, required=True)
    token = db.StringField(max_length=511, required=True)
    refresh = db.StringField(max_length=511, required=True)
    health_data_per_day = db.ListField(db.EmbeddedDocumentField('PatientHealthData'))

    def get_url(self):
        """ Returns the appropriate url for the patients unique ID. """
        return url_for('post', kwargs={'slug': self.slug})

    def __unicode__(self):
        """ Returns how to show a patient """
        return self.first_name + ' ' + self.last_name

    def stats(self, date):
        for d in self.health_data_per_day:
            if d['date'] == date:
                return d
        d = PatientHealthData()
        d['date'] = date
        d['day_complete'] = False
        self.health_data_per_day.append(d)
        return self.health_data_per_day[-1]

    meta = {
        'ordering': ['last_name'],
        'indexes': ['first_name', 'slug']
    }
