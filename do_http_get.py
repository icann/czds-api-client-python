import requests

def do_get(url, access_token):

    bearer_headers = {'Content-Type': 'application/json',
                      'Accept': 'application/json',
                      'Authorization': 'Bearer {0}'.format(access_token)}

    response = requests.get(url, params=None, headers=bearer_headers, stream=True)

    return response
