import time
import hmac
import hashlib
import requests
import urllib.parse

import config

accessSecret = '8a83845cf57bb044dbf5cde895dc69b7'
print(config.Whale_keySecret)
ACCESS_KEY = '83059bbabb2535b6d57a65e3b0616600'
url = 'https://be.whalefin.com'
method = 'GET'
timestamp = int(time.time() * 1000)
urlPath = '/api/v2/earn/products'
params = urllib.parse.urlencode(
    {
        "type": 'FIXED',
        'ccy': 'USD'

    }
)
path = f'{urlPath}?{params}'

signStr = f'method={method}&path={path}&timestamp={timestamp}'
# method=GET&path=/api/v2/asset/statement?page=1&size=3&createStartTime=2022-03-06T03%3A00%3A00.000Z&timestamp=1646816265520

signature = hmac.new(bytes(accessSecret, 'utf-8'), bytes(signStr, 'utf-8'), hashlib.sha256).hexdigest()
# 3b6da1674b0667556f99c28b675e0b2e881e7792f28cbdbfe9babd9aba32f02a

headers = {
    'access-key': ACCESS_KEY,
    'access-timestamp': str(timestamp),
    'access-sign': signature
}
# {'access-key': 'ACCESS_KEY', 'access-timestamp': '1646816265520', 'access-sign': '3b6da1674b0667556f99c28b675e0b2e881e7792f28cbdbfe9babd9aba32f02a'}

resp = requests.get(url + path, headers=headers)
r = resp.json()['result']['items']
for i in r:
    print(i)