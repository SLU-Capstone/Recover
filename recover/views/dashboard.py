import datetime
import os

from flask import Blueprint, render_template, flash, request, send_from_directory, jsonify
from flask.ext.login import login_required, current_user
from recover import app
from recover.models import User, Patient, check_password_hash, generate_password_hash
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

    fetch_dates = []
    for p in people:
        d = p.date_last_data_fetch.split('-')
        fetch_dates.append('{}/{}/{}'.format(d[1], d[2], d[0]))

    return render_template('patients/dashboard.html', physician=current_user, patients=people, fetch_dates=fetch_dates,
                           alert_counts=alert_counts_per_patient())


def alert_counts_per_patient():
    """
    Returns a dictionary of the number of unread alerts that are outstanding on each patient.
    patient_alerts is keyed by the patient object's id.
    """
    patient_alerts = {}
    for alert in current_user.alerts:
        if not alert.read:
            patient_alerts[alert.patient.id] += 1

    for p in current_user.patients:
        if p not in patient_alerts:
            patient_alerts[p.id] = 0

    return patient_alerts


def unread_alerts(patient_id):
    """
    Returns an array of all unread alerts for a given patient.
    """
    alerts = []
    for alert in current_user.alerts:
        if not alert.read and alert.patient.id == patient_id:
            alerts.append(alert)
    return alerts


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
        last_pull = patient.date_last_data_fetch
        if last_pull != today.isoformat()[0:10]:
            today = today
            last = datetime.datetime.strptime(last_pull, '%Y-%m-%d')
            days = (today - last).days
            patient_data = PatientData(patient)
            PatientData.get_heart_rate_data_for_x_days(patient_data, days)
            PatientData.get_activity_data_for_x_days(patient_data, days)
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
        try:
            resting_hr /= ave_count
        except ZeroDivisionError:
            pass

    except (KeyError, IndexError):
        p = PatientData(patient)
        if p.get_heart_rate_data_for_day():
            resting_hr = patient[DAILY_DATA][-1][HR]
            HRdata = patient[DAILY_DATA][-1][HR]
        else:
            resting_hr = "No Data."
            HRdata = "No Data."

    try:
        last_worn = patient.date_last_worn()
    except Exception as e:
        last_worn = e.message
    return render_template('patients/profile.html', patient=patient, resting=resting_hr, HRaverage=HRaverage,
                           HRdata=HRdata, StepsData=StepsData, start=start, end=end,
                           alerts=unread_alerts(patient.id), config=config_for_patient(patient.id),
                           last_worn=last_worn)


@patient_dashboard.route('/remove-patient', methods=['POST'])
@login_required
def remove_patient():
    """
    Removes a patient from a physician's list of current patients.
    After, we redirect the user back to the dashboard.
    """
    if request.form['slug'] is None:
        return "An error occurred, please try again later."
    else:
        slug = request.form['slug']
        patient = Patient.objects.get_or_404(slug=slug)
        name = "{} {}".format(patient.first_name, patient.last_name)

        # Remove this patient from the physician's list of active patients.
        User.objects(id=current_user.id).update_one(pull__patients=patient)

        # Remove all physician's config settings on this patient.
        for config in current_user.patient_config:
            if config.patient.id == patient.id:
                current_user.patient_config.filter(patient=patient).delete()

        flash('The patient {} has been removed successfully from your dashboard.'.format(name), 'success')
        return jsonify({"status": 200})


@patient_dashboard.route('/update-notes', methods=['POST'])
@login_required
def update_notes():
    """
    Updates the 'notes' field on the PatientConfig object for a given patient.
    """
    if request.form['slug'] is None or request.form['notes'] is None:
        return "An error occurred, please try again later."
    else:
        slug = request.form['slug']
        patient = Patient.objects.get_or_404(slug=slug)
        config = config_for_patient(patient.id)

        config.notes = request.form['notes']
        config.save()

        return jsonify({"status": 200})


@patient_dashboard.route('/dashboard/<slug>/export/<begin>/<end>', methods=['GET'])
@login_required
def export(slug, begin, end):
    """
    Allows all health data associated with a given patient to be downloaded.
    The data is in the form of a JSON file and is zipped.

    :param slug: A unique id associated with a given patient.
    :param begin: string of date to begin in YYYY-MM-DD format
    :param end: string of date to end in YYYY-MM-DD format
    """
    patient = Patient.objects.get_or_404(slug=slug)
    file_name = patient.export_data_as_json(begin, end)
    zipfile = app.config['JSON_FOLDER'] + 'recover_data.zip'
    command = 'zip -j ' + zipfile + ' ' + file_name
    os.system('rm ' + zipfile)
    os.system(command)
    return send_from_directory(directory=app.config['JSON_FOLDER'], filename='recover_data.zip',
                               as_attachment=True, attachment_filename='recover_data.zip')


def config_for_patient(patient_id):
    """
    Returns the physician's config object for a given patient.
    """
    return [c for c in current_user.patient_config if c.patient.id == patient_id][0]
