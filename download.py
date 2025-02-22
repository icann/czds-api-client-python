import json
import sys
import os
import datetime
from email.message import Message  # Replaces deprecated cgi module
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
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
except Exception as e:
    sys.stderr.write(f"Error loading config.json file: {e}\n")
    exit(1)

# Extract configuration
username = config.get('icann.account.username')
password = config.get('icann.account.password')
authen_base_url = config.get('authentication.base.url')
czds_base_url = config.get('czds.base.url')
working_directory = config.get('working.directory', '.')

# Validate required fields
if not all([username, password, authen_base_url, czds_base_url]):
    sys.stderr.write("Missing required parameters in config.json\n")
    exit(1)

##############################################################################################################
# Second Step: authenticate the user to get an access_token.
##############################################################################################################

print(f"Authenticating user {username}")
access_token = authenticate(username, password, authen_base_url)

##############################################################################################################
# Third Step: Get the download zone file links
##############################################################################################################

def get_zone_links(czds_base_url):
    """Fetches the list of available zone file links."""
    global access_token
    links_url = f"{czds_base_url}/czds/downloads/links"
    
    response = do_get(links_url, access_token)
    
    if response.status_code == 200:
        zone_links = response.json()
        print(f"{datetime.datetime.now()}: Number of zone files to download: {len(zone_links)}")
        return zone_links
    elif response.status_code == 401:
        print("Access token expired. Re-authenticating...")
        access_token = authenticate(username, password, authen_base_url)
        return get_zone_links(czds_base_url)
    else:
        sys.stderr.write(f"Failed to fetch zone links ({response.status_code}): {response.text}\n")
        return None

zone_links = get_zone_links(czds_base_url)
if not zone_links:
    exit(1)

##############################################################################################################
# Fourth Step: download zone files
##############################################################################################################

def parse_filename(response):
    """Extracts filename from content-disposition header or generates a fallback name."""
    content_disposition = response.headers.get('content-disposition')
    if content_disposition:
        message = Message()
        message['content-disposition'] = content_disposition
        filename = message.get_param('filename')
        if filename:
            return filename
    return f"{response.url.rsplit('/', 1)[-1].split('.')[0]}.txt.gz"

def download_one_zone(url, output_directory):
    """Downloads a single zone file from the given URL."""
    global access_token
    print(f"{datetime.datetime.now()}: Downloading {url}")

    response = do_get(url, access_token)
    
    if response.status_code == 200:
        filename = parse_filename(response)
        file_path = os.path.join(output_directory, filename)
        
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        print(f"{datetime.datetime.now()}: Downloaded to {file_path}")

    elif response.status_code == 401:
        print("Access token expired. Re-authenticating...")
        access_token = authenticate(username, password, authen_base_url)
        download_one_zone(url, output_directory)

    elif response.status_code == 404:
        print(f"No zone file found for {url}")

    else:
        sys.stderr.write(f"Failed to download {url} (Error {response.status_code})\n")

def download_zone_files(urls, working_directory):
    """Downloads all zone files into a sub-directory."""
    output_directory = os.path.join(working_directory, "zonefiles")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for link in urls:
        download_one_zone(link, output_directory)

start_time = datetime.datetime.now()
download_zone_files(zone_links, working_directory)
end_time = datetime.datetime.now()

print(f"{end_time}: Completed downloading all zone files. Time taken: {end_time - start_time}")
