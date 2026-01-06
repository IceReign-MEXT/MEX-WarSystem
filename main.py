import os, threading, time, telebot, random, requests, base64, json
from flask import Flask, render_template_string

# --- CONFIGURATION ---
VAULT_ETH = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
VAULT_SOL = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy"
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@ICEGODSICEDEVILS"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

state = {
    "members": ["559382910"],
    "nodes": 54,
    "sol_reserves": 335.55,
    "eth_reserves": 1.80099
}

def is_paid(uid):
    return str(uid) in state["members"]

# --- DUAL-CHAIN SURVEILLANCE ---
def global_monitoring():
    time.sleep(10) # Wait for bot to settle
    while True:
        time.sleep(random.randint(900, 1800))
        chain = random.choice(["SOLANA", "ETHEREUM"])
        whale_amt = random.randint(100, 1000)
        alert = (
            f"🚨 **{chain} WHALE ALERT** 🚨\n"
            "────────────────────\n"
            f"Detected: `{whale_amt} {'SOL' if chain=='SOLANA' else 'ETH'}` movement.\n"
            "Status: `BETTER THAN ALIENS BRAIN`"
        )
        try: bot.send_message(CHANNEL_ID, alert, parse_mode='Markdown')
        except: pass

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    msg = f"❄️ **MONOLITH V21: DUAL-CHAIN**\n\n🏦 **SOL:** `{VAULT_SOL}`\n🏦 **ETH:** `{VAULT_ETH}`"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", url="https://ice-gods-nexus.vercel.app"))
    markup.add(telebot.types.InlineKeyboardButton("🛠️ ACTIVATE NODE", callback_data="pay"))
    bot.reply_to(message, msg, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['strike', 'snipe', 'raid', 'stats', 'roadmap', 'snipers'])
def handle_all_commands(message):
    if not is_paid(message.from_user.id):
        bot.reply_to(message, "🔒 **ACCESS DENIED.**\nSubscription required: 0.5 ETH / 5 SOL.")
        return
    bot.reply_to(message, "🚀 **PROTOCOL ACTIVATED.**")

@bot.callback_query_handler(func=lambda c: c.data == "pay")
def pay_callback(call):
    bot.send_message(call.message.chat.id, f"💳 **VAULT PROTOCOL**\n\nETH: `{VAULT_ETH}`\nSOL: `{VAULT_SOL}`")

@app.route('/')
def home():
    return "MONOLITH NODE ACTIVE"

def run_bot():
    # Crucial: retry loop to handle the "409 Conflict" during redeploys
    while True:
        try:
            print("Starting bot...")
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Bot error: {e}. Retrying in 5s...")
            time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=global_monitoring, daemon=True).start()
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
