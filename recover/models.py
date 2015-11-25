from recover import db
from flask import url_for


class Data(db.EmbeddedDocumentField):
    date = db.StringField(primary_key=True)
    resting_heart_rate = db.IntField()
    heart_rate = db.DictField()


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
    data = db.ListField(db.EmbeddedDocumentField('Data'))

    def get_url(self):
        """ Returns the appropriate url for the patients unique ID. """
        return url_for('post', kwargs={'slug': self.slug})

    def __unicode__(self):
        """ Returns how to show a patient """
        return self.first_name + ' ' + self.last_name

    def add_data(self, date):
        return self.data.find(date=date)

    meta = {
        'ordering': ['last_name'],
        'indexes': ['first_name']
    }


