from flask import Blueprint, render_template
from flask.ext.login import login_required, current_user
from recover.models import Patient
from recover.patient_data import PatientData

patient_dashboard = Blueprint('patient_dashboard', __name__, template_folder='templates')


@patient_dashboard.route('/dashboard')
@login_required
def dashboard():
    """ Renders patients/list.html with all of the patients as input """
    people = current_user.patients
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
