CZDS API Client in Python
===========

This repository provides a Python example of how to download zone files via CZDS (Centralized Zone Data Service) REST API.
A detail API Specs can be found [here.](https://github.com/icann/czds-api-client-java/tree/master/docs)

It has been modified to post CloudWatch metrics for each zone file successfully downloaded.

Installation
------------

According to ICANN this script requires Python 3, but it works fine with Python 2.7. It has been tested with Python 3.7.1 and 2.7.12.

It requires:
* The `requests` extension library. It can be installed using `pip install requests`.
* The `boto3` library. This can be installed using `pip install boto3`.

AWS authentication
------------------

This utility supports authenticating with AWS in the following ways:
* AWS instance profiles
* AWS profiles defined in ~/.aws/credentials
* AWS IAM keys

AWS authentication parameters are configured in `config.json`. In order to use an instance profile ensure that `aws.iam.profile`, `aws.iam.access_key_id`, and `aws.iam.secret_access_key` are set to `null`. If you want to specify an instance profile just set `aws.iam.profile` to the name of the desired AWS profile you want to use. `aws.iam.access_key_id` and `aws.iam.secret_access_key` should be set to `null` and will be ignored in favor of the AWS authentication profile if specified. In order to use AWS access keys `aws.iam.profile` should be set to `null`.

CloudWatch metrics
------------------

In order to track zone file download success this utility leverages CloudWatch metrics. Each zone file download attempt will generate a CloudWatch metric for the attempt. The CloudWatch namespace and region these metrics are stored with is configured `config.json` as `aws.coudwatch.namespace` and `aws.region` respectively. The dimensions for each zone file are as follows:
* File: The name of the zone being downloaded.
* Source: Statically set to `ICANN`.

Breakdown of the `status` metric:
* The absence of a `status` metric indicates the script didn't properly run or hasn't been executed.
* A `status` metric of `0` indicates that there was an error during the download of the zone file.
* A `status` metric of `1` indicates that the zone file downloaded successfully.

Run
---------------------

1. Copy the configuration file template to `config.json` by running `cp config.json{.dist,}`.
2. Edit `config.json` and fill in your information.
2. Run `python download.py`

All the zone files will be saved in `working-directory`/zonefiles, `working-directory` is specified in `config.json`,
or default to current directory if not specified in `config.json`

Documentation
-------------

* CZDS REST API Specs - https://github.com/icann/czds-api-client-java/blob/master/docs/ICANN_CZDS_api.pdf

Contributing
------------

Contributions are welcome.

Other
-----

Reference Implementation in Java: https://github.com/icann/czds-api-client-java
