"""
A Python library for accessing the FitBit API.

This library provides a wrapper to the FitBit API and does not provide storage of tokens or caching if that is required.

Most of the code has been adapted from: https://github.com/magnific0/FitBit.py
"""
import base64
import requests
import secret
import urllib


class Fitbit:
    # All information must be as on the https://dev.fitbit.com/apps page.
    def __init__(self):
        self.CLIENT_ID = secret.CLIENT_ID
        self.CLIENT_SECRET = secret.CLIENT_SECRET
        self.REDIRECT_URI = secret.REDIRECT_URI
        # Decide which information the FitBit.py should have access to.
        # Options: 'activity', 'heartrate', 'location', 'nutrition',
        #          'profile', 'settings', 'sleep', 'social', 'weight'
        self.API_SCOPES = (
            'activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight')

        # These settings should probably not be changed.
        self.API_SERVER = 'api.fitbit.com'
        self.WWW_SERVER = 'www.fitbit.com'
        self.AUTHORIZE_URL = 'https://%s/oauth2/authorize' % self.WWW_SERVER
        self.TOKEN_URL = 'https://%s/oauth2/token' % self.API_SERVER

    def get_authorization_uri(self):

        # Parameters for authorization, make sure to select 
        params = {
            'client_id': self.CLIENT_ID,
            'response_type': 'code',
            'scope': ' '.join(self.API_SCOPES),
            'redirect_uri': self.REDIRECT_URI,
            'expires_in': 2592000  # 30 day access
        }

        # Encode parameters and construct authorization url to be returned to user.
        urlparams = urllib.urlencode(params)
        return "%s?%s" % (self.AUTHORIZE_URL, urlparams)

    # Tokes are requested based on access code. Access code must be fresh (10 minutes)
    def get_access_token(self, access_code):

        # Construct the authentication header
        auth_header = base64.b64encode(self.CLIENT_ID + ':' + self.CLIENT_SECRET)
        headers = {
            'Authorization': 'Basic %s' % auth_header,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # Parameters for requesting tokens (auth + refresh)
        params = {
            'code': access_code,
            'grant_type': 'authorization_code',
            'client_id': self.CLIENT_ID,
            'redirect_uri': self.REDIRECT_URI
        }

        # Place request
        resp = requests.post(self.TOKEN_URL, data=params, headers=headers)
        status_code = resp.status_code
        resp = resp.json()

        if status_code != 200:
            raise Exception("Something went wrong exchanging code for token (%s): %s" % (
                resp['errors'][0]['errorType'], resp['errors'][0]['message']))

        # Strip the goodies
        token = dict()
        token['access_token'] = resp['access_token']
        token['refresh_token'] = resp['refresh_token']

        return token

    # Get new tokens based if authentication token is expired
    def refresh_access_token(self, token):

        # Construct the authentication header
        auth_header = base64.b64encode(self.CLIENT_ID + ':' + self.CLIENT_SECRET)
        headers = {
            'Authorization': 'Basic %s' % auth_header,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # Set up parameters for refresh request
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': token['refresh_token']
        }

        # Place request
        resp = requests.post(self.TOKEN_URL, data=params, headers=headers)

        status_code = resp.status_code
        resp = resp.json()

        if status_code != 200:
            raise Exception("Something went wrong refreshing (%s): %s" % (
                resp['errors'][0]['errorType'], resp['errors'][0]['message']))

        # Distill
        token['access_token'] = resp['access_token']
        token['refresh_token'] = resp['refresh_token']

        return token

    # Place api call to retrieve recover
    def api_call(self, token, call='/1/user/-/activities/log/steps/date/today/1d.json'):
        # Other API Calls possible, or read the FitBit documentation for the full list
        # (https://dev.fitbit.com/docs/), e.g.:
        # apiCall = '/1/user/-/devices.json'
        # apiCall = '/1/user/-/profile.json'
        # apiCall = '/1/user/-/activities/date/2015-10-22.json'

        headers = {
            'Authorization': 'Bearer %s' % token['access_token']
        }

        final_url = 'https://' + self.API_SERVER + call

        resp = requests.get(final_url, headers=headers)

        status_code = resp.status_code

        resp = resp.json()
        resp['token'] = token

        if status_code == 200:
            return resp
        elif status_code == 401:
            print "The access token you provided has been expired let me refresh that for you."
            # Refresh the access token with the refresh token if expired. Access tokens should be good for 1 hour.
            token = self.refresh_access_token(token)
            self.api_call(token, call)
        else:
            raise Exception("Something went wrong requesting (%s): %s" % (
                resp['errors'][0]['errorType'], resp['errors'][0]['message']))
