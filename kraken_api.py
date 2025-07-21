import time
import requests
import hashlib
import hmac
import base64
from urllib.parse import urlencode
import logging

from config import KRAKEN_API_KEY, KRAKEN_API_SECRET

print("Loaded key:", KRAKEN_API_KEY[:5] + "..." + KRAKEN_API_KEY[-5:])

API_URL = "https://api.kraken.com"
API_VERSION = "0"

def generate_signature(urlpath, data, secret):
    """
    Generates the HMAC signature required by Kraken's private endpoints.
    """
    nonce = str(int(time.time() * 1000))
    data['nonce'] = nonce
    postdata = urlencode(data)
    message = urlpath.encode('utf-8') + hashlib.sha256((nonce + postdata).encode('utf-8')).digest()
    signature = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(signature.digest()).decode()

def kraken_request(uri_path, data=None):
    urlpath = f"/{API_VERSION}/{uri_path}"  # ✅ Fix: include the leading slash
    url = f"{API_URL}{urlpath}"             # ✅ Full URL

    headers = {}
    data = data or {}

    # ✅ Correct signature with full path
    signature = generate_signature(urlpath, data, KRAKEN_API_SECRET)
    headers['API-Key'] = KRAKEN_API_KEY
    headers['API-Sign'] = signature

    response = requests.post(url, headers=headers, data=data)
    result = response.json()

    if 'error' in result and result['error']:
        logging.warning(f"🚫 API Error: {result['error']}")

    return result


def get_balance():
    """
    Fetches balance from Kraken API and returns the result.
    """
    balance = kraken_request("private/Balance")
    if 'error' in balance and balance['error']:
        logging.error(f"API Error in get_balance: {balance['error']}")
        return None  # Return None if there's an error
    return balance

def get_usd_balance():
    """
    Retrieves USD balance from Kraken and handles error gracefully.
    """
    balance = get_balance()
    if balance is None:
        logging.error("Failed to get balance due to an API error.")
        return 0.0  # Return 0 if there's an error with balance retrieval

    try:
        usd_balance = balance['result'].get('USD.F', '0')  # Get the USD balance from the result
        if usd_balance == '0':
            logging.warning("USD balance is zero or not found.")
        return float(usd_balance)
    except Exception as e:
        logging.error(f"Error parsing USD.F balance: {e}")
        return 0.0

def get_price(pair):
    """
    Fetches price for a given coin pair from Kraken public API.
    """
    url = f"{API_URL}/{API_VERSION}/public/Ticker?pair={pair}"
    response = requests.get(url)
    data = response.json()
    
    if 'error' in data and data['error']:
        logging.error(f"Ticker error for {pair}: {data['error']}")
        return 0.0
    
    return float(data['result'][pair]['c'][0])

def place_market_order(pair, volume, side="buy"):
    """
    Places a market order for a given pair.
    """
    uri_path = "private/AddOrder"
    data = {
        "pair": pair,
        "type": side,
        "ordertype": "market",
        "volume": volume
    }
    return kraken_request(uri_path, data)

