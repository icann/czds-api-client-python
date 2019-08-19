#!/usr/bin/env python3
import requests
import json
import os
import argparse


class AuthenticationError(Exception):
    pass


class CZDSClient(object):
    czds_api_base = 'https://czds-api.icann.org'
    auth_api = 'https://account-api.icann.org/api/authenticate'
    request_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    _token = None

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def authenticate(self):
        """
        Authenticate against the icann account api.

        :return: authorizaiton token
        """
        creds = {
            'username': self.username,
            'password': self.password,
        }
        response = requests.post(self.auth_api, data=json.dumps(creds), headers=self.request_headers)
        if response.status_code == 401:
            raise AuthenticationError('Invalid Credentials')
        if response.status_code != 200:
            raise Exception('Invalid response code returned by server: {}'.format(response.status_code))
        response_json = response.json()
        if 'accessToken' not in response_json:
            raise Exception('Access token not in json response: {}'.format(repr(response_json)))
        return response_json['accessToken']

    @property
    def auth_headers(self):
        """
        Return authenticated headers (lazy authentication when required)

        :return: headers dict
        """
        if not self._token:
            self._token = self.authenticate()
        headers = {'Authorization': 'Bearer {}'.format(self._token)}
        headers.update(self.request_headers)
        return headers

    def download_zonefiles(self, dest_dir):
        """
        Download Zonefiles
        :param dest_dir: directory to save zonefiles to
        :return:
        """
        dest_dir = os.path.abspath(dest_dir)
        if not os.path.isdir:
            raise OSError('Invalid file path')
        links_url = self.czds_api_base + '/czds/downloads/links'
        zonefile_links = requests.get(links_url, headers=self.auth_headers).json()
        downloads = []
        for z in zonefile_links:
            # Create a filename based off the zonefile name (zonename.zone.gz)
            filename = z.split('/')[-1] + '.gz'
            with open(os.path.join(dest_dir, filename), 'wb') as fh:
                response = requests.get(z, headers=self.auth_headers, stream=True)
                response_len = 0
                for chunk in response.iter_content(chunk_size=1024):
                    response_len += len(chunk)
                    fh.write(chunk)
            downloads.append((filename, response_len))
        return downloads

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', '-u', dest='username', default=os.environ.get('ICANN_USER', None),
                        help='ICANN Username')
    parser.add_argument('--password', '-p', dest='password', default=os.environ.get('ICANN_PASS', None),
                        help='ICANN Password')
    parser.add_argument('--dest', '-d', dest='dest_dir', default=os.environ.get('DEST_DIR', '.'),
                        help='Destination directory')
    args = parser.parse_args()
    if not args.username:
        print('No credentials defined!')
        parser.print_help()
    try:
        print('Starting Zonefile Downloads')
        czds_client = CZDSClient(args.username, args.password)
        results = czds_client.download_zonefiles(args.dest_dir)
        print('Downloaded {} files'.format(len(results)))
    except AuthenticationError:
        print('Invalid Credentials, check user/password')
        parser.print_help()


if __name__ == '__main__':
    main()
