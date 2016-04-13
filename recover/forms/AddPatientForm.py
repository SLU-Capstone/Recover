from wtforms import Form, StringField, validators
from wtforms.fields.html5 import EmailField


class AddPatientForm(Form):
    """
    Form to add a patient to invite to our system.
    The physician will enter to patient's first and last name, as well as
    an email for our system to contact them with.
    """
    first_name = StringField('First Name', [validators.Length(min=4, max=25)])
    last_name = StringField('Last Name', [validators.Length(min=4, max=25)])
    email = EmailField('Email Address', [validators.Length(min=5, max=35), validators.Email()])
