import json
import requests
import sys
import datetime

def authenticate(username, password, authen_base_url):
    authen_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' 
    }

    credential = {'username': username, 'password': password}
    authen_url = authen_base_url + '/api/authenticate'

    try:
        response = requests.post(authen_url, data=json.dumps(credential), headers=authen_headers)
        status_code = response.status_code
        response_text = response.text

        # ✅ Successful authentication
        if status_code == 200:
            access_token = response.json().get('accessToken')
            print(f"{datetime.datetime.now()}: Authentication successful!")
            print(f"Received access token: {access_token[:10]}... [truncated]")
            return access_token
        
        # 🚨 Handle specific API error cases
        elif status_code == 400:
            sys.stderr.write(f"\n{datetime.datetime.now()} - ERROR: 400 Bad Request\n")
            sys.stderr.write(f"Request URL: {authen_url}\n")
            sys.stderr.write(f"Request Headers: {json.dumps(authen_headers, indent=2)}\n")
            sys.stderr.write(f"Request Body: {json.dumps(credential, indent=2)}\n")
            sys.stderr.write(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}\n")
            sys.stderr.write(f"Response Body: {response_text}\n")
            sys.stderr.write("\n🚨 Possible causes: Invalid request format, missing fields, or ICANN API changes.\n")
            exit(1)

        elif status_code == 401:
            sys.stderr.write(f"\n{datetime.datetime.now()} - ERROR: 401 Unauthorized\n")
            sys.stderr.write("Invalid username/password. Please reset your password via web.\n")
            exit(1)

        elif status_code == 404:
            sys.stderr.write(f"\n{datetime.datetime.now()} - ERROR: 404 Not Found\n")
            sys.stderr.write(f"Invalid URL: {authen_url}\n")
            exit(1)

        elif status_code == 429:
            sys.stderr.write(f"\n{datetime.datetime.now()} - ERROR: 429 Too Many Requests\n")
            sys.stderr.write("Rate limit exceeded. Try again later.\n")
            exit(1)

        elif status_code == 500:
            sys.stderr.write(f"\n{datetime.datetime.now()} - ERROR: 500 Internal Server Error\n")
            sys.stderr.write("ICANN API is down. Please try again later.\n")
            exit(1)

        else:
            sys.stderr.write(f"\n{datetime.datetime.now()} - ERROR: Unexpected Status Code {status_code}\n")
            sys.stderr.write(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}\n")
            sys.stderr.write(f"Response Body: {response_text}\n")
            exit(1)

    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"\n{datetime.datetime.now()} - ERROR: Network or Connection Issue\n")
        sys.stderr.write(f"Exception: {str(e)}\n")
        exit(1)
