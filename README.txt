🚀 Trading Bot - Windows 11 Setup Guide

This bot supports simulation and live mode with Kraken and Telegram integration.

🧰 Requirements:
1. Windows 11
2. Python 3.10 or newer
3. pip install -r requirements.txt (required packages: requests)

📂 Folder Contents:
- main.py         ← Start this file to run the bot
- config.py       ← Set your coins, TP/SL, Telegram and Kraken API keys
- README.txt      ← You're reading it!

🟢 Getting Started:
1. Open Command Prompt
2. Navigate to this folder:
   cd path\to\trading_bot
3. Run the bot:
   python main.py

✏️ Edit config.py to:
- Switch between simulation and live mode
- Add/change coins
- Set custom TP/SL
- Set your Telegram token and chat ID
- Add your Kraken API keys (for live mode)

🔐 SECURITY WARNING:
Never share your config.py publicly. It contains sensitive keys.

❓ Need Help?
Message the bot via Telegram commands like:
- stop
- resume
- trade DOGE
- full out
