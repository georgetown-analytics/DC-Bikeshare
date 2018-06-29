import os

import requests
import sys

OFO_URL = 'http://ofo-global.open.ofo.com/api/bike'
OFO_DATA = {
    'token': 'c902b87e3ce8f9f95f73fe7ee14e81fe',
    'name': 'Washington',
    'lat': 38.894432,
    'lng': -77.013655,
}


resp = requests.post(
    OFO_URL,
    data=OFO_DATA,
)

print(len(resp.json()['values']['cars']))

#333 available OFOs as of 2/18/2018
