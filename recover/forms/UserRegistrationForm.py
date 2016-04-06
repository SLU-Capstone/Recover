from wtforms import Form, StringField, PasswordField, validators


class UserRegistrationForm(Form):
    """
    Form to represent required fields for user (physician) registration.
    Physician enters a username, full name, email, and password.
    """
    username = StringField('Username', [validators.Length(min=4, max=25)])
    full_name = StringField('Full Name', [validators.Length(min=2, max=70)])
    email = StringField('Email Address', [validators.Length(min=5, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
