import os, threading, telebot, time, random, json, requests
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

VAULT_ADDRESS = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
MY_CHANNEL = "@ICEGODSICEDEVILS"
DB_FILE = "whitelist.json"

TIERS = {
    "basic": {"name": "Basic Node", "price": "0.5 MON", "strike_power": "15%"},
    "pro": {"name": "Pro Striker", "price": "2.0 MON", "strike_power": "60%"},
    "god": {"name": "Ice God Mode", "price": "5.0 MON", "strike_power": "100%"}
}

state = {"vault_balance": 312.85, "total_pools_hit": 10429, "recent_hits": []}

# --- FIXED BOT HANDLERS ---
@bot.message_handler(commands=['start', 'dashboard', 'stats'])
def handle_start(message):
    try:
        markup = telebot.types.InlineKeyboardMarkup()
        for key, data in TIERS.items():
            markup.add(telebot.types.InlineKeyboardButton(f"🔓 {data['name']} ({data['price']})", callback_data=f"pay_{key}"))
        
        web_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'mex-warsystem-wunb.onrender.com')}"
        markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", web_app=telebot.types.WebAppInfo(web_url)))

        welcome = (
            "❄️ *NEXUS v10.2 | STABLE*\n"
            "────────────────────\n"
            "Status: *ACTIVE*\n"
            f"Vault: `{VAULT_ADDRESS}`\n"
            "────────────────────\n"
            "Select your Node Tier:"
        )
        bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_payment(call):
    tier = TIERS.get(call.data.split('_')[1])
    msg = f"💳 *{tier['name'].upper()}*\n\nSend `{tier['price']}` to:\n`{VAULT_ADDRESS}`\n\nContact @MexRobert_Admin"
    bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

# --- ENGINES ---
def autonomous_engine():
    while True:
        time.sleep(random.randint(600, 1200))
        token = random.choice(["$MON", "$ICE", "$NEXUS"])
        profit = round(random.uniform(0.1, 0.5), 2)
        state["vault_balance"] += profit
        state["total_pools_hit"] += 1
        try:
            bot.send_message(MY_CHANNEL, f"🎯 *STRIKE:* `{token}`\nProfit: `+{profit} MON`", parse_mode='Markdown')
        except: pass

def heartbeat():
    url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'mex-warsystem-wunb.onrender.com')}"
    while True:
        try: requests.get(url)
        except: pass
        time.sleep(600)

@app.route('/')
def home(): return "NEXUS ONLINE"

@app.route('/api/stats')
def api_stats(): return jsonify(state)

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(timeout=10, long_polling_timeout=5), daemon=True).start()
    threading.Thread(target=autonomous_engine, daemon=True).start()
    threading.Thread(target=heartbeat, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
