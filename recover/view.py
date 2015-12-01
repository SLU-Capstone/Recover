from flask import request, redirect, Blueprint, render_template
from flask.views import MethodView
from mongoengine import DoesNotExist

from fitbit import Fitbit
from recover.models import Patient
from recover.patient_data import PatientData

patient_dashboard = Blueprint('patient_dashboard', __name__, template_folder='templates')
patient_add = Blueprint('patient_add', __name__)


# noinspection PyAbstractClass
class AddPatient(MethodView):
    @staticmethod
    def get():
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

        new_guy = Patient(slug=fitbit_id, first_name=first, last_name=last, token=token['access_token'],
                          refresh=token['refresh_token'], health_data_per_day=[])
        new_guy.save()
        return redirect('/dashboard')


# noinspection PyAbstractClass
class PatientListView(MethodView):
    @staticmethod
    def get():
        """ Renders patients/list.html with all of the patients as input """
        people = Patient.objects.all()
        return render_template('patients/list.html', patients=people)


# noinspection PyAbstractClass
class PatientDetailView(MethodView):
    @staticmethod
    def get(slug):
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


patient_dashboard.add_url_rule('/dashboard/', view_func=PatientListView.as_view('list'))
patient_dashboard.add_url_rule('/dashboard/<slug>/', view_func=PatientDetailView.as_view('detail'))

patient_add.add_url_rule('/dashboard/add', view_func=AddPatient.as_view('patientAdder'))
