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
Gemini_PATH = 'https://api.gemini.com/v1/earn/rates'
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
    len_reslut_list = 0
    #####params
    Binance_params = {
        'timestamp': timestamp,
        'type': 'CUSTOMIZED_FIXED',
        'size': 100
    }

    query_string = urlencode(Binance_params)
    Binance_params['signature'] = hmac.new(Binance_SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'),
                                           hashlib.sha256).hexdigest()

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
                Binance_result.append(f"{int(Binance_data['lotsUpLimit']) * int(Binance_data['lotSize']) / 1000000}M")
                len_reslut_list = len(Binance_result)
                Result_list.append(Binance_result)
    else:
        raise BinanceException(status_code=Binance_r.status_code, data=Binance_r.json())

    # space = [''] * len_reslut_list
    # Result_list.append(space)

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
            Whale_result = ['WhaleFin', 'USDC']
            Whale_result.append(Whale_data['tenor'])
            Whale_result.append("{:.2%}".format(float(Whale_data['originalApr'])))
            Whale_result.append(int(float(Whale_data['minSubscribeAmount'])))
            if Whale_data['maxIndividualSubscribeAmount'] is not None:
                Whale_result.append(f"{int(Whale_data['maxIndividualSubscribeAmount']) / 1000000}M")
            else:
                Whale_result.append('NA')

            Result_list.append(Whale_result)
    else:
        print(f'{resp.status_code}, WhaleFin API Call Failed')
    ####Gemini###########################################################################

    Gem_result = []
    gemini_resp = requests.get(Gemini_PATH)
    Gem_data = pd.read_json(Gemini_PATH)
    Gem_df = pd.DataFrame(Gem_data)
    index_list = list(Gem_df.index.values)
    Gem_stablecoin_list = [i for i in index_list if 'USD' in i]
    if len(Gem_stablecoin_list) > 0:
        for coin in Gem_stablecoin_list:
            Gem_earn_product_detail = gemini_resp.json()["5fecd3fd-b705-4242-8880-00be626642b4"][coin]
            gem_subresult = ['Gemini',
                             coin,
                             1,
                             "{:.2%}".format(float(Gem_earn_product_detail['apyPct']) / 100),
                             1,
                             str(Gem_earn_product_detail['depositUsdLimit'] / 1000000) + "M"
                             ]

            Gem_result.append(gem_subresult)

    else:
        print(f'{gemini_resp.status_code}, Gemini API Call Failed')

    Result_list += Gem_result

    return Result_list


###########run#####################################################
def run():
    ##########dataframe##############################################
    Result_list = get_api_data()
    df = pd.DataFrame(columns=Col, data=Result_list)


    #####data formating#######################################################################
    New_output = []
    ##product name#########################################

    tenor_list = list(filter(None, set(df['Tenor'].tolist())))
    tenor_list.sort()
    platform_list = list(filter(None, set(df['Platform'].tolist())))
    currency_list = list(filter(None, set(df['Currency'].tolist())))

    ##find product details
    if len(platform_list) > 0:
        new_col = ['Product', 'Tenor']
        new_col = new_col + platform_list

        for product in currency_list:
            for tenor in tenor_list:
                new_result = [product, int(tenor)]
                empty_result = 0

                for exchange in platform_list:
                    select_data = df.loc[
                        (df['Platform'] == exchange) &
                        (df['Tenor'] == tenor) &
                        (df['Currency'] == product)
                        ]
                    try:
                        # new_result.append(select_data['APR'][0])
                        new_result.append(select_data['APR'].item())

                    except:
                        new_result.append(None)
                        empty_result += 1
                if empty_result < len(platform_list):
                    New_output.append(new_result)

    else:
        print(f'No platform found from APIs')

    new_df = pd.DataFrame(columns=new_col, data=New_output).sort_values(by=['Tenor'])
    file_name = f'Stablecoin_Yield_Overview_{Today_date}.csv'
    new_df.to_csv(f'files/{file_name}', index=False)

    ##########telegram
    token = config.telegram_token
    receiverID = config.receiver_token

    bot = telepot.Bot(token)
    bot.sendMessage(receiverID, f'{new_df}')
    bot.sendDocument(receiverID, document=open(f'files/{file_name}'))
