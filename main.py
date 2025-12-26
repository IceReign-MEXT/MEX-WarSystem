import os
import time
import threading
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
ETH_RPC = os.getenv("RPC_URL_ETH")
MAKER_ADDR = os.getenv("MAKER_ADDR")

w3 = Web3(Web3.HTTPProvider(ETH_RPC))

def send_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
    except: pass

def revenue_monitor():
    try: last_bal = float(w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether'))
    except: last_bal = 0
    while True:
        try:
            curr_bal = float(w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether'))
            if curr_bal > last_bal:
                send_msg(ADMIN_ID, f"💰 <b>REVENUE!</b>\nGain: +{curr_bal - last_bal:.4f} ETH")
                last_bal = curr_bal
        except: pass
        time.sleep(30)

def handle_cmds():
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=20"
            res = requests.get(url).json()
            for u in res.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message", {})
                if "/status" in msg.get("text", ""):
                    bal = w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether')
                    send_msg(msg["chat"]["id"], f"❄️ <b>STATUS</b>\nVault: {float(bal):.4f} ETH")
        except: time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=revenue_monitor, daemon=True).start()
    handle_cmds()
