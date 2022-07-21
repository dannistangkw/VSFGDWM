import requests
import json
import config
import pandas as pd

# its bad practice to place your bearer token directly into the script (this is just done for illustration purposes)
BEARER_TOKEN = config.twitter_bearer_token


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

##link https://twitter.com/TwitterDev/status/1228393702244134912
for key in keys:
    query = key
    # twitter fields to be returned by api call
    tweet_fields = "tweet.fields=text,author_id,created_at,geo"

    # twitter api call
    json_response = search_twitter(query=query, tweet_fields=tweet_fields, bearer_token=BEARER_TOKEN)
    # pretty printing
    print(json.dumps(json_response, indent=4, sort_keys=True))
    # print(json_response)
    # for data in json_response['data']:
    #     print(f"{query}: {data['text']}")
    #     print('------------------------')

