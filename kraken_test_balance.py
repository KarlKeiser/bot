import time
import hmac
import hashlib
import requests
import base64
from urllib.parse import urlencode
from kraken_api import get_price
from config import TICKER_MAP


API_KEY = "DjFm9DbHlSB7Aq4+wt/bv3JFemGVMCWOuCW7C4t3JFPrcSEGF6NQ7VRP"
API_SECRET = "G2PRyLxRxuNJjwIY1AHb2jt0nSXEHiGWqI7Dl3qWmoELU9BBLNydnAWv5T+WdhBe0ibJuJokAXeoJZjATMPVkA=="

url = "https://api.kraken.com/0/private/Balance"
urlpath = "/0/private/Balance"

def generate_signature(urlpath, data, secret):
    nonce = str(int(time.time() * 1000))
    data['nonce'] = nonce
    postdata = urlencode(data)
    message = urlpath.encode('utf-8') + hashlib.sha256((nonce + postdata).encode('utf-8')).digest()
    signature = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(signature.digest()).decode()


print("🔍 Testing all coin pairs from TICKER_MAP...\n")

for coin, pair in TICKER_MAP.items():
    price = get_price(pair)
    if price == 0.0:
        print(f"❌ {coin} ({pair}) - Invalid or unsupported on Kraken")
    else:
        print(f"✅ {coin} ({pair}) - Valid | Current price: ${price:.4f}")

pair = "PEPEUSD"
price = get_price(pair)

if price == 0.0:
    print(f"❌ {pair} is likely invalid or unsupported on Kraken.")
else:
    print(f"✅ {pair} is valid. Current price: ${price}")

def fetch_balance():
    try:
        data = {}
        signature = generate_signature(urlpath, data, API_SECRET)
        headers = {
            "API-Key": API_KEY,
            "API-Sign": signature
        }
        response = requests.post(url, headers=headers, data=data)
        result = response.json()

        if result['error']:
            print(f"🚫 API Error: {result['error']}")
        else:
            usd_balance = result['result'].get('USD.F', '0.0')
            print(f"✅ USD.F Balance: ${usd_balance}")
    except Exception as e:
        print(f"Error: {str(e)}")

fetch_balance()


