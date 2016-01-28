from wtforms import Form, StringField, PasswordField, validators


class AdminUsers(Form):
    """
    """
    username = StringField('Username', [validators.Length(min=4, max=25)], id='username')
    email = StringField('Email Address', [validators.Length(min=5, max=35)], id='userEmail')


class AdminPatients(Form):
    """
    """
    first = StringField('First Name', [validators.Length(min=4, max=25)])
    last = StringField('Last Name', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=5, max=25)])
