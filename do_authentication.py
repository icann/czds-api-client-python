import json
import requests
import sys
import datetime
import time
import urllib.parse

def authenticate(username, password, authen_base_url, retry_attempts=3):
    """Authenticate with ICANN CZDS API and return an access token."""

    authen_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (compatible; CZDS-Client/1.0; +https://github.com/mthcht/czds-api-client-python)'
    }

    credential = {
        "username": username,
        "password": password,  # No encoding for now, unless ICANN blocks special characters
        "grant_type": "password"  # Some APIs require this
    }

    authen_url = authen_base_url + '/api/authenticate'

    for attempt in range(1, retry_attempts + 1):
        try:
            response = requests.post(authen_url, json=credential, headers=authen_headers)
            status_code = response.status_code
            response_text = response.text

            if status_code == 200:
                access_token = response.json().get('accessToken')
                print(f"{datetime.datetime.now()}: Authentication successful!")
                print(f"Received access token: {access_token[:10]}... [truncated]")
                return access_token

            elif status_code == 400:
                sys.stderr.write(f"\n{datetime.datetime.now()} - ERROR: 400 Bad Request\n")
                sys.stderr.write(f"Request Headers: {json.dumps(authen_headers, indent=2)}\n")
                sys.stderr.write(f"Request Body: {json.dumps(credential, indent=2)}\n")
                sys.stderr.write(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}\n")
                sys.stderr.write(f"Response Body: {response_text}\n")
                sys.stderr.write("\n🚨 Possible causes: Invalid request format, missing fields, ICANN API changes, or IP blocking.\n")
                exit(1)

            elif status_code == 401:
                sys.stderr.write("\nERROR: 401 Unauthorized - Invalid username or password.\n")
                exit(1)

            elif status_code == 429:
                wait_time = 2 ** attempt  # Exponential backoff
                sys.stderr.write(f"\nERROR: 429 Too Many Requests - Rate limited. Retrying in {wait_time} seconds...\n")
                time.sleep(wait_time)

            elif status_code == 500:
                sys.stderr.write("\nERROR: 500 Internal Server Error - ICANN API might be down. Try again later.\n")
                exit(1)

            else:
                sys.stderr.write(f"\nERROR: Unexpected Status Code {status_code}\n")
                sys.stderr.write(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}\n")
                sys.stderr.write(f"Response Body: {response_text}\n")
                exit(1)

        except requests.exceptions.RequestException as e:
            sys.stderr.write(f"\nERROR: Network or Connection Issue\n")
            sys.stderr.write(f"Exception: {str(e)}\n")
            exit(1)

    sys.stderr.write("\nERROR: Maximum authentication retries exceeded.\n")
    exit(1)
