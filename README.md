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

Run
---------------------

1. Make a copy of the `config.sample.json` file and name it `config.json`
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
