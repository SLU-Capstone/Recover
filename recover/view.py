from recover.models import Patient
from recover.patientdata import PatientData
from flask import request, redirect, Blueprint, render_template, url_for
from flask.views import MethodView
from fitbit import Fitbit
from mongoengine import DoesNotExist

patients = Blueprint('patients', __name__, template_folder='templates')
register = Blueprint('register', __name__)


class PatientAdder(MethodView):
    def get(self):
        """
        Send a new patient to Fitbit to authorize our app, then
        receives access code to get token.
        """
        access_code = request.args.get('code')
        fitterbitter = Fitbit()
        if access_code is None:
            auth_url = fitterbitter.get_authorization_uri()
            return redirect(auth_url)
        try:
            token = fitterbitter.get_access_token(access_code)
        except Exception as e:
            return e
        # get the name
        try:
            response = fitterbitter.api_call(token, '/1/user/-/profile.json')
        except Exception as e:
            return e
        fullname = response['user']['fullName']
        first, last = fullname.split(' ')
        fitbit_id = response['user']['encodedId']

        try:
            inside = Patient.objects.get(slug=fitbit_id)
            # if exception is not raised, we failed
            return redirect('/')
        except DoesNotExist as e:
            # This is good!
            pass

        new_guy = Patient(slug=fitbit_id, first_name=first, last_name=last, token=token['access_token'], refresh=token['refresh_token'])
        new_guy.save()
        return redirect('/')


class ListView(MethodView):
    def get(self):
        """ Renders patients/list.html with all of the patients as input """
        people = Patient.objects.all()
        return render_template('patients/list.html', patients=people)


class DetailView(MethodView):
    def get(self, slug):
        """
        Renders patients/details.html with one of the patients as input.
        We will need to extend the functionality of this in order to pass
        additional health information.
        """
        patient = Patient.objects.get_or_404(slug=slug)
        resting_hr = PatientData(patient).get_resting_heart_rate()
        return render_template('patients/detail.html', patient=patient, resting=resting_hr)


patients.add_url_rule('/', view_func=ListView.as_view('list'))
patients.add_url_rule('/<slug>/', view_func=DetailView.as_view('detail'))
register.add_url_rule('/register/', view_func=PatientAdder.as_view('patientAdder'))
