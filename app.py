from flask import Flask, redirect, request
import fitbit 
import json

app = Flask(__name__)
z = fitbit.Fitbit();

@app.route('/')
def index():
    # If not generate a new file
    # Get the authorization URL for user to complete in browser.
    auth_url = z.GetAuthorizationUri()
    return redirect(auth_url)

@app.route('/welcome')
def hey():
    access_code = request.args.get('code')
    
    try:
        token = z.GetAccessToken(access_code)
    except Exception as e:
        return e
    
    # Sample API calls
    try:
        response = z.ApiCall(token, '/1/user/-/profile.json')
    except Exception as e:
        return e
    name = response['user']['displayName']

    try:
        response = z.ApiCall(token, '/1/user/-/activities/heart/date/today/1d.json')
    except Exception as e:
        return e
    resting = str(response['activities-heart'][0]['value']['restingHeartRate'])
    
    try:
        response = z.ApiCall(token, '/1/user/-/activities/steps/date/today/1d.json')
    except Exception as e:
        return e
    steps = str(response['activities-steps'][0]['value'])

    return 'Hello, %s. You took %s steps today and your resting HR was %s' \
            % (name, steps, resting)

if __name__ == '__main__':
    app.run()
