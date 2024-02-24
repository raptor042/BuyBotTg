import requests
import logging

def getTokenVolume(token):
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token}")
    except Exception as e:
        logging.error(f"An error occured while fetching token data, {e}")
    else:
        data = response.json()
        print(data)

        return data["pairs"][0]["volume"]["h24"]