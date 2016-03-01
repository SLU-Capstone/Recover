import logging
import datetime

from flask import Blueprint, render_template
from flask.ext.login import login_required, current_user

from recover import app
from recover.models import Patient
from recover.patient_data import PatientData

patient_dashboard = Blueprint('patient_dashboard', __name__, template_folder='templates')


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
        last_pull = patient['health_data_per_day'][-1]['date']
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
        start = patient['health_data_per_day'][0]['date']
        end = patient['health_data_per_day'][-1]['date']
        for i in range(0,len(patient['health_data_per_day'])):
            d.update(patient['health_data_per_day'][i]['heart_rate'])
            resting_hr += patient['health_data_per_day'][-1]['resting_heart_rate']
        resting_hr /= len(patient['health_data_per_day'])

    except (KeyError, IndexError):
        p = PatientData(patient)
        if p.get_heart_rate_data_for_day():
            resting_hr = patient['health_data_per_day'][-1]['resting_heart_rate']
            d = patient['health_data_per_day'][-1]['heart_rate']
        else:
            resting_hr = "No Data."
            d = "No Data."
        start = patient['health_data_per_day'][0]['date']
        end = patient['health_data_per_day]'][-1]['date']

    return render_template('patients/detail.html', patient=patient, resting=resting_hr, data=d, start=start, end=end)
