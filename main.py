import os
import json
import requests
import telebot
from firebase_admin import credentials, firestore, initialize_app

# --- 🛡️ SOVEREIGN INFRASTRUCTURE BOOT ---
try:
    raw_service_account = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not raw_service_account:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_MISSING")

    cred = credentials.Certificate(json.loads(raw_service_account))
    initialize_app(cred)
    db = firestore.client()
    print("🛡️ DATABASE_LINK: ESTABLISHED")
except Exception as e:
    print(f"❌ BOOT_CRITICAL: {e}")

# --- 📡 CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
APP_ID = "mex-war-system"

# Public RPC Endpoints for Verification
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
ETH_RPC = "https://cloudflare-eth.com"

# --- 💎 BLOCKCHAIN VERIFICATION LOGIC ---
def verify_solana_tx(tx_hash):
    """Checks Solana blockchain for payment existence."""
    try:
        payload = {
            "jsonrpc": "2.0", "id": 1,
            "method": "getTransaction",
            "params": [tx_hash, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
        }
        response = requests.post(SOLANA_RPC, json=payload).json()
        if "result" in response and response["result"] is not None:
            return True
        return False
    except:
        return False

def verify_eth_tx(tx_hash):
    """Checks Ethereum blockchain for payment existence."""
    try:
        payload = {"jsonrpc":"2.0","method":"eth_getTransactionByHash","params":[tx_hash],"id":1}
        response = requests.post(ETH_RPC, json=payload).json()
        if "result" in response and response["result"] is not None:
            return True
        return False
    except:
        return False

# --- 🤖 COMMAND HANDLERS (AUTONOMOUS) ---

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📡 VIEW LIVE TERMINAL", url="https://mex-war-system-ox6f.vercel.app"))

    text = (
        "❄️ **MONOLITH V22: AUTONOMOUS SOVEREIGN** ❄️\n\n"
        "The machine is hunting. Zero human intervention required.\n\n"
        "📍 **SOL VAULT:** `8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy`\n"
        "📍 **ETH VAULT:** `0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F`\n\n"
        "**To Activate:**\n"
        "1. Send your tribute to a vault above.\n"
        "2. Reply with `/verify YOUR_TRANSACTION_HASH`"
    )
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['verify'])
def autonomous_verify(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Error: Provide the Transaction Hash. \nFormat: `/verify hash_here`", parse_mode="Markdown")
            return

        tx_hash = args[1]
        checking_msg = bot.reply_to(message, "🔍 `STRIKE_ENGINE: VERIFYING_ON_CHAIN...`", parse_mode="Markdown")

        # Try both chains
        is_valid = verify_solana_tx(tx_hash) or verify_eth_tx(tx_hash)

        if is_valid:
            # --- ⛓️ AUTOMATIC WHITELISTING ---
            user_id = str(message.from_user.id)
            user_ref = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('verified_users').document(user_id)

            user_ref.set({
                "username": message.from_user.username,
                "tx_hash": tx_hash,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "status": "ACTIVE"
            })

            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=checking_msg.message_id,
                text=f"✅ **VERIFIED.**\n\nWelcome to the Monolith, @{message.from_user.username}.\nYour node is now active on the Global Terminal.",
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=checking_msg.message_id,
                text="❌ **STRIKE_ENGINE: REJECTED.**\nTransaction not found or not confirmed yet. Try again in 60 seconds.",
                parse_mode="Markdown"
            )

    except Exception as e:
        bot.reply_to(message, f"❌ SYSTEM_ERROR: {str(e)}")

# --- 🚀 RUN ENGINE ---
if __name__ == "__main__":
    print("💎 MONOLITH_V22: ENGINE_STARTED")
    bot.infinity_polling()
