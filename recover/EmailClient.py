import mandrill
import secret


def send_email(destination_email, recipient_name, subject, message):
    """
    Sends an email to recipient_name at destination_email with the subject,
    subject and the message, message
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
        return result
    except mandrill.Error as e:
        print 'A mandrill error occurred: %s - %s' % (e.__class__, e)
        raise


def email_patient_invite(email, first_name, invite_id, physician_name):
    """
    Sends an email to a patient alerting them that their physician wishes
    for them to sign up for the service.
    """
    message = "Hello " + first_name + ",\n\n" + physician_name + " has invited you to join Recover." \
              "\n\nPlease click the confirmation link to grant Recover access to your Fitbit data." \
              "\n\n162.243.19.76/authorize?state=" + invite_id

    return send_email(email, first_name, "You're invited to Recover!", message)
