from wtforms import Form, StringField, PasswordField, validators


class UserRegistrationForm(Form):
    """
    Form for physician registration to use our system.
    Physician will enter a username, email, and a password.
    """
    username = StringField('Desired Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=5, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')






