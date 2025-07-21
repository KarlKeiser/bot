import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
last_update_id = 0  # Will track the last processed update ID

def send_message(text):
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", data=payload, timeout=5)
    except Exception as e:
        print(f"Telegram send error: {e}")

def get_updates():
    global last_update_id
    try:
        params = {
            "offset": last_update_id + 1,
            "timeout": 1
        }
        response = requests.get(f"{TELEGRAM_API}/getUpdates", params=params, timeout=5)
        data = response.json()

        updates = []
        for result in data.get("result", []):
            message = result.get("message")
            if message:
                updates.append(message)
                last_update_id = result["update_id"]

        return updates

    except Exception as e:
        print(f"Telegram getUpdates error: {e}")
        return []
