import time
import threading
import logging
from datetime import datetime
from config import COINS, BTC_DROP_LIMIT, TICKER_MAP
from kraken_api import get_price, get_usd_balance, get_balance, place_market_order
from telegram_commands import send_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# === Active Trades Tracking ===
active_trades = {}  # e.g., { "PEPE": True, "DOGE": False }

def can_trade(coin):
    return not active_trades.get(coin, False)

def mark_trade_active(coin):
    active_trades[coin] = True

def mark_trade_closed(coin):
    active_trades[coin] = False


TP_BASE = 0.01
TP_EXTENDED_1 = 0.013
TP_EXTENDED_2 = 0.018
TP_FALLBACK_5H = 0.005
TP_FALLBACK_18H = 0.002

TREND_SYNC_REQUIRED = True
TREND_SYNC_WINDOW = 3  # how many checks to compare sync
TREND_SYNC_TOLERANCE = 0.5  # % difference tolerance

def get_recent_change(coin, minutes=5):
    initial = get_price(TICKER_MAP[coin])
    time.sleep(minutes * 60)
    later = get_price(TICKER_MAP[coin])
    return ((later - initial) / initial) * 100

def calculate_take_profit(entry_price, entry_time, coin):
    held_time = time.time() - entry_time
    if held_time < 60:
        return entry_price * (1 + TP_EXTENDED_2)
    elif held_time < 180:
        return entry_price * (1 + TP_EXTENDED_1)
    elif held_time < 5 * 3600:
        return entry_price * (1 + TP_BASE)
    elif held_time < 18 * 3600:
        send_message(f"🕐 {coin} fallback TP: +0.5% (5h)")
        return entry_price * (1 + TP_FALLBACK_5H)
    else:
        send_message(f"🕐 {coin} final TP: +0.2% (18h)")
        return entry_price * (1 + TP_FALLBACK_18H)

def is_market_stable():
    btc_start = get_price(TICKER_MAP["BTC"])
    eth_start = get_price(TICKER_MAP["ETH"])
    time.sleep(300)
    btc_now = get_price(TICKER_MAP["BTC"])
    eth_now = get_price(TICKER_MAP["ETH"])

    btc_change = ((btc_now - btc_start) / btc_start) * 100
    eth_change = ((eth_now - eth_start) / eth_start) * 100

    if btc_change < -0.3 or eth_change < -0.3:
        send_message(f"⚠️ BTC/ETH falling >0.3%. BTC={btc_change:.2f}%, ETH={eth_change:.2f}%. Skipping trades.")
        return False
    return True

def is_coin_in_sync(coin):
    btc = get_price(TICKER_MAP["BTC"])
    eth = get_price(TICKER_MAP["ETH"])
    alt = get_price(TICKER_MAP[coin])
    time.sleep(30)
    btc2 = get_price(TICKER_MAP["BTC"])
    eth2 = get_price(TICKER_MAP["ETH"])
    alt2 = get_price(TICKER_MAP[coin])

    btc_trend = btc2 - btc
    eth_trend = eth2 - eth
    alt_trend = alt2 - alt

    # Coin should move in same direction as BTC/ETH
    if (btc_trend > 0 and alt_trend < 0) or (eth_trend > 0 and alt_trend < 0):
        return False
    return True

def monitor_btc_eth_crash():
    initial_btc = get_price(TICKER_MAP["BTC"])
    initial_eth = get_price(TICKER_MAP["ETH"])
    time.sleep(300)
    new_btc = get_price(TICKER_MAP["BTC"])
    new_eth = get_price(TICKER_MAP["ETH"])

    drop_btc = ((new_btc - initial_btc) / initial_btc) * 100
    drop_eth = ((new_eth - initial_eth) / initial_eth) * 100

    return drop_btc < -0.5 or drop_eth < -0.5

def monitor_coin_trade(coin, volume, entry_price):
    entry_time = time.time()
    while True:
        current_price = get_price(TICKER_MAP[coin])
        if monitor_btc_eth_crash():
            send_message(f"⚡ BTC/ETH crash mid-trade. Exiting {coin} early at ~break-even.")
            place_market_order(TICKER_MAP[coin], volume, "sell")
            break
        mark_trade_closed(coin)
        target_price = calculate_take_profit(entry_price, entry_time, coin)
        if current_price >= target_price:
            sell = place_market_order(TICKER_MAP[coin], volume, "sell")
            if sell.get("error"):
                send_message(f"❌ Sell {coin} failed: {sell['error']}")
            else:
                profit = (current_price - entry_price) / entry_price * 100
                send_message(f"📈 Sold {coin} at ${current_price:.4f} | +{profit:.2f}%")
            break

        if time.time() - entry_time > 18 * 3600:
            send_message(f"⌛ {coin} held 18h — forced exit.")
            place_market_order(TICKER_MAP[coin], volume, "sell")
            break
        time.sleep(60)

def trade_coin(coin, allocation):

    active_now = sum(1 for c in active_trades if active_trades[c])
    if active_now >= 2:
        logging.info("⏳ Max 2 trades active. Skipping new entries for now.")
        return
    if not can_trade(coin):
        logging.info(f"⏳ Already in trade with {coin}. Skipping.")
        return

    if not is_market_stable():
        return
    if not is_coin_in_sync(coin):
        send_message(f"🧠 {coin} not in sync with BTC/ETH. Skipping.")
        return

    price = get_price(TICKER_MAP[coin])
    volume = round(allocation / price, 6)
    buy = place_market_order(TICKER_MAP[coin], volume, "buy")
    if buy.get("error"):
        send_message(f"❌ Buy {coin} failed: {buy['error']}")
        return

    send_message(f"✅ Bought {coin} at ${price:.4f}")
    mark_trade_active(coin)
    threading.Thread(target=monitor_coin_trade, args=(coin, volume, price)).start()

def resume_held_coins():
    balances = get_balance()["result"]
    for coin in COINS:
        for key in balances:
            if coin in key:
                volume = float(balances[key])
                if volume > 0:
                    price = get_price(TICKER_MAP[coin])
                    send_message(f"📦 Resuming monitoring of {volume} {coin}")
                    threading.Thread(target=monitor_coin_trade, args=(coin, volume, price)).start()

def run_bot():
    last_day = datetime.now().day
    while True:
        try:
            current_day = datetime.now().day
            if current_day != last_day:
                send_message("🔁 Daily restart triggered.")
                last_day = current_day
            send_message("🚀 Bot started")
            logging.info("🔍 Checking balance, coins and market conditions...")
            send_message("🤖 Bot is now running. Checking balance, coins, and monitoring market for entry...")

            resume_held_coins()
            balance = get_usd_balance()
            if balance <= 0:
                send_message("❌ No USD balance. Focusing only on selling current positions.")
                logging.info("💤 No USD available, skipping new buy logic.")
                resume_held_coins()
                time.sleep(600)
                continue

            allocation = balance / 2
            for coin in COINS:
                threading.Thread(target=trade_coin, args=(coin, allocation)).start()

            time.sleep(3600)
        except Exception as e:
            send_message(f"❌ Fatal error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
