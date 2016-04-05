import logging
import datetime

from flask import Blueprint, render_template, flash, request
from flask.ext.login import login_required, current_user

from recover import app
from recover.models import Patient
from recover.patient_data import PatientData
from recover.forms.UserRegistrationForm import UserRegistrationForm

patient_dashboard = Blueprint('patient_dashboard', __name__, template_folder='templates')

# Keys for database models
DAILY_DATA = "health_data_per_day"
HR = "heart_rate"
RESTING_HR = "resting_heart_rate"


@patient_dashboard.route('/dashboard')
@login_required
def dashboard():
    """
    Renders the dashboard home for a logged on user.
    Corresponding html file is in `recover/templates/patients/list.html`
    with all of the patients associated with the logged on user as input.
    """
    people = current_user.patients
    return render_template('patients/list.html', physician=current_user, patients=people)


@patient_dashboard.route('/settings/', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Renders the Settings page for a logged-on Physician.
    Corresponding html file is in `recover/templates/settings.html`.
    The UserRegistrationForm class is used to edit account properties as well.
    """
    form = UserRegistrationForm(request.form)
    num_patients = len(current_user.patients)
    date_joined = current_user.id.generation_time.strftime('%b %d, %Y')

    if request.method == 'POST':
        if form.validate():
            flash("Your profile has been updated.", 'success')

            user = current_user
            user.full_name = form.full_name.data
            user.username = form.username.data
            user.email = form.email.data
            user.set_password(form.password.data)
            user.save()
        else:
            flash("Invalid input: please see the suggestions below.", 'warning')

    # Pre-populate form
    form.full_name.data = current_user.full_name
    form.username.data = current_user.username
    form.email.data = current_user.email

    return render_template('settings.html', form=form, user=current_user, num_patients=num_patients, joined=date_joined)


@patient_dashboard.route('/dashboard/<slug>', methods=['GET'])
@login_required
def patient_detail(slug):
    """
    Renders a detailed view of a selected patient. More functionality
    is coming soon! Corresponding html file is in
    `recover/templates/patients/detail.html` with the selected patient
    as input.

    Parameters:
     - *slug*: A unique id associated with a given patient.
    """

    patient = Patient.objects.get_or_404(slug=slug)
    t = datetime.datetime.today()
    try:
        last_pull = patient[DAILY_DATA][-1]['date']
        if last_pull != t.isoformat()[0:10]:
            app.logger.addHandler(logging.FileHandler('log/patient_detail.txt'))
            app.logger.info(last_pull)
            app.logger.info(t.isoformat()[0:10])
            today = t
            last = datetime.datetime.strptime(last_pull, '%Y-%m-%d')
            days = (today - last).days
            PatientData(patient).get_heart_rate_data_for_X_days(days)
        resting_hr = 0
        d = {}
        hrDaily = {}
        start = patient[DAILY_DATA][0]['date']
        end = patient[DAILY_DATA][-1]['date']
        for i in range(0, len(patient[DAILY_DATA])):
            d.update(patient[DAILY_DATA][i][HR])
            resting_hr += patient[DAILY_DATA][-1][RESTING_HR]
            hrDaily[patient[DAILY_DATA][i]['date']] = patient[DAILY_DATA][i][RESTING_HR]
        resting_hr /= len(patient[DAILY_DATA])

    except (KeyError, IndexError):
        p = PatientData(patient)
        if p.get_heart_rate_data_for_day():
            resting_hr = patient[DAILY_DATA][-1][HR]
            d = patient[DAILY_DATA][-1][HR]
        else:
            resting_hr = "No Data."
            d = "No Data."
        start = patient[DAILY_DATA][0]['date']
        end = patient[DAILY_DATA][-1]['date']

    return render_template('patients/detail.html', patient=patient, resting=resting_hr, hrDaily=hrDaily, data=d, start=start, end=end)
