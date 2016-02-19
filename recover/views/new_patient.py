from flask import Blueprint, request, flash, render_template, redirect
from flask.ext.login import login_required, current_user
from mongoengine import DoesNotExist

from recover.EmailClient import email_patient_invite
from recover.fitbit import Fitbit
from recover.forms.AddPatientForm import AddPatientForm
from recover.models import PatientInvite, Patient
from recover.patient_data import PatientData

patient_add = Blueprint('patient_add', __name__)


@patient_add.route('/dashboard/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    """
    Allows a physician to enter in patient information and for an
    invitational email to be sent to the patient. The PatientInvite
    is then stored so as to not spam the patient and for logging
    purposes.
    :return:
    """
    form = AddPatientForm(request.form)
    if request.method == 'POST':
        try:
            # Ensure this physician is not already monitoring this patient
            if current_user.patients.objects(email=form.email.data).count() > 0:
                flash("Error: You are already monitoring this patient. Please specify a new patient.", 'warning')
                return render_template('add-patient.html', form=form)
        except AttributeError:
            pass  # Patients table is empty, so no need to check

        # TODO: refactor out this invitation functionality
        if form.validate():

            # Don't allow Physician to send duplicate invite requests to a new patient
            if PatientInvite.objects(email=form.email.data).count() > 0:
                flash("Warning: You have already invited this patient to join.", 'warning')
                return redirect('/dashboard')

            # Generate and send an invite email to patient
            invite = PatientInvite(inviting_physician=current_user.to_dbref(), accepted=False, email=form.email.data,
                                   first_name=form.first_name.data, last_name=form.last_name.data)
            invite.save()
            resp = email_patient_invite(email=form.email.data, first_name=form.first_name.data,
                                        invite_id=str(invite.id), physician_name=current_user.username)
            if resp[0]['status'] == "sent":
                success_msg = form.first_name.data + " has been emailed an invitation, and will appear" \
                                                     " on your Dashboard after granting access."
                flash(success_msg, 'success')
            else:
                flash("There was an error in sending the patient invitation. Please try again later.", 'warning')
            return redirect('/dashboard')
        else:
            flash("Invalid input: please see the suggestions below.", 'warning')
    return render_template('add-patient.html', form=form)


@patient_add.route('/authorize', methods=['GET'])
def authorize_new_patient():
    """
    This is called once a patient clicks the confirmation link in their email.
    Send a new patient to Fitbit to authorize our app, then receives access
    code to get Fitbit token.
    """
    access_code = request.args.get('code')
    invite_id = request.args.get('state')
    api = Fitbit()

    # Require users to be invited by a physician. Only occurs when they receive an email w/ invite_id (aka "state").
    if invite_id is None:
        flash("Error: an authorization token is required. Please use the confirmation link that was emailed to you.",
              'warning')
        return redirect('/')

    if access_code is None:
        auth_url = api.get_authorization_uri(invite_id)
        return redirect(auth_url)
    try:
        token = api.get_access_token(access_code)
    except Exception as e:
        flash(e.message, 'warning')
        return redirect('/')
    try:
        response = api.api_call(token, '/1/user/-/profile.json')
    except Exception as e:
        flash(e.message, 'warning')
        return redirect('/')

    # fullname = response['user']['fullName']  # Using name entered by Physician on invite instead.
    fitbit_id = response['user']['encodedId']

    try:
        invite = PatientInvite.objects.get(id=invite_id)
        if not invite.accepted:
            invite.accepted = True
            invite.save()
            new_patient = Patient(slug=fitbit_id, first_name=invite.first_name, last_name=invite.last_name,
                                  email=invite.email, token=token['access_token'], refresh=token['refresh_token'],
                                  health_data_per_day=[])
            new_patient.save()

            # get the first months worth of data for the brand new patient
            new_patient_data = PatientData(new_patient)
            if not new_patient_data.get_heart_rate_data_for_period('1m'):
                flash('Could not retrieve Patient data', 'warning')
                return redirect('/')

            # Now save this patient to the inviting physician's list of patients.
            inviting_physician = invite.inviting_physician
            inviting_physician.patients.append(new_patient)
            inviting_physician.save()

            return redirect('/patient-registered?name=' + invite.first_name)
        else:
            flash("It appears you've already confirmed this account.", 'warning')
            return redirect('/')

    except DoesNotExist as e:
        flash(e.__str__(), 'warning')
        return redirect('/')


@patient_add.route('/patient-registered')
def thanks():
    """
    Page to offer gratitude for patients signing up for this program.
    """
    fname = request.args.get('name')
    return render_template('patient-registered.html', name=fname)
