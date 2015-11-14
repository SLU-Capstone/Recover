from recover.models import Patient
from recover.patientdata import PatientData
from flask import request, redirect, Blueprint, render_template, url_for
from flask.views import MethodView

patients = Blueprint('patients', __name__, template_folder='templates')


class ListView(MethodView):
    def get(self):
        people = Patient.objects.all()
        return render_template('patients/list.html', patients=people)


class DetailView(MethodView):
    def get(self, slug):
        patient = Patient.objects.get_or_404(slug=slug)
        resting_hr = PatientData(patient).get_resting_heart_rate()
        return render_template('patients/detail.html', patient=patient, resting=resting_hr)


patients.add_url_rule('/', view_func=ListView.as_view('list'))
patients.add_url_rule('/<slug>/', view_func=DetailView.as_view('detail'))

