import os
import time
import random
import logging
import requests
from web3 import Web3
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MEX-WarSystem")
load_dotenv()

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN = os.getenv("ADMIN_ID")
RPC_URL = "https://monad-mainnet.blockvision.org/v1/37HJ6YcLfOxeMxX0JS01bnFQzNV"
MAKER_KEY = os.getenv("MAKER_KEY")

V2_ROUTER = Web3.to_checksum_address(os.getenv("V2_ROUTER", "0xfb8e1c3b833f9e67a71c859a132cf783b645e436"))
WMON = Web3.to_checksum_address(os.getenv("WMON_ADDRESS", "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"))
TOKEN_ADDR = Web3.to_checksum_address(os.getenv("TOKEN_ADDRESS", "0x2cFa3EAb79E5CfE34EAabfb6aCaAC0Da0565Aa77"))

w3 = Web3(Web3.HTTPProvider(RPC_URL))
ROUTER_ABI = [{"name":"swapExactETHForTokens","type":"function","inputs":[{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"payable"}]

def send_msg(text):
    if TOKEN and ADMIN:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            r = requests.post(url, json={"chat_id": ADMIN, "text": text, "parse_mode": "HTML"})
            return r.status_code == 200
        except Exception as e:
            logger.error(f"Telegram fail: {e}")
    return False

def perform_buy():
    if not MAKER_KEY:
        logger.error("MAKER_KEY missing in .env!")
        return
    try:
        account = w3.eth.account.from_key(MAKER_KEY)
        router = w3.eth.contract(address=V2_ROUTER, abi=ROUTER_ABI)
        val = random.uniform(float(os.getenv("VOLUME_MIN", 0.01)), float(os.getenv("VOLUME_MAX", 0.05)))

        tx = router.functions.swapExactETHForTokens(0, [WMON, TOKEN_ADDR], account.address, int(time.time()) + 600).build_transaction({
            'from': account.address, 'value': w3.to_wei(val, 'ether'), 'gas': 400000,
            'gasPrice': w3.eth.gas_price, 'nonce': w3.eth.get_transaction_count(account.address), 'chainId': 10143
        })

        signed = w3.eth.account.sign_transaction(tx, MAKER_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

        logger.info(f"✅ Success: {tx_hash.hex()}")
        send_msg(f"🟢 <b>Green Buy!</b>\nAmount: {val:.4f} MON\n<a href='https://testnet.monadexplorer.com/tx/{tx_hash.hex()}'>View Tx</a>")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    logger.info("⚔️ Engine Starting...")
    send_msg("🚀 <b>MEX WarSystem Online</b>")
    while True:
        perform_buy()
        time.sleep(random.randint(60, 180))
