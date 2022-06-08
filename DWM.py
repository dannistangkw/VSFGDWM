import hashlib
import hmac
import json
import time
from urllib.parse import urljoin, urlencode
import requests
import config
import telepot
import datetime
import urllib.parse
import pandas as pd


#########Keys & URL########################################
Binance_API_KEY = config.Binance_keyPrivate
Binance_SECRET_KEY = config.Binance_keySecret
WhaleFin_API_Key = config.Whale_keyPrivate
WhaleFin_SECRET_KEY = config.Whale_keySecret
Binance_BASE_URL = 'https://api.binance.com'
Binance_PATH = '/sapi/v1/lending/project/list'
WhaleFin_BASE_URL = 'https://be.whalefin.com'
WhaleFin_PATH = '/api/v2/earn/products'
timestamp = int(time.time() * 1000)
Col = ['Platform', 'Currency', 'Tenor', 'APR', 'Min_Subscribe', 'Max_Subscribe']

# #Datetime -> HK_time
datetime = datetime.datetime.fromtimestamp(int(timestamp) / 1000)  # using the local timezone
Today_date = datetime.strftime("%Y-%m-%d")



###headers##############################################
Binance_headers = {
    'X-MBX-APIKEY': Binance_API_KEY
}

#############Binance###########################################################################################################################################################################################################
class BinanceException(Exception):
    def __init__(self, status_code, data):

        self.status_code = status_code
        if data:
            self.code = data['code']
            self.msg = data['msg']
        else:
            self.code = None
            self.msg = None
        message = f"{status_code} [{self.code}] {self.msg}"
        super().__init__(message)

def get_api_data():
    timestamp = int(time.time() * 1000)
    Result_list = []
    #####params
    Binance_params = {
        'timestamp': timestamp,
        'type': 'CUSTOMIZED_FIXED',
        'size': 100
    }


    query_string = urlencode(Binance_params)
    Binance_params['signature'] = hmac.new(Binance_SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    Binance_url = urljoin(Binance_BASE_URL, Binance_PATH)
    Binance_r = requests.get(Binance_url, headers=Binance_headers, params=Binance_params)
    if Binance_r.status_code == 200:
        Binance_res = Binance_r.json()
        output = json.dumps(Binance_res, indent=2)
        for Binance_data in Binance_res:
            Binance_result = ['Binance']
            if 'US' in Binance_data['asset']:
                Binance_result.append(Binance_data['asset'])
                Binance_result.append(Binance_data['duration'])
                Binance_result.append("{:.2%}".format(float(Binance_data['interestRate'])))
                Binance_result.append(int(Binance_data['lotSize']))
                Binance_result.append(f"{int(Binance_data['lotsUpLimit'])*int(Binance_data['lotSize'])/1000000}M")
                Result_list.append(Binance_result)
    else:
        raise BinanceException(status_code=Binance_r.status_code, data=Binance_r.json())


    #############WhaleFin###########################################################################################################################################################################################################


    method = 'GET'
    timestamp = int(time.time() * 1000)

    params = urllib.parse.urlencode(
        {
            "type": 'FIXED',
            'ccy': 'USD'

        }
    )
    path = f'{WhaleFin_PATH}?{params}'

    signStr = f'method={method}&path={path}&timestamp={timestamp}'
    # method=GET&path=/api/v2/asset/statement?page=1&size=3&createStartTime=2022-03-06T03%3A00%3A00.000Z&timestamp=1646816265520

    signature = hmac.new(bytes(WhaleFin_SECRET_KEY, 'utf-8'), bytes(signStr, 'utf-8'), hashlib.sha256).hexdigest()


    headers = {
        'access-key': WhaleFin_API_Key,
        'access-timestamp': str(timestamp),
        'access-sign': signature
    }

    resp = requests.get(WhaleFin_BASE_URL + path, headers=headers)

    if resp.status_code == 200:
        Whale_r = resp.json()['result']['items']
        for Whale_data in Whale_r:
            # print(Whale_data)
            Whale_result = ['WhaleFin', 'USDS']
            Whale_result.append(Whale_data['tenor'])
            Whale_result.append("{:.2%}".format(float(Whale_data['originalApr'])))
            Whale_result.append(int(float(Whale_data['minSubscribeAmount'])))
            if Whale_data['maxIndividualSubscribeAmount'] is not None:
                Whale_result.append(f"{int(Whale_data['maxIndividualSubscribeAmount'])/1000000}M")
            else: Whale_data['maxIndividualSubscribeAmount']

            Result_list.append(Whale_result)
    else:
        print(f'{resp.status_code}, WhaleFin API Call Failed')

    return Result_list



###########run#####################################################
def run():
    ##########dataframe##############################################
    Result_list = get_api_data()
    df = pd.DataFrame(columns=Col, data=Result_list)
    file_name = f'Stablecoin_Yield_Overview_{Today_date}.csv'
    df.to_csv(f'files/{file_name}')


    ###########telegram
    token = config.telegram_token
    receiverID = config.receiver_token

    bot = telepot.Bot(token)
    bot.sendMessage(receiverID, f'{df}')
    bot.sendDocument(receiverID, document=open(f'files/{file_name}'))
