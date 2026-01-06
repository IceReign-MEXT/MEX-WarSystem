import os, threading, time, telebot, random, requests, base64, json
from flask import Flask, render_template_string, jsonify

# --- THE ARCHITECT'S CORE ---
ARCHITECT_WALLET = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
GEMINI_API_KEY = "AIzaSyBKuQjUPi9WK2c66r7L_weuj7CD8PtpUo4"
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@ICEGODSICEDEVILS"
DASH_URL = "https://ice-gods-nexus.vercel.app"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- SYSTEM STATE ---
state = {
    "eth_vault": 1.80099,
    "usd_valuation": 5804.64,
    "verified_members": ["559382910"],
    "nodes_active": 158
}

# 1. WHALE SURVEILLANCE
def surveillance_engine():
    while True:
        time.sleep(random.randint(1200, 2400))
        whale_amt = random.randint(50, 450)
        alert = (
            "🐋 **MULTITUDE WHALE DETECTION**\n"
            "────────────────────\n"
            f"Value: `{whale_amt} ETH`\n"
            "Target: `Liquidity Pool Alpha`\n"
            "────────────────────\n"
            "📊 **STATUS:** `NODES PRIMED`"
        )
        try: bot.send_message(CHANNEL_ID, alert, parse_mode='Markdown')
        except: pass

# 2. THE GATEKEEPER
def is_authorized(user_id):
    return str(user_id) in state["verified_members"]

@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 NEXUS TERMINAL", url=DASH_URL),
        telebot.types.InlineKeyboardButton("⚡ ACTIVATE NODE", callback_data="pay")
    )
    bot.reply_to(message, "❄️ **MONOLITH v20.0**\n\nStatus: `CONNECTED`\nVault: `0xf34c...888F`", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    if not is_authorized(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💳 ACTIVATE (0.5 ETH)", callback_data="pay"))
        bot.reply_to(message, "🔒 **ACCESS DENIED.**\nSubscription required.", parse_mode='Markdown', reply_markup=markup)
        return
    bot.reply_to(message, "🚀 **COMMAND EXECUTED.**")

@bot.callback_query_handler(func=lambda c: c.data == "pay")
def pay_callback(call):
    bot.send_message(call.message.chat.id, f"💳 **VAULT PROTOCOL**\n\nSend 0.5 ETH to:\n`{ARCHITECT_WALLET}`")

# 3. WEB INTERFACE
@app.route('/')
def home():
    return "MONOLITH NODE ACTIVE"

if __name__ == '__main__':
    threading.Thread(target=surveillance_engine, daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
