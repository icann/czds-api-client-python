import json
import requests


def do_get(url, access_token):

    bearer_headers = {'Content-Type': 'application/json',
                      'Accept': 'application/json',
                      'Authorization': 'Bearer {0}'.format(access_token)}

    response = requests.get(url, params=None, headers=bearer_headers, stream=True)

    return response


def do_post(url, access_token, data=None):
    bearer_headers = {'Content-Type': 'application/json',
                      'Accept': 'application/json',
                      'Authorization': 'Bearer {0}'.format(access_token)}

    if data is None:
        response = requests.post(url, params=None, headers=bearer_headers, stream=True)
    else:
        response = requests.post(url, params=None, data=json.dumps(data), headers=bearer_headers, stream=True)

    return response
