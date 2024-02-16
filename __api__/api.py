import requests
import logging
    
def getToken(token):
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token}")
    except:
        logging.error("Unable to send request to payment gateway")
    else:
        print(response.json())
        return response.json()