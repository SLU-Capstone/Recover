import sendgrid
import secret
import logging
from recover import app

BASE_PATH = "162.243.19.76"
CONFIRM_ROUTE = "/confirm-account?id="
FROM_ADDRESS = "notifications@getrecover.co"


def send_email(destination_email, recipient_name, subject, message):
    """
    Sends an email to recipient_name at destination_email with the given subject and message.
    :returns: True or False indicating whether email was sent successfully.
    """
    sg = sendgrid.SendGridClient(secret.SENDGRID_API_KEY, raise_errors=True)
    to = '{} <{}>'.format(recipient_name, destination_email)
    html = message.replace('\n', '</br>')

    message = sendgrid.Mail(to=to, subject=subject, html=html, text=message, from_name="Recover App",
                            from_email=FROM_ADDRESS)

    app.logger.addHandler(logging.FileHandler('log/email_client.txt'))

    try:
        status, msg = sg.send(message)
        app.logger.info('Email send successfully: %s - %s' % (status, message))
        return True
    except sendgrid.SendGridError as e:
        app.logger.info('A SendGrid error occurred: %s - %s - %s - %s' % (e.__class__, e, status, message))
        return False


def email_patient_invite(email, name, invite_id, physician_name):
    """
    Sends an invitation email to a patient with the name of their inviting physician,
    including a confirmation link to sign up for the service.
    """

    message = 'Hello {name}, \n\n' \
              '{physician} has invited you to join Recover.\n\n' \
              'Please click the confirmation link below to grant Recover access to your Fitbit data.\n\n' \
              'http://{URL}/authorize?state={invite_id}'.format(name=name, physician=physician_name,
                                                                URL=BASE_PATH, invite_id=invite_id)

    subject = "You're invited to Recover!"

    return send_email(email, name, subject, message)


def email_physician_confirmation(email, name):
    """
    Sends an account confirmation email to a new physician user.
    This verifies that the user has access to the email address they provided,
    and that they will be able to receive future service-related alerts.
    """

    link = 'http://' + BASE_PATH + CONFIRM_ROUTE + email.encode('hex')

    message = 'Hello {name}, \n\n' \
              'Thank you for registering for Recover. \n\n' \
              'Please click the confirmation link below to confirm your account. \n\n' \
              '{link}\n\n' \
              'Thank you,\n' \
              'Recover Team'.format(name=name, link=link)

    subject = "Required: Please Confirm Recover Account"

    return send_email(email, name, subject, message)
