import os, time, requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ETH_ADDR = os.getenv("MAKER_ADDR")
RPC_URL = os.getenv("RPC_URL_ETH")

def get_status():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        bal = w3.from_wei(w3.eth.get_balance(ETH_ADDR), 'ether')
        return f"❄️ <b>ICE GODS ACTIVE</b>\n───\n💰 WALLET: {ETH_ADDR[:8]}...\n⛽ BAL: {float(bal):.4f} ETH\n💎 SUPPLY: 30B IBS\n✅ 1% FEE: ENABLED"
    except: return "⚠️ Syncing Oracle..."

def main():
    last_id = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id+1}").json()
            for u in r.get("result", []):
                last_id = u["update_id"]
                if "/status" in u.get("message", {}).get("text", ""):
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                    json={"chat_id": u["message"]["chat"]["id"], "text": get_status(), "parse_mode": "HTML"})
        except: time.sleep(5)

if __name__ == "__main__": main()
