import requests

JUMP_URL = 'https://dc.jumpmobility.com/opendata/free_bike_status.json'


def jump_proxy():
    resp = requests.get(JUMP_URL)
    return resp.json()


jump_resp = jump_proxy()
print(len(jump_resp['data']['bikes']))

# 42 available bikes as of 4:16pm on 2/11/28, does not represent total number
