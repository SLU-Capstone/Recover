import logging

from flask import Blueprint, render_template
from flask.ext.login import login_required, current_user
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

    # foo = ['this', 'is', 'a', 'series', 'of', 'data']
    return render_template('patients/detail.html', patient=patient, resting=resting_hr, data=d)
