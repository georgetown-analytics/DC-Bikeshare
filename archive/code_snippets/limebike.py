
import requests



LIMEBIKE_URL = 'https://lime.bike/api/partners/v1/bikes'
LIMEBIKE_HEADERS = {'Authorization': 'Bearer limebike-PMc3qGEtAAXqJa'}
LIMEBIKE_PARAMS = {'region': 'Washington DC Proper'}


def limebike_proxy():
    resp = requests.get(
        LIMEBIKE_URL,
        headers=LIMEBIKE_HEADERS,
        params=LIMEBIKE_PARAMS,
    )
    return resp.json()

limebike_resp = limebike_proxy()

print(len(limebike_resp['data']))

# Limebike has 410 bikes as of 2/11/2018
