import requests


SPIN_URL = 'https://web.spin.pm/api/gbfs/v1/free_bike_status'


def spin_proxy():
    resp = requests.get(SPIN_URL)
    return resp.json()


spin_resp = spin_proxy()
print(len(spin_resp['data']['bikes']))

# Spin has 136 bikes as of 2/11/2018
