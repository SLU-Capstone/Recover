from wtforms import Form, PasswordField, validators


class ChangePasswordForm(Form):
    """
    Form to represent fields required for changing user password.
    """
    current_password = PasswordField('Current Password')

    new_password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    new_password_confirm = PasswordField('Repeat New Password')
