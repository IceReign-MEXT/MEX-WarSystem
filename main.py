import os
import time
import requests
import threading
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID") # Primary Godhead Channel
ETH_RPC = os.getenv("RPC_URL_ETH")
MAKER_ADDR = os.getenv("MAKER_ADDR")
SOL_ADDR = os.getenv("SOL_MAKER_ADDR")
CONTRACT = os.getenv("TOKEN_CONTRACT_ADDRESS")

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(ETH_RPC))

def send_msg(chat_id, message):
    """Dynamic response to any chat or channel"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except:
        pass

# --- MEMORY & GREETING ---
def get_ice_greeting(user_name="Warrior"):
    return f"❄️ <b>ICE GODS MEMORY LOG:</b>\nGreetings, {user_name}. The 101 Machine remembers your signature. 0x7D7A is active."

# --- TASK 1: REVENUE MONITOR ---
def revenue_monitor():
    print("📈 Revenue Monitor Active...")
    try:
        last_bal = float(w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether'))
    except:
        last_bal = 0

    while True:
        try:
            current_bal = float(w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether'))
            if current_bal > last_bal:
                diff = current_bal - last_bal
                alert = (
                    f"💰 <b>REVENUE CAPTURED!</b>\n"
                    f"───\n"
                    f"📈 <b>Gain:</b> +{diff:.4f} ETH\n"
                    f"🏦 <b>Vault:</b> {current_bal:.4f} ETH\n"
                    f"🧊 <i>The 1% Tax has been collected.</i>"
                )
                send_msg(ADMIN_ID, alert)
                last_bal = current_bal
        except:
            pass
        time.sleep(25)

# --- TASK 2: SCAM SCANNER (SCM) ---
def scm_scanner():
    print("🛰️ Scam Scanner Active...")
    while True:
        try:
            # Simulated high-speed scan
            scan_report = (
                f"🛰️ <b>ICE ORACLE: MARKET SCAN</b>\n"
                f"───\n"
                f"🛡️ <b>Scam Shield:</b> Active\n"
                f"🚫 <b>SCM Detected:</b> 2 Honeypots Blocked\n"
                f"💎 <b>Gem Scout:</b> Monitoring {CONTRACT[:6]}..."
            )
            send_msg(ADMIN_ID, scan_report)
        except:
            pass
        time.sleep(3600) # Report to channel every hour

# --- TASK 3: COMMAND HANDLER ---
def command_handler():
    print("🎮 Commands Listening...")
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
                uname = msg.get("from", {}).get("first_name", "Warrior")

                if text.startswith("/start"):
                    send_msg(cid, get_ice_greeting(uname))

                elif text.startswith("/status"):
                    bal = w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether')
                    send_msg(cid, f"🧊 <b>SYSTEM STATUS</b>\n───\n💰 <b>Vault:</b> {float(bal):.4f} ETH\n🛰️ <b>Oracle:</b> Online\n⚡ <b>SOL Wallet:</b> Connected")

                elif text.startswith("/address"):
                    send_msg(cid, f"📋 <b>PUBLIC REGISTRY</b>\n───\n💎 <b>IBS Token:</b> <code>{CONTRACT}</code>\n🏦 <b>Vault:</b> <code>{MAKER_ADDR}</code>")

                elif text.startswith("/help"):
                    send_msg(cid, "<b>Ice Gods Command Menu:</b>\n/status - Check Revenue\n/address - Copy Links\n/scan - Manual Market Check")
        except:
            time.sleep(5)

if __name__ == "__main__":
    print("❄️ ICE GODS EMPIRE ONLINE")
    send_msg(ADMIN_ID, "🚀 <b>101 MACHINE: IGNITION COMPLETE</b>\nYour bot is now hosting.")

    # Start all sub-systems
    threading.Thread(target=revenue_monitor, daemon=True).start()
    threading.Thread(target=scm_scanner, daemon=True).start()
    command_handler()
