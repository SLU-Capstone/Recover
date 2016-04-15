from flask import Blueprint, request, flash, render_template, redirect
from flask.ext.login import login_required, current_user
from mongoengine import DoesNotExist

from recover.EmailClient import email_patient_invite
from recover.fitbit import Fitbit
from recover.forms.AddPatientForm import AddPatientForm
from recover.models import PatientInvite, Patient, PatientConfig
from recover.patient_data import PatientData

patient_add = Blueprint('patient_add', __name__)


@patient_add.route('/dashboard/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    """
    Allows a physician to enter in patient information and for an
    invitational email to be sent to the patient. The PatientInvite
    is then stored so as to not spam the patient and for logging purposes.
    """
    form = AddPatientForm(request.form)
    if request.method == 'POST':
        try:
            # First, ensure this physician is not already monitoring this patient
            if current_user.patients.objects(email=form.email.data).count() > 0:
                flash("Error: You are already monitoring this patient. Please specify a new patient.", 'warning')
                return render_template('add-patient.html', form=form)
        except AttributeError:
            pass  # Patients table is empty, so no need to check

        if form.validate():

            # Don't allow physician to send duplicate invite requests to a new patient
            if PatientInvite.objects(email=form.email.data, inviting_physician=current_user.to_dbref()).count() > 0:
                flash("Warning: You have already invited this patient to join.", 'warning')
                return redirect('/dashboard')

            # Generate a PatientInvite object and send an invite email to given patient
            invite = PatientInvite(inviting_physician=current_user.to_dbref(), accepted=False, email=form.email.data,
                                   first_name=form.first_name.data, last_name=form.last_name.data)
            invite.save()

            email_sent = email_patient_invite(email=form.email.data, first_name=form.first_name.data,
                                              invite_id=str(invite.id), physician_name=current_user.full_name)

            if email_sent:
                success_msg = "{fname} {lname} has been emailed an invitation, and will appear" \
                              " on your Dashboard after granting access.".format(fname=form.first_name.data,
                                                                                 lname=form.last_name.data)
                flash(success_msg, 'success')
            else:
                flash('We were unable to send the patient invitation. Please ensure the address provided is correct.',
                      'warning')

            return redirect('/dashboard')
        else:
            flash("Invalid input: please see the suggestions below.", 'warning')

    return render_template('add-patient.html', form=form)


@patient_add.route('/authorize', methods=['GET'])
def authorize_new_patient():
    """
    This is called once a patient clicks the confirmation link in their email.
    Redirect a new patient to Fitbit to authorize our app via OAuth 2 Authorization Grant Flow, and
    then receives access token (for making API calls on the user's behalf) as well as a
    refresh token (for obtaining a new access token when the access token expires).
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
            PatientInvite.delete(invite)
            new_patient = Patient(slug=fitbit_id, first_name=invite.first_name, last_name=invite.last_name,
                                  email=invite.email, token=token['access_token'], refresh=token['refresh_token'],
                                  health_data_per_day=[], date_last_synced='')
            new_patient.save()

            # By default, get 5 days worth of data for the brand new patient
            new_patient_data = PatientData(new_patient)
            retrieved = new_patient_data.get_heart_rate_data_for_x_days(5)
            retrieved = retrieved and new_patient_data.get_activity_data_for_x_days(5)
            if not retrieved:
                flash('Could not retrieve Patient data', 'warning')
                return redirect('/')

            # Now save this patient to the inviting physician's list of patients.
            inviting_physician = invite.inviting_physician
            inviting_physician.patients.append(new_patient)
            inviting_physician.save()

            # Now attach a generic config to Patient for the Physician to edit later
            min_hr_default = {'value': 50, 'window': 15}  # BPS / minute
            max_hr_default = {'value': 110, 'window': 15} # BPS / minute
            min_steps_default = {'value': 500, 'window': 60 * 12} # steps / 12 hr
            max_steps_default = {'value': 5000, 'window': 60} # steps / 1 hr
            config = PatientConfig(minHR=min_hr_default, maxHR=max_hr_default, minSteps=min_steps_default,
                                   maxSteps=max_steps_default, patient=new_patient)
            inviting_physician.patient_config.append(config)
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
    Page to offer gratitude to a patient who just confirmed their account.
    """
    fname = request.args.get('name')
    return render_template('patient-registered.html', name=fname)
