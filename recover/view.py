from flask import request, redirect, Blueprint, render_template
from flask.views import MethodView
from mongoengine import DoesNotExist

from fitbit import Fitbit
from recover.models import Patient, Data

patients = Blueprint('patients', __name__, template_folder='templates')
register = Blueprint('register', __name__)
data = Blueprint('data', __name__)


# noinspection PyAbstractClass
class PatientAdder(MethodView):
    @staticmethod
    def get():
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
            Patient.objects.get(slug=fitbit_id)
            # if exception is not raised, we failed
            return redirect('/')
        except DoesNotExist:
            # This is good!
            pass

        new_guy = Patient(slug=fitbit_id, first_name=first, last_name=last, token=token['access_token'],
                          refresh=token['refresh_token'], data=[])
        new_guy.save()
        return redirect('/')


# noinspection PyAbstractClass
class ListView(MethodView):
    @staticmethod
    def get():
        """ Renders patients/list.html with all of the patients as input """
        people = Patient.objects.all()
        return render_template('patients/list.html', patients=people)


# noinspection PyAbstractClass
class DetailView(MethodView):
    @staticmethod
    def get(slug):
        """
        Renders patients/details.html with one of the patients as input.
        We will need to extend the functionality of this in order to pass
        additional health information.
        :param slug: unique id
        """
        patient = Patient.objects.get_or_404(slug=slug)
        resting_hr = patient.data.resting_heart_rate
        return render_template('patients/detail.html', patient=patient, resting=resting_hr)


patients.add_url_rule('/', view_func=ListView.as_view('list'))
patients.add_url_rule('/<slug>/', view_func=DetailView.as_view('detail'))
register.add_url_rule('/register/', view_func=PatientAdder.as_view('patientAdder'))
