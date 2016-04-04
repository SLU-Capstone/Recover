from wtforms import Form, StringField, PasswordField, validators


class UserRegistrationForm(Form):
    """
    Form for physician registration to use our system.
    Physician will enter a username, full_name, email, and password.
    """
    username = StringField('Desired Username', [validators.Length(min=4, max=25)])
    full_name = StringField('Full Name', [validators.Length(min=2, max=70)])
    email = StringField('Email Address', [validators.Length(min=5, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
