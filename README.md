CZDS API Client in Python
===========

This repository provides a Python example of how to download zone files via CZDS (Centralized Zone Data Service) REST API. 
A detail API Specs can be found [here.](https://github.com/icann/czds-api-client-java/tree/master/docs)

There is also an example provided in Java. It can be found in [this repo.](https://github.com/icann/czds-api-client-java)

Installation
------------

This script requires Python 3. It has been tested with Python 3.7.1. 

It requires the `requests` extension library. Please checkout here to see how to install it - https://github.com/requests/requests

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