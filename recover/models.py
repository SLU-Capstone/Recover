from recover import db
from flask import url_for


class Patient(db.Document):
    """
    Patient model for storage in our Database.
    Currently, we are only storing the name and tokens of the patient. If we
    need the data for the patient, we make an api call for it.
    """
    first_name = db.StringField(max_length=32, required=True)
    last_name = db.StringField(max_length=32, required=True)
    token = db.StringField(max_length=511, required=True)
    refresh = db.StringField(max_length=511, required=True)
    slug = db.StringField(max_length=255, required=True) # unique id

    def get_url(self):
        """ Returns the appropriate url for the patients unique ID. """
        return url_for('post', kwargs={'slug': self.slug})

    def __unicode__(self):
        """ Returns how to show a patient """
        return self.first_name + ' ' + self.last_name

    meta = {
        'ordering': ['last_name'],
        'indexes': ['first_name']
    }



