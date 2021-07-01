import json
import sys
import cgi
import os
import datetime

from do_authentication import authenticate
from do_http_get import do_get

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

# This is optional. Default to current directory
working_directory = config.get('working.directory', '.') # Default to current directory

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

print("Authenticate user {0}".format(username))
access_token = authenticate(username, password, authen_base_url)



##############################################################################################################
# Third Step: Get the download zone file links
##############################################################################################################

# Function definition for listing the zone links
def get_zone_links(czds_base_url):
    global  access_token

    links_url = czds_base_url + "/czds/downloads/links"
    links_response = do_get(links_url, access_token)

    status_code = links_response.status_code

    if status_code == 200:
        zone_links = links_response.json()
        print("{0}: The number of zone files to be downloaded is {1}".format(datetime.datetime.now(),len(zone_links)))
        return zone_links
    elif status_code == 401:
        print("The access_token has been expired. Re-authenticate user {0}".format(username))
        access_token = authenticate(username, password, authen_base_url)
        get_zone_links(czds_base_url)
    else:
        sys.stderr.write("Failed to get zone links from {0} with error code {1}\n".format(links_url, status_code))
        return None


# Get the zone links
zone_links = get_zone_links(czds_base_url)
if not zone_links:
    exit(1)

# We may not want to download all the zone files, for a poor connection this will take a long time.
# So, enable the user to specify which files to download at the command line. They just need to add
# the TLD of all those that they wish to download, i.e. `python3 download.py net com org` to download
# the .net, .com, and .org zone files. The zone files downloaded will be a subset of those available
# and those specified.

# Zones to download are those passed by name
zones_to_download = sys.argv[1:]

if any([zone == "*" for zone in zones_to_download]):
    # If any are a *, then just download all
    pass
else:
    # Append .zone to each to make it easier to search
    zones_to_download = [f"{zone.lower()}.zone" for zone in zones_to_download]
    zone_links = [zone for zone in zone_links if any([zone.endswith(z) for z in zones_to_download])]
    if len(zone_links) != len(zones_to_download):
        # We get here if either we don't have permission to download zones we wanted, or they don't exist
        not_found = [zone for zone in zones_to_download if not any([z.endswith(zone) for z in zone_links])]
        print(zone_links, zones_to_download)
        print("The following zones could not be downloaded because they either do not exist or you do not have permission:\n\t{0}".format('\n\t'.join(not_found)))

##############################################################################################################
# Fourth Step: download zone files
##############################################################################################################

# Function definition to download one zone file
def download_one_zone(url, output_directory):
    print("{0}: Downloading zone file from {1}".format(str(datetime.datetime.now()), url))

    global  access_token
    download_zone_response = do_get(url, access_token)

    status_code = download_zone_response.status_code

    if status_code == 200:
        # Try to get the filename from the header
        _,option = cgi.parse_header(download_zone_response.headers['content-disposition'])
        filename = option.get('filename')

        # If could get a filename from the header, then makeup one like [tld].txt.gz
        if not filename:
            filename = url.rsplit('/', 1)[-1].rsplit('.')[-2] + '.txt.gz'

        # This is where the zone file will be saved
        path = '{0}/{1}'.format(output_directory, filename)

        with open(path, 'wb') as f:
            for chunk in download_zone_response.iter_content(1024):
                f.write(chunk)

        print("{0}: Completed downloading zone to file {1}".format(str(datetime.datetime.now()), path))

    elif status_code == 401:
        print("The access_token has been expired. Re-authenticate user {0}".format(username))
        access_token = authenticate(username, password, authen_base_url)
        download_one_zone(url, output_directory)
    elif status_code == 404:
        print("No zone file found for {0}".format(url))
    else:
        sys.stderr.write('Failed to download zone from {0} with code {1}\n'.format(url, status_code))

# Function definition for downloading all the zone files
def download_zone_files(urls, working_directory):

    # The zone files will be saved in a sub-directory
    output_directory = working_directory + "/zonefiles"

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Download the zone files one by one
    for link in urls:
        download_one_zone(link, output_directory)

# Finally, download all zone files
start_time = datetime.datetime.now()
download_zone_files(zone_links, working_directory)
end_time = datetime.datetime.now()

print("{0}: DONE DONE. Completed downloading all zone files. Time spent: {1}".format(str(end_time), (end_time-start_time)))
