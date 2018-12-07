import json
import requests
import sys
import datetime

def authenticate(username, password, authen_base_url):
    authen_headers = {'Content-Type': 'application/json',
                      'Accept': 'application/json'}

    credential = {'username': username,
                  'password': password}

    authen_url = authen_base_url + '/api/authenticate'

    response = requests.post(authen_url, data=json.dumps(credential), headers=authen_headers)

    status_code = response.status_code

    # Return the access_token on status code 200. Otherwise, terminate the program.
    if status_code == 200:
        access_token = response.json()['accessToken']
        print('{0}: Received access_token:'.format(datetime.datetime.now()))
        print(access_token)
        return access_token
    elif status_code == 404:
        sys.stderr.write("Invalid url " + authen_url)
        exit(1)
    elif status_code == 401:
        sys.stderr.write("Invalid username/password. Please reset your password via web")
        exit(1)
    elif status_code == 500:
        sys.stderr.write("Internal server error. Please try again later")
        exit(1)
    else:
        sys.stderr.write("Failed to authenticate user {0} with error code {1}".format(username, status_code))
        exit(1)
