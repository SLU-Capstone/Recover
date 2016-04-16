import os

from flask import Blueprint, request, flash, render_template, redirect, send_from_directory, url_for
from flask.ext.login import login_user, login_required, current_user, logout_user
from mongoengine import DoesNotExist, NotUniqueError
from recover import login_manager, app
from recover.EmailClient import email_physician_confirmation
from recover.forms.UserRegistrationForm import UserRegistrationForm
from recover.models import User
from datetime import datetime

user_management = Blueprint('user_management', __name__, template_folder='../templates')


@user_management.route('/register/', methods=['GET', 'POST'])
def register():
    """
    Registers a Physician to use our system. Physicians will be required to
    enter a username, email address, password, and password confirmation.
    """
    form = UserRegistrationForm(request.form)
    if request.method == 'POST':
        try:
            if User.objects(email=form.email.data).count() > 0:
                u = User.objects(email=form.email.data)[0]
                if not u.confirmed:
                    flash("That email address has already been registered, but has not been confirmed. "
                          "Please click the link in the confirmation email to continue.", 'warning')
                    return render_template('register.html', form=form)
        except AttributeError:
            pass  # Users table is empty, so no need to check.

        if form.validate():

            # Create the new user with "unconfirmed" state.
            new_user = User(username=form.username.data.lower(), full_name=form.full_name.data, email=form.email.data)
            new_user.set_password(form.password.data)
            new_user.confirmed = False

            try:
                # Try to save this new user (implicitly validating the uniqueness of email/username)
                new_user.save()

                # Generate and send a confirmation email to this new Physician user
                email_sent = email_physician_confirmation(email=form.email.data, name=form.full_name.data)

                if email_sent:
                    success_msg = "Account successfully created. Please check your email for a confirmation link " \
                                  " in order to login."
                    flash(success_msg, 'success')
                    return redirect('/')
                else:
                    flash('We were unable to send your confirmation email. Please ensure the provided email address " \
                          "is correct.', 'warning')

            except NotUniqueError:
                flash("That username or email is already registered. Please try a different one.", 'warning')

            return render_template('register.html', form=form)

        else:
            flash("Invalid input: please see the suggestions below.", 'warning')
    return render_template('register.html', form=form)


@user_management.route('/confirm-account')
def confirm_account():
    """
    New physician users directed here via email link to verify email address.
    Pass in "id" (which represents their account), and mark it to "confirmed".
    """
    id = request.args.get('id')
    user = User.objects.get(email=id.decode('hex'))
    user.confirmed = True
    user.save()
    return render_template('account-confirmed.html', name=user.username)


@user_management.route('/login', methods=['POST'])
def login():
    """
    Compares hash of given password to the password hash of the user with the given username.
    If matching, successfully logs in user. If unsuccessful, show warning and redirect user.
    """
    username = request.form['username']
    login_unsuccessful = "Login failed: Invalid username or password. Please try again."

    # First, ensure that user with given username exists.
    try:
        user = User.objects.get(username=username.lower())
    except DoesNotExist:
        flash(login_unsuccessful, 'warning')
        return redirect('/')

    if not user.confirmed:
        flash("Please first confirm your account by clicking the link in the Account Confirmation email.", 'warning')
        return redirect('/')

    if user.check_password(request.form['password']):
        login_user(user)

        user.last_login = datetime.utcnow()
        user.save()

        message = 'Welcome, {}!'.format(user.full_name)
        flash(message, 'success')
        return redirect('/dashboard')

    flash(login_unsuccessful, 'warning')
    return redirect('/')


@user_management.route('/logout')
@login_required
def logout():
    """
    Deauthenticate current user and log out.
    """
    user = current_user
    user.authenticated = False
    user.save()
    logout_user()
    return redirect('/')


@login_manager.user_loader
def load_user(unique):
    """
    Loads a user after successfully logging into the app.
    """
    user = User.objects(id=unique)
    if user.count() == 1:
        return user[0]
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """
    Show warning and redirect users if they attempt to access privileged resources.
    """
    flash("Unauthorized resource: You'll first need to login to do that.", 'warning')
    return redirect('/')


@app.before_request
def before_request():
    """
    Before each resource request, update user's last_activity attribute.
    """
    if current_user.is_authenticated:
        current_user.last_active = datetime.utcnow()
        current_user.save()


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


@user_management.route('/settings/export', methods=['GET'])
@login_required
def export_all():
    user = current_user
    files = []
    for patient in user.patients:
        files.append(patient.export_data_as_json())
    zipfile = app.config['JSON_FOLDER'] + 'recover_data.zip'
    command = 'zip -j ' + zipfile
    for f in files:
        command += ' ' + f
    os.system('rm ' + zipfile)
    os.system(command)

    return send_from_directory(directory=app.config['JSON_FOLDER'], filename='recover_data.zip',
                               as_attachment=True, attachment_filename='recover_data.zip')


# Admin section - WIP #
from recover.forms import AdminViewer


@user_management.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if str(current_user) != 'admin':
        flash('Error: Restricted Access', 'warning')
        return redirect('/')
    userForms = []
    for user in User.objects():
        form = AdminViewer.AdminUsers(request.form, [user.username, user.email])
        form.username.data = user.username
        form.email.data = user.email
        form.meta = user.id
        userForms.append(form)

    patientForm = AdminViewer.AdminPatients(request.form)
    if request.method == 'POST':
        string = '%s' % request.form.__str__()
        flash(string, 'success')
        return redirect('/admin')
    return render_template('admin.html', userForms=userForms)
