import logging
import datetime
import os

from flask import Blueprint, render_template, flash, request, send_from_directory
from flask.ext.login import login_required, current_user
from recover import app
from recover.models import Patient, check_password_hash, generate_password_hash
from recover.patient_data import PatientData
from recover.forms.EditProfileForm import EditProfileForm
from recover.forms.ChangePasswordForm import ChangePasswordForm

patient_dashboard = Blueprint('patient_dashboard', __name__, template_folder='templates')

# Keys for database models
DAILY_DATA = "health_data_per_day"
HR = "heart_rate"
RESTING_HR = "resting_heart_rate"
STEPS = "activity_data"


@patient_dashboard.route('/dashboard')
@login_required
def dashboard():
    """
    Renders the dashboard home for a logged on user.
    Corresponding html file is in `recover/templates/patients/dashboard.html`
    with all of the patients associated with the logged on user as input.
    """
    people = current_user.patients
    return render_template('patients/dashboard.html', physician=current_user, patients=people)


@patient_dashboard.route('/settings/', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Renders the Settings page for a logged-on Physician.
    Corresponding html file is in `recover/templates/settings.html`.
    The EditProfileForm class is used to edit account properties.
    """
    form = EditProfileForm(request.form)
    password_form = ChangePasswordForm()

    num_patients = len(current_user.patients)
    date_joined = current_user.id.generation_time.strftime('%b %d, %Y')

    if request.method == 'POST':
        if form.validate():
            flash("Your profile has been updated.", 'success')

            user = current_user
            user.full_name = form.full_name.data
            user.username = form.username.data
            user.email = form.email.data
            user.save()
        else:
            flash("Invalid input: please see the suggestions below.", 'warning')

    # Pre-populate form
    form.full_name.data = current_user.full_name
    form.username.data = current_user.username
    form.email.data = current_user.email

    return render_template('settings.html', form=form, password_form=password_form, user=current_user,
                           num_patients=num_patients, joined=date_joined)


@patient_dashboard.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Submit 'change user password' form from Settings page to this endpoint.
    If new passwords match and user entered correct current password, then update user's password accordingly.
    """
    if request.form['current'] is None or request.form['new'] is None or request.form['new_confirm'] is None:
        return "An error occurred, please try again later."
    else:
        current = request.form['current']
        new = request.form['new']
        new_confirm = request.form['new_confirm']
        if check_password_hash(current_user.password, current):
            if new == new_confirm:
                current_user.password = generate_password_hash(new)
                return "success"
            else:
                return "The 'new password' and 'repeat new password' fields do not match."
        else:
            return "Incorrect current password. Please try again."


@patient_dashboard.route('/dashboard/<slug>', methods=['GET'])
@login_required
def patient_profile(slug):
    """
    Renders a detailed view of a selected patient's profile.
    Corresponding html file is in `recover/templates/patients/profile.html`
    :param slug: A unique id associated with a given patient.
    """

    patient = Patient.objects.get_or_404(slug=slug)
    today = datetime.datetime.today()
    end = today
    start = end - datetime.timedelta(days=1)
    try:
        last_pull = patient.date_last_synced
        if last_pull != today.isoformat()[0:10]:
            app.logger.addHandler(logging.FileHandler('log/patient_profile.txt'))
            app.logger.info(last_pull)
            app.logger.info(today.isoformat()[0:10])
            today = today
            last = datetime.datetime.strptime(last_pull, '%Y-%m-%d')
            days = (today - last).days
            patient_data = PatientData(patient)
            patient_data.get_heart_rate_data_for_x_days(days)
            patient_data.get_activity_data_for_x_days(days)
        resting_hr = 0
        HRdata = {}
        HRaverage = {}
        StepsData = {}
        ave_count = 0
        for i in range(0, len(patient[DAILY_DATA])):
            HRdata.update(patient[DAILY_DATA][i][HR])
            StepsData.update(patient[DAILY_DATA][i][STEPS])
            try:
                resting_hr += patient[DAILY_DATA][i][RESTING_HR]
                ave_count += 1
            except TypeError:
                pass
            HRaverage[patient[DAILY_DATA][i]['date']] = patient[DAILY_DATA][i][RESTING_HR]
        resting_hr /= ave_count

    except (KeyError, IndexError):
        p = PatientData(patient)
        if p.get_heart_rate_data_for_day():
            resting_hr = patient[DAILY_DATA][-1][HR]
            HRdata = patient[DAILY_DATA][-1][HR]
        else:
            resting_hr = "No Data."
            HRdata = "No Data."

    return render_template('patients/profile.html', patient=patient, resting=resting_hr, HRaverage=HRaverage,
                           HRdata=HRdata, StepsData=StepsData, start=start, end=end)


@patient_dashboard.route('/dashboard/<slug>/export', methods=['GET'])
@login_required
def export(slug):
    """
    Allows all health data associated with a given patient to be downloaded.
    The data is in the form of a JSON file and is zipped.

    :param slug: A unique id associated with a given patient.
    """
    patient = Patient.objects.get_or_404(slug=slug)
    file_name = patient.export_data_as_json()
    zipfile = app.config['JSON_FOLDER'] + 'recover_data.zip'
    command = 'zip -j ' + zipfile + ' ' + file_name
    os.system('rm ' + zipfile)
    os.system(command)
    return send_from_directory(directory=app.config['JSON_FOLDER'], filename='recover_data.zip',
                               as_attachment=True, attachment_filename='recover_data.zip')
