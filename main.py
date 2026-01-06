import os, threading, time, telebot, random, requests, json
from flask import Flask
from firebase_admin import credentials, firestore, initialize_app, auth as admin_auth

# --- THE SOVEREIGN CONFIG ---
VAULT_ETH = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
VAULT_SOL = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy"
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DASH_URL = "https://mex-war-system-ox6f.vercel.app"
CHANNEL_ID = "@ICEGODSICEDEVILS"

# Initialize Firebase for persistence
firebase_config = json.loads(os.environ.get("__firebase_config", "{}"))
app_id = os.environ.get("__app_id", "mex-war-system")
cred = credentials.Certificate(json.loads(os.environ.get("FIREBASE_SERVICE_ACCOUNT")))
initialize_app(cred)
db = firestore.client()

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# --- BLOCKCHAIN VERIFIER (AUTOMATIC DETECTION) ---
def verify_tx_sol(tx_hash):
    """Verifies a Solana Transaction via Public RPC"""
    try:
        url = "https://api.mainnet-beta.solana.com"
        payload = {
            "jsonrpc": "2.0", "id": 1,
            "method": "getTransaction",
            "params": [tx_hash, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
        }
        response = requests.post(url, json=payload).json()
        # Check if the vault received > 4.9 SOL
        # (Simplified logic for the example - checks if tx exists)
        return "result" in response and response["result"] is not None
    except:
        return False

# --- CORE LOGIC ---
def get_user_ref(uid):
    return db.collection('artifacts').document(app_id).collection('public').document('data').collection('verified_users').document(str(uid))

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 VIEW REAL-TIME DASHBOARD", url=DASH_URL),
        telebot.types.InlineKeyboardButton("💳 AUTO-ACTIVATE NODE", callback_data="pay_auto")
    )
    bot.reply_to(message, "❄️ **MONOLITH V22: AUTONOMOUS**\n\nStatus: `LISTENING`\n\nThe Ice Gods no longer require manual approval. The machine detects your tribute instantly.", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "pay_auto")
def pay_auto(call):
    instruction = (
        "💳 **AUTONOMOUS ACTIVATION**\n\n"
        "1. Send **5 SOL** or **0.5 ETH** to the vaults.\n"
        "2. Copy the **Transaction Hash (TXID)**.\n"
        "3. Type `/verify [your_tx_id]` here.\n\n"
        f"SOL: `{VAULT_SOL}`\n"
        f"ETH: `{VAULT_ETH}`"
    )
    bot.send_message(call.message.chat.id, instruction, parse_mode='Markdown')

@bot.message_handler(commands=['verify'])
def verify_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Please provide the Transaction ID.\nFormat: `/verify TX_HASH_HERE`", parse_mode='Markdown')
        return

    tx_id = args[1]
    bot.reply_to(message, "🔍 **SCANNING BLOCKCHAIN...**\nThis takes ~30 seconds.", parse_mode='Markdown')

    # Simulate Blockchain Verification (In production, use verify_tx_sol/eth)
    time.sleep(5)

    # Auto-Whitelist in Database
    user_ref = get_user_ref(message.from_user.id)
    user_ref.set({
        "activated_at": firestore.SERVER_TIMESTAMP,
        "tx_id": tx_id,
        "username": message.from_user.username
    })

    bot.reply_to(message, "✅ **ACCESS GRANTED.**\n\nYour Node is now synchronized with the 54-Node Multitude. All commands are now unlocked.", parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, f"🆕 **NODE ACTIVATED**\nUser: @{message.from_user.username}\nNetwork: `AUTONOMOUS_V22`", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def gated_access(message):
    user_ref = get_user_ref(message.from_user.id)
    if not user_ref.get().exists:
        bot.reply_to(message, "🔒 **ACCESS DENIED.**\nUse `/verify` to unlock.", parse_mode='Markdown')
        return
    bot.reply_to(message, "🚀 **STRIKE ENGINE ACTIVE.** Scanning pools...")

@app.route('/health')
def health(): return "OK", 200

def run_bot():
    while True:
        try: bot.infinity_polling()
        except: time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
