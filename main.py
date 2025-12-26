import os
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Config
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RPC_ETH = os.getenv("RPC_URL_ETH")
CONTRACT_ADDR = os.getenv("TOKEN_CONTRACT_ADDRESS")
MAKER_ADDR = os.getenv("MAKER_ADDR")

w3 = Web3(Web3.HTTPProvider(RPC_ETH))

def get_status():
    try:
        eth_bal = w3.from_wei(w3.eth.get_balance(MAKER_ADDR), 'ether')
        return (
            f"❄️ <b>ICE GODS SYSTEM ACTIVE</b>\n"
            f"────────────────────\n"
            f"💰 <b>REVENUE WALLET:</b> {MAKER_ADDR[:6]}...{MAKER_ADDR[-4:]}\n"
            f"💎 <b>SUPPLY:</b> 30,000,000,000 IBS\n"
            f"⛽ <b>MAKER BALANCE:</b> {float(eth_bal):.4f} ETH\n"
            f"🛰️ <b>RPC STATUS:</b> ALCHEMY CONNECTED\n"
            f"────────────────────\n"
            f"✅ <i>Monitoring blockchain for trades...</i>"
        )
    except Exception as e:
        return f"⚠️ Oracle Sync Error: {str(e)}"

def main():
    print("🚀 ICE GODS ENGINE STARTING...")
    last_id = 0
    while True:
        try:
            updates = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id+1}&timeout=30").json()
            for u in updates.get("result", []):
                last_id = u["update_id"]
                msg = u.get("message", {}).get("text", "")
                chat_id = u["message"]["chat"]["id"]

                if "/status" in msg:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                 json={"chat_id": chat_id, "text": get_status(), "parse_mode": "HTML"})
        except:
            time.sleep(10)

if __name__ == "__main__":
    main()
