import os, threading, telebot, time, random, json, requests
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

VAULT_ADDRESS = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
RENDER_URL = "https://mex-warsystem-wunb.onrender.com"

# --- SIMPLE TEXT TO PREVENT CRASHING ---
@bot.message_handler(commands=['start', 'dashboard'])
def handle_start(message):
    try:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="🌐 OPEN TERMINAL", web_app=telebot.types.WebAppInfo(url=RENDER_URL)))
        markup.add(telebot.types.InlineKeyboardButton(text="🔓 ACTIVATE NODE (0.5 MON)", callback_data="pay_basic"))
        
        # Use plain text to avoid Markdown parsing errors
        welcome = (
            "ICE GODS | NEXUS v10.5\n"
            "--------------------\n"
            "System: ONLINE\n"
            f"Vault: {VAULT_ADDRESS}\n"
            "--------------------\n"
            "Click below to start:"
        )
        bot.send_message(message.chat.id, welcome, reply_markup=markup)
    except Exception as e:
        print(f"Bot Error: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    msg = f"PAYMENT GATEWAY\n\nSend 0.5 MON to:\n{VAULT_ADDRESS}\n\nContact @MexRobert_Admin"
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, msg)

# --- WEB SERVER ROUTES ---
@app.route('/')
def home():
    return "NEXUS TERMINAL IS LIVE"

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/stats')
def api_stats():
    return jsonify({"vault_balance": 314.15, "total_pools_hit": 10512, "recent_hits": []})

if __name__ == "__main__":
    # Start polling with skip_updates to clear the "stuck" messages
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
