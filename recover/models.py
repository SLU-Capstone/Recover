from recover import db
from flask import url_for


class Patient(db.Document):
    first_name = db.StringField(max_length=32, required=True)
    last_name = db.StringField(max_length=32, required=True)
    token = db.StringField(max_length=255, required=True)
    refresh = db.StringField(max_length=255, required=True)
    slug = db.StringField(max_length=255, required=True) # unique id

    def get_url(self):
        return url_for('post', kwargs={'slug': self.slug})

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name

    meta = {
        'ordering': ['last_name'],
        'indexes': ['first_name']
    }



