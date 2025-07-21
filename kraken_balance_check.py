import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from config import KRAKEN_API_KEY, KRAKEN_API_SECRET

url = "https://api.kraken.com/0/private/Balance"
urlpath = "/0/private/Balance"


def generate_signature(urlpath, data, secret):
    nonce = str(int(time.time() * 1000))
    data['nonce'] = nonce
    postdata = urlencode(data)
    message = urlpath.encode('utf-8') + hashlib.sha256(nonce.encode('utf-8') + postdata.encode('utf-8')).digest()
    signature = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(signature.digest())

def fetch_balance():
    try:
        data = {}
        urlpath = "/0/private/Balance"
        signature = generate_signature(urlpath, data, KRAKEN_API_SECRET)
        headers = {
            "API-Key": KRAKEN_API_KEY,
            "API-Sign": signature.decode()
        }
        response = requests.post(url, headers=headers, data=data)
        response_data = response.json()

        if response_data["error"]:
            print(f"❌ API Error: {response_data['error']}")
            return None

        usd_balance = response_data['result'].get('ZUSD', '0')
        return float(usd_balance)

    except Exception as e:
        print(f"⚠️ Error fetching balance: {str(e)}")
        return None

# Run test
if __name__ == "__main__":
    balance = fetch_balance()
    if balance is not None:
        print(f"✅ USD Balance: ${balance:.4f}")
    else:
        print("❌ Failed to fetch balance.")
