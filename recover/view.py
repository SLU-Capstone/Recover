from flask import request, redirect, Blueprint, render_template, flash
from flask.ext.login import current_user, login_user, logout_user, login_required
from mongoengine import DoesNotExist
from recover import login_manager
from fitbit import Fitbit
from recover.models import Patient, User
from recover.patient_data import PatientData
from recover.UserRegistrationForm import UserRegistrationForm

patient_dashboard = Blueprint('patient_dashboard', __name__, template_folder='templates')
patient_add = Blueprint('patient_add', __name__)
user_management = Blueprint('user_management', __name__, template_folder='templates')


@patient_add.route('/dashboard/add', methods=['GET'])
@login_required
def add_patient():
    """
    Send a new patient to Fitbit to authorize our app, then
    receives access code to get token.
    """
    access_code = request.args.get('code')
    api = Fitbit()
    if access_code is None:
        auth_url = api.get_authorization_uri()
        return redirect(auth_url)
    try:
        token = api.get_access_token(access_code)
    except Exception as e:
        return e
    # get the name
    try:
        response = api.api_call(token, '/1/user/-/profile.json')
    except Exception as e:
        return e
    fullname = response['user']['fullName']
    first, last = fullname.split(' ')
    fitbit_id = response['user']['encodedId']

    try:
        Patient.objects.get(slug=fitbit_id)
        # if exception is not raised, we failed
        return redirect('/dashboard')
    except DoesNotExist:
        # This is good!
        pass

    new_patient = Patient(slug=fitbit_id, first_name=first, last_name=last, token=token['access_token'],
                          refresh=token['refresh_token'], health_data_per_day=[])
    new_patient.save()
    return redirect('/dashboard')


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
