import mandrill
import secret

BASE_PATH = "162.243.19.76"
CONFIRM_ROUTE = "/confirm-account?id="

def send_email(destination_email, recipient_name, subject, message):
    """
    Sends an email to recipient_name at destination_email with the given subject and message.
    :returns: True or False indicating whether email was sent successfully.
    """
    mandrill_client = mandrill.Mandrill(secret.MANDRILL_API_KEY)
    message = {
        'to': [{'email': destination_email,
                'name': recipient_name,
                'type': 'to'}],
        'from_email': 'notifications@getrecover.co',
        'from_name': 'Recover App',
        'subject': subject,
        'text': message
    }

    try:
        result = mandrill_client.messages.send(message=message)
        return True if result[0]['status'] == "sent" else False
    except mandrill.Error as e:
        print 'A mandrill error occurred: %s - %s' % (e.__class__, e)
        raise
        return False


def email_patient_invite(email, first_name, invite_id, physician_name):
    """
    Sends an invitation email to a patient with the name of their inviting physician,
    including a confirmation link to sign up for the service.
    """

    message = 'Hello {name}, \n\n' \
              '{physician} has invited you to join Recover.\n\n' \
              'Please click the confirmation link below to grant Recover access to your Fitbit data.\n\n' \
              'http://{URL}/authorize?state={invite_id}'.format(name=first_name, physician=physician_name,
                                                                URL=BASE_PATH, invite_id=invite_id)

    subject = "You're invited to Recover!"

    return send_email(email, first_name, subject, message)


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
              '{link}\n\n'\
              'Thank you,\n' \
              'Recover Team'.format(name=name, link=link)

    subject = "Required: Please Confirm Recover Account"

    return send_email(email, name, subject, message)
