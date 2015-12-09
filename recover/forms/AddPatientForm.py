from wtforms import Form, StringField, validators


class AddPatientForm(Form):
    first_name = StringField('First name', [validators.Length(min=4, max=25)])
    last_name = StringField('Last name', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=5, max=35)])
