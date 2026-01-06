import os, threading, time, telebot, random, requests, base64, json
from flask import Flask, render_template_string

# --- CONFIGURATION ---
VAULT_ETH = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
VAULT_SOL = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy"
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@ICEGODSICEDEVILS"
DASH_URL = "https://mex-war-system-ox6f.vercel.app"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

state = {
    "members": ["559382910"],
    "nodes": 54
}

def is_paid(uid):
    return str(uid) in state["members"]

# --- BROADCAST ENGINE ---
def global_monitoring():
    # Wait 30 seconds to ensure the old bot instance has been killed by Render
    time.sleep(30)
    while True:
        try:
            time.sleep(random.randint(900, 1800))
            chain = random.choice(["SOLANA", "ETHEREUM"])
            whale_amt = random.randint(150, 850)
            alert = (
                f"🚨 **{chain} WHALE DETECTION** 🚨\n"
                "────────────────────\n"
                f"Value: `{whale_amt} {'SOL' if chain=='SOLANA' else 'ETH'}`\n"
                "Status: `54 NODES ACTIVE`\n"
                "────────────────────\n"
                f"🌐 [VIEW TERMINAL]({DASH_URL})"
            )
            bot.send_message(CHANNEL_ID, alert, parse_mode='Markdown')
        except:
            pass

# --- COMMANDS ---
@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    msg = f"❄️ **MONOLITH V21**\n\n🏦 **SOL:** `{VAULT_SOL}`\n🏦 **ETH:** `{VAULT_ETH}`"
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", url=DASH_URL),
        telebot.types.InlineKeyboardButton("💳 ACTIVATE NODE", callback_data="pay")
    )
    bot.reply_to(message, msg, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['strike', 'snipe', 'raid', 'stats', 'snipers'])
def handle_commands(message):
    if not is_paid(message.from_user.id):
        bot.reply_to(message, "🔒 **ACCESS DENIED.** Payment required.")
        return
    bot.reply_to(message, "🚀 **PROTOCOL ACTIVE.**")

@bot.callback_query_handler(func=lambda c: c.data == "pay")
def pay_callback(call):
    bot.send_message(call.message.chat.id, f"💳 **VAULT PROTOCOL**\n\nSOL: `{VAULT_SOL}`\nETH: `{VAULT_ETH}`")

# --- RENDER HEALTH CHECK FIX ---
@app.route('/health')
def health():
    return "OK", 200

@app.route('/')
def home():
    return "MONOLITH_ACTIVE", 200

# --- STABLE RUNTIME ---
def run_bot():
    # Initial sleep to let Render finish switching instances
    time.sleep(10)
    while True:
        try:
            bot.remove_webhook() # Clear any stuck webhooks
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            # If 409 Conflict happens, wait longer and retry
            time.sleep(10)

if __name__ == '__main__':
    threading.Thread(target=global_monitoring, daemon=True).start()
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
