import sendgrid
from flask import json

import secret
import logging
from recover import app

BASE_PATH = "getrecover.co"
CONFIRM_ROUTE = "/confirm-account?id="
FROM_ADDRESS = "notifications@" + BASE_PATH


def send_email(destination_email, recipient_name, subject, message):
    """
    Sends an email to recipient_name at destination_email with the given subject and message.

    :param destination_email: email recipient
    :param recipient_name: name of person receiving email
    :param subject: subject of email message
    :param message: body of the email message
    :returns: True or False indicating whether email was sent successfully.
    """
    sg = sendgrid.SendGridClient(secret.SENDGRID_API_KEY, raise_errors=True)
    to = '{} <{}>'.format(recipient_name, destination_email)
    html = message.replace('\n', '</br>')

    message = sendgrid.Mail(to=to, subject=subject, html=html, text=message, from_name="Recover App",
                            from_email=FROM_ADDRESS)

    if app.debug:
        app.logger.addHandler(logging.FileHandler(app.config['INFO'] + 'email_client.txt'))

    try:
        status, msg = sg.send(message)
        if app.debug:
            app.logger.info('Email send successfully: %s - %s' % (status, message))
        return True
    except sendgrid.SendGridError as e:
        if app.debug:
            app.logger.info('A SendGrid error occurred: %s - %s - %s - %s' % (e.__class__, e, status, message))
        return False


def email_patient_invite(email, name, invite_id, physician_name):
    """
    Sends an invitation email to a patient with the name of their inviting physician,
    including a confirmation link to sign up for the service.

    :param email: Email address of a patient that is being invited to our system
    :param name: Name of patient being invited
    :param invite_id: Unique id associated with a physician to link the patient to
    :param physician_name: Physician's name for the invitation
    :returns True or False indicating whether the email was sent successfully
    """

    message = 'Hello {name}, <br><br>' \
              '{physician} has invited you to join Recover.<br>' \
              'Please click the confirmation link below to grant Recover access to your Fitbit data.<br><br>' \
              'http://{URL}/authorize?state={invite_id}<br><br>' \
              'Thank you,<br>' \
              'Recover Team'.format(name=name, physician=physician_name,
                                    URL=BASE_PATH, invite_id=invite_id)

    subject = "You're invited to Recover!"

    return send_email(email, name, subject, message)


def email_physician_confirmation(email, name):
    """
    Sends an account confirmation email to a new physician user.
    This verifies that the user has access to the email address they provided,
    and that they will be able to receive future service-related alerts.

    :param email: Email of new physician registering for our system
    :param name: Name of new physician for register confirmation
    :returns True or False whether or no the email was sent successfully
    """

    link = 'http://' + BASE_PATH + CONFIRM_ROUTE + email.encode('hex')

    message = 'Hello {name}, <br><br>' \
              'Thank you for registering for Recover! ' \
              'Please click the confirmation link below to confirm your account. <br><br>' \
              '{link}<br><br>' \
              'Thank you,<br>' \
              'Recover Team'.format(name=name, link=link)

    subject = "Required: Please Confirm Recover Account"

    return send_email(email, name, subject, message)
