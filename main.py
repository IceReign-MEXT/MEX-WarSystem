import os
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ETH_ADDR = os.getenv("MAKER_ADDR")
RPC_URL = os.getenv("RPC_URL_ETH")
ADMIN_ID = os.getenv("ADMIN_ID")

def get_status():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            return "⚠️ RPC Connection Failed"
        
        balance_wei = w3.eth.get_balance(ETH_ADDR)
        bal = w3.from_wei(balance_wei, 'ether')
        
        status_msg = (
            "❄️ <b>ICE GODS ENGINE ACTIVE</b>\n"
            "───\n"
            f"💰 WALLET: <code>{ETH_ADDR[:10]}...</code>\n"
            f"⛽ BALANCE: {float(bal):.4f} ETH\n"
            "💎 SUPPLY: 30B IBS\n"
            "🛡️ 1% FEE: ARMED & READY"
        )
        return status_msg
    except Exception as e:
        return f"⚠️ Syncing Oracle... Error: {str(e)[:20]}"

def main():
    print("🚀 ICE GODS ENGINE STARTING ON RENDER...")
    last_id = 0
    while True:
        try:
            # Check for Telegram Updates
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id+1}&timeout=30"
            response = requests.get(url).json()
            
            for update in response.get("result", []):
                last_id = update["update_id"]
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")

                if "/status" in text:
                    requests.post(
                        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": get_status(),
                            "parse_mode": "HTML"
                        }
                    )
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
