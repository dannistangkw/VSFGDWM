import requests
import json
import config
import pandas as pd
from openpyxl import Workbook
import telepot
from datetime import date

wb = Workbook()
sheet = wb.active
today = date.today()
# its bad practice to place your bearer token directly into the script (this is just done for illustration purposes)
BEARER_TOKEN = config.twitter_bearer_token

# ##########telegram
token = config.telegram_token
receiverID = config.receiver_token
bot = telepot.Bot(token)
# bot.sendMessage(receiverID, f'{News_result}')
# bot.sendDocument(receiverID, document=open(f'Tweets/{file_name}'))

# define search twitter function
def search_twitter(query, tweet_fields, bearer_token=BEARER_TOKEN):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}

    url = "https://api.twitter.com/2/tweets/search/recent?query={}&{}".format(
        query, tweet_fields
    )
    response = requests.request("GET", url, headers=headers)

    # print(response.status_code)

    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


# search term
keys = [i.upper() for i in pd.read_csv('Keywords.csv', header=0)['Keys']]
News_result = []
i = 1
##link https://twitter.com/TwitterDev/status/1228393702244134912
for key in keys:
    query = key
    # twitter fields to be returned by api call
    tweet_fields = "tweet.fields=text,author_id,created_at,geo"

    # twitter api call
    json_response = search_twitter(query=query, tweet_fields=tweet_fields, bearer_token=BEARER_TOKEN)
    # pretty printing
    # print(json.dumps(json_response, indent=4, sort_keys=True))
    # print(json_response)
    for data in json_response['data']:
        # news = f"{query} https://twitter.com/TwitterDev/status/{data['id']}: {data['text']}"
        url = f"https://twitter.com/TwitterDev/status/{data['id']}"
        text = f"{query}: {data['text']}"

        print(f"{i}. {text}")
        # print('------------------------')
        # News_result.append(news)

        # Add a hyperlink
        sheet.cell(row=i, column=1).value = '=HYPERLINK("{}", "{}")'.format(url, text)

        i += 1
wb.save(f"Tweets/Tweets_{today}.xlsx")

# # print(News_result)
# new_df = pd.DataFrame(columns=['Key', 'Content'], data=News_result)
# print(new_df)
# file_name = f'Tweets_{today}.csv'
# new_df.to_csv(f'Tweets/{file_name}', index=False)
# bot.sendDocument(receiverID, document=open(f'Tweets/{file_name}', encoding="utf8"))

