import os
import time
import threading
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Config from Environment
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
ETH_RPC = os.getenv("RPC_URL_ETH")
MAKER_ADDR = os.getenv("MAKER_ADDR")
CONTRACT = os.getenv("TOKEN_CONTRACT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(ETH_RPC))

def send_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def revenue_tracker():
    print("📈 Revenue Tracker Active...")
    try:
        last_bal = float(w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether'))
    except:
        last_bal = 0
    while True:
        try:
            curr_bal = float(w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether'))
            if curr_bal > last_bal:
                send_msg(ADMIN_ID, f"💰 <b>REVENUE CAPTURED!</b>\nGain: +{curr_bal - last_bal:.4f} ETH\nVault: {curr_bal:.4f} ETH")
                last_bal = curr_bal
        except: pass
        time.sleep(30)

def command_handler():
    print("🎮 Commands Active...")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=20"
            res = requests.get(url).json()
            for u in res.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message", {})
                text = msg.get("text", "")
                cid = msg.get("chat", {}).get("id")
                
                if "/status" in text:
                    bal = w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether')
                    status = f"❄️ <b>SYSTEM STATUS</b>\nVault: {float(bal):.4f} ETH\nSupply: 30B IBS"
                    send_msg(cid, status)
                elif "/address" in text:
                    send_msg(cid, f"📋 <b>REGISTRY</b>\nToken: <code>{CONTRACT}</code>\nVault: <code>{MAKER_ADDR}</code>")
        except: time.sleep(5)

if __name__ == "__main__":
    if ADMIN_ID:
        send_msg(ADMIN_ID, "🚀 <b>101 MACHINE: RECONSTRUCTION LIVE</b>")
    threading.Thread(target=revenue_tracker, daemon=True).start()
    command_handler()
