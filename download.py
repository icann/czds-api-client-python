import boto3
import cgi
import datetime
import json
import os
import sys
import traceback

from do_authentication import authenticate
from do_http_get import do_get

aws_session_args = {}


##############################################################################################################
# First Step: Get the config data from config.json file
##############################################################################################################

try:
    # In case we run the script from somewhere outside our working directory...
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_file = open(base_path + "/config.json", "r")
    config = json.load(config_file)
    config_file.close()

except:
    sys.stderr.write("Error loading config.json file.\n")
    exit(1)

# Front load some of the AWS creds values
aws_profile           = None
aws_access_key_id     = None
aws_secret_access_key = None

# The config.json file must contain the following data:
username                 = config['icann.account.username']
password                 = config['icann.account.password']
authentication_base_url  = config['authentication.base.url']
czds_base_url            = config['czds.base.url']
aws_region               = config['aws.region']
aws_cloudwatch_namespace = config['aws.cloudwatch.namespace']

# The config.json can contain the following data:
aws_profile           = config['aws.iam.profile']
aws_access_key_id     = config['aws.iam.access_key_id']
aws_secret_access_key = config['aws.iam.secret_access_key']

# This is optional. Default to current directory
working_directory = config['working.directory']

if not username:
    sys.stderr.write("'icann.account.username' parameter not found in the config.json file\n")
    exit(1)

if not password:
    sys.stderr.write("'icann.account.password' parameter not found in the config.json file\n")
    exit(1)

if not authentication_base_url:
    sys.stderr.write("'authentication.base.url' parameter not found in the config.json file\n")
    exit(1)

if not czds_base_url:
    sys.stderr.write("'czds.base.url' parameter not found in the config.json file\n")
    exit(1)

if not aws_region:
    sys.stderr.write("'aws.aws_region' parameter not found in the config.json file\n")
    exit(1)

if not aws_cloudwatch_namespace:
    sys.stderr.write("'aws.cloudwatch.namespace' parameter not found in the config.json file\n")
    exit(1)

if not working_directory:
    # Default to current directory
    working_directory = '.'

if (aws_access_key_id == None) ^ (aws_secret_access_key == None):
    sys.stderr.write("'aws.iam.aws_access_key_id' and 'aws.iam.aws_secret_access_key' parameters must both be used together in config.json file\n")
    exit(1)


# Actually set up AWs creds if we're using keys or a profile. Otherwise we'll just
# hope we're running on a host/container with an instance profile.
if aws_access_key_id != None:
    aws_session.update({
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key
    })

if aws_profile != None:
    aws_session.update({'profile_name': aws_profile})


##############################################################################################################
# Second Step: authenticate the user to get an access_token.
# Note that the access_token is global for all the REST API calls afterwards
##############################################################################################################

print("Authenticate user {0}".format(username))
access_token = authenticate(username, password, authentication_base_url)


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
        access_token = authenticate(username, password, authentication_base_url)
        get_zone_links(czds_base_url)
    else:
        sys.stderr.write("Failed to get zone links from {0} with error code {1}\n".format(links_url, status_code))
        return None


# Get the zone links
zone_links = get_zone_links(czds_base_url)
if not zone_links:
    exit(1)


##############################################################################################################
# Fourth Step: Set up AWS integration
##############################################################################################################

boto3.setup_default_session(**aws_session_args)
aws_cloudwatch = boto3.client('cloudwatch', region_name=aws_region)


##############################################################################################################
# Fifth Step: download zone files
##############################################################################################################

# Function definition to download one zone file
def download_one_zone(url, output_directory):
    print("{0}: Downloading zone file from {1}".format(str(datetime.datetime.now()), url))

    global  access_token

    try:
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
            access_token = authenticate(username, password, authentication_base_url)
            download_one_zone(url, output_directory)
        elif status_code == 404:
            print("No zone file found for {0}".format(url))
        else:
            sys.stderr.write('Failed to download zone from {0} with code {1}\n'.format(url, status_code))

        # Make sure we throw an exception we can catch back down the line.
        if status_code >= 400:
            raise RuntimeError("Download failed.")

    except:
        # Don't just die here. We need to know that we failed.
        raise

# Function definition for downloading all the zone files
def download_zone_files(urls, working_directory):

    # Set up a list to store our CloudWatch metrics.
    cloudwatch_metrics = []

    # The zone files will be saved in a sub-directory
    output_directory = working_directory + "/zonefiles"

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Download the zone files one by one
    for link in urls:
        # Start with success.
        cloudwatch_metric_value = 1

        try:
            # Taken from above download_one_zone().
            filename = link.rsplit('/', 1)[-1].rsplit('.')[-2]

            # This is where the zone file will be saved
            download_one_zone(link, output_directory)

        except:
            # Failure happened.
            cloudwatch_metric_value = 0
            print("Exception downloading file:\n %s" %traceback.format_exc())

        finally:
            # Add the results to our list of results.
            cloudwatch_metrics.append({
                "MetricName": 'status',
                "Value": cloudwatch_metric_value,
                "Dimensions": [
                    {
                        "Name": "File",
                        "Value": filename
                    },
                    {
                        "Name": "Source",
                        "Value": "ICANN"
                    }
                ],
                "Timestamp": datetime.datetime.utcnow()
            })

    # Put all our metrics in one shot.
    aws_cloudwatch.put_metric_data(Namespace=aws_cloudwatch_namespace, MetricData=cloudwatch_metrics)


# Finally, download all zone files
start_time = datetime.datetime.now()
download_zone_files(zone_links, working_directory)
end_time = datetime.datetime.now()

print("{0}: DONE DONE. Completed downloading all zone files. Time spent: {1}".format(str(end_time), (end_time-start_time)))
