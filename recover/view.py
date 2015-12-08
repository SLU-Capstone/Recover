from flask import request, redirect, Blueprint, render_template, flash
from flask.ext.login import current_user, login_user, logout_user, login_required
from mongoengine import DoesNotExist
from recover import login_manager
from fitbit import Fitbit
from recover.models import Patient, User, PatientInvite
from recover.patient_data import PatientData
from recover.UserRegistrationForm import UserRegistrationForm
from recover.AddPatientForm import AddPatientForm
from recover.EmailClient import email_patient_invite

patient_dashboard = Blueprint('patient_dashboard', __name__, template_folder='templates')
patient_add = Blueprint('patient_add', __name__)
user_management = Blueprint('user_management', __name__, template_folder='templates')


@patient_add.route('/dashboard/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    form = AddPatientForm(request.form)
    if request.method == 'POST':
        try:
            # Ensure this physician is not already monitoring this patient
            if current_user.patients.objects(email=form.email.data).count() > 0:
                flash("Error: You are already monitoring this patient. Please specify a new patient.", 'warning')
                return render_template('add-patient.html', form=form)
        except AttributeError:
            pass  # Patients table is empty, so no need to check

        if form.validate():
            # Use Mandrill to generate and send an invite email to patient
            invite = PatientInvite(inviting_physician=current_user, accepted=False, email=form.email.data)
            invite.save()
            resp = email_patient_invite(form.email.data, form.first_name.data, invite_id)
            if resp[0]['status'] == "sent":
                flash("Patient has been invited. They will appear on your Dashboard after granting access.", 'success')

                ''' #TODO: - generate dynamic code to send in patient invite.
                           - associate this patient and email with the Physician that invited them,
                             i.e. so not all physicians can see each other's patients!
                '''
            else:
                flash("There was an error in sending the patient invitation. Please try again later.", 'warning')
            return redirect('/dashboard')
        else:
            flash("Invalid input: please see the suggestions below.", 'warning')
    return render_template('add-patient.html', form=form)


@patient_add.route('/authorize', methods=['GET'])
# @login_required // patients cant log in
def authorize_new_patient():
    """
    This is called once a patient clicks the confirmation link in their email.
    Send a new patient to Fitbit to authorize our app, then
    receives access code to get token.
    """
    ''' #TODO: Need to determine how to persist <id> through the OAauth request process in order to associate the
        returned Fitbit account with the Physician that invited the user who clicked the link in the email. '''
    access_code = request.args.get('code')
    invite_id = request.args.get('state')
    api = Fitbit()
    if access_code is None:
        auth_url = api.get_authorization_uri(invite_id)
        return redirect(auth_url)
    try:
        token = api.get_access_token(access_code)
    except Exception as e:
        return e
    try:
        response = api.api_call(token, '/1/user/-/profile.json')
    except Exception as e:
        return e

    fullname = response['user']['fullName']
    first, last = fullname.split()
    fitbit_id = response['user']['encodedId']

    # Ensure this patient has been invited by a physician.
    try:
        Patient.objects.get(slug=fitbit_id)
        return redirect('/thanks')
    except DoesNotExist:
        # This is good!
        pass

    new_patient = Patient(slug=fitbit_id, first_name=first, last_name=last, token=token['access_token'],
                          refresh=token['refresh_token'], health_data_per_day=[])
    new_patient.save()
    return redirect('/thanks invited by' + str(User.username))

@patient_add.route('/thanks')
def thanks():
    return 'Thanks'


@patient_dashboard.route('/dashboard')
@login_required
def dashboard():
    """ Renders patients/list.html with all of the patients as input """
    people = Patient.objects.all()
    return render_template('patients/list.html', physician=current_user, patients=people)


# noinspection PyAbstractClass
@patient_dashboard.route('/dashboard/<slug>', methods=['GET'])
@login_required
def patient_detail(slug):
    """
    Renders patients/details.html with one of the patients as input.
    We will need to extend the functionality of this in order to pass
    additional health information.
    :param slug: unique id
    """
    patient = Patient.objects.get_or_404(slug=slug)
    try:
        resting_hr = patient['health_data_per_day'][0]['resting_heart_rate']
        d = patient['health_data_per_day'][-1]['heart_rate']
    except (KeyError, IndexError):
        p = PatientData(patient)
        if p.get_heart_rate_data_for_day():
            resting_hr = patient['health_data_per_day'][-1]['resting_heart_rate']
            d = patient['health_data_per_day'][-1]['heart_rate']
        else:
            resting_hr = "No Data."
            d = "No Data."

    return render_template('patients/detail.html', patient=patient, resting=resting_hr, data=d)


@user_management.route('/register/', methods=['GET', 'POST'])
def register():
    form = UserRegistrationForm(request.form)
    if request.method == 'POST':
        try:
            if User.objects(email=form.email.data).count() > 0:
                flash("A user with that email already exists. Please try again.", 'warning')
                return render_template('register.html', form=form)
        except AttributeError:
            pass  # Users table is empty, so no need to check.

        if form.validate():
            new_user = User(username=form.username.data, email=form.email.data)
            new_user.set_password(form.password.data)
            new_user.save()
            flash("User registration successful. You can now login above.", 'success')
            return redirect('/')
        else:
            flash("Invalid input: please see the suggestions below.", 'warning')
    return render_template('register.html', form=form)


@user_management.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    login_unsuccessful = "Login failed: Invalid email or password. Please try again."

    try:  # User with given email does not exist
        user = User.objects.get(email=email)
    except DoesNotExist:
        flash(login_unsuccessful, 'warning')
        return redirect('/')

    if user.check_password(request.form['password']):
        login_user(user)
        message = "Welcome, " + user.username + "!"
        flash(message, 'success')
        return redirect('/dashboard')

    flash(login_unsuccessful, 'warning')
    return redirect('/')


@login_manager.user_loader
def load_user(email):
    user = User.objects(email=email)
    if user.count() == 1:
        return user[0]
    return None


@login_manager.unauthorized_handler
def unauthorized():
    # customize message shown for unauthorized route access.
    flash("Unauthorized resource: You'll first need to login to do that.", 'warning')
    return redirect('/')


@user_management.route('/logout')
@login_required
def logout():
    user = current_user
    user.authenticated = False
    user.save()
    logout_user()
    return redirect('/')
