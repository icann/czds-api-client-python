import json
import sys
import os
import datetime

from do_authentication import authenticate
from do_request import do_post

##############################################################################################################
# First Step: Get the config data from config.json file
##############################################################################################################

try:
    if 'CZDS_CONFIG' in os.environ:
        config_data = os.environ['CZDS_CONFIG']
        config = json.loads(config_data)
    else:
        config_file = open("config.json", "r")
        config = json.load(config_file)
        config_file.close()
except:
    sys.stderr.write("Error loading config.json file.\n")
    exit(1)

# The config.json file must contain the following data:
username = config['icann.account.username']
password = config['icann.account.password']
authen_base_url = config['authentication.base.url']
czds_base_url = config['czds.base.url']
access_token = config['czds.bearer.token']

# This is optional. Default to current directory
working_directory = config.get('working.directory', '.')  # Default to current directory

if not username:
    sys.stderr.write("'icann.account.username' parameter not found in the config.json file\n")
    exit(1)

if not password:
    sys.stderr.write("'icann.account.password' parameter not found in the config.json file\n")
    exit(1)

if not authen_base_url:
    sys.stderr.write("'authentication.base.url' parameter not found in the config.json file\n")
    exit(1)

if not czds_base_url:
    sys.stderr.write("'czds.base.url' parameter not found in the config.json file\n")
    exit(1)


##############################################################################################################
# Second Step: authenticate the user to get an access_token.
# Note that the access_token is global for all the REST API calls afterwards
##############################################################################################################

if access_token:
    print("Authenticate user {0}".format(username))
    access_token = authenticate(username, password, authen_base_url)


##############################################################################################################
# Third Step: Get the list of expiring zones
##############################################################################################################
def get_zone_ids(czds_base_url):
    global access_token

    links_url = czds_base_url + "/czds/requests/all"
    pagination = {"size": 1200, "page": 0}
    sort = {"field": "expired", "direction": "asc"}
    data = {"status": "Approved", "filter": None, "pagination": pagination, "sort": sort}
    links_response = do_post(links_url, access_token, data)

    status_code = links_response.status_code

    if status_code == 200:
        zone_details = links_response.json()
        zone_ids = []
        current_date = datetime.datetime.today()
        for zone in zone_details["requests"]:
            expired = datetime.datetime.strptime(zone["expired"], '%Y-%m-%dT%H:%M:%SZ')
            if abs(expired-current_date).days < 30:
                zone_ids.append(zone["requestId"])
        print("{0}: The number of zone files to request expiry extension is {1}".format(datetime.datetime.now(), len(zone_ids)))
        return zone_ids
    elif status_code == 401:
        print("The access_token has been expired. Re-authenticate user {0}".format(username))
        access_token = authenticate(username, password, authen_base_url)
        get_zone_ids(czds_base_url)
    else:
        sys.stderr.write("Failed to get zone ids from {0} with error code {1}\n".format(links_url, status_code))
        return None


# Get the zone links
zone_ids = get_zone_ids(czds_base_url)
if not zone_ids:
    exit(1)


##############################################################################################################
# Fourth Step: Request extensions on zone file expiry
##############################################################################################################
def request_extension(zone_ids):
    global access_token

    for zone_id in zone_ids:
        links_url = czds_base_url + f"/czds/requests/extension/{zone_id}"
        links_response = do_post(links_url, access_token)

        status_code = links_response.status_code

        if status_code == 200:
            zone_ids.remove(zone_id)  # don't request again if got 401 while running this
            print("Request for extension successful.")
        elif status_code == 401:
            print("The access_token has been expired. Re-authenticate user {0}".format(username))
            access_token = authenticate(username, password, authen_base_url)
            request_extension(zone_ids)
        else:
            sys.stderr.write('Failed to request extension from {0} with code {1}\n'.format(links_url, status_code))


# Finally, request extension for all zone files
start_time = datetime.datetime.now()
request_extension(zone_ids)
end_time = datetime.datetime.now()

print("{0}: DONE DONE. Completed requesting extension for all expiring zone files. Time spent: {1}".format(str(end_time), (end_time-start_time)))
