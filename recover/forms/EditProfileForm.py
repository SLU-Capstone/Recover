from wtforms import Form, StringField, validators
from wtforms.fields.html5 import EmailField


class EditProfileForm(Form):
    """
    Form to represent required fields for Profile Settings page.
    Physician can modify existing username, full_name, and email.
    """
    username = StringField('Username', [validators.Length(min=4, max=25)])
    full_name = StringField('Full Name', [validators.Length(min=2, max=70)])
    email = EmailField('Email Address', [validators.Length(min=5, max=35), validators.Email()])

