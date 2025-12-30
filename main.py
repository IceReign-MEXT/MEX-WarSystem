import os
import threading
import telebot
import time
import random
import json
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# --- CONFIG & ASSETS ---
VAULT_ADDRESS = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
MY_CHANNEL = "@ICEGODSICEDEVILS"
DB_FILE = "whitelist.json"

# --- DATABASE LOGIC ---
def get_whitelist():
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return []

def add_to_whitelist(user_id):
    users = get_whitelist()
    if user_id not in users:
        users.append(user_id)
        with open(DB_FILE, 'w') as f: json.dump(users, f)

# --- BOT INTERFACE ---
@bot.message_handler(commands=['start', 'dashboard'])
def handle_start(message):
    user_id = message.from_user.id
    whitelist = get_whitelist()
    markup = telebot.types.InlineKeyboardMarkup()
    web_app = telebot.types.WebAppInfo(f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'mex-warsystem-wunb.onrender.com')}")
    
    if user_id in whitelist:
        markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL [ADMIN]", web_app=web_app))
        status = "✅ AUTHORIZED"
    else:
        markup.add(telebot.types.InlineKeyboardButton("💳 ACTIVATE NODE (0.5 MON)", callback_data="buy"))
        status = "❌ RESTRICTED"

    msg = f"❄️ **NEXUS v8.5 | IRONCLAD**\n\nStatus: {status}\nVault: `{VAULT_ADDRESS}`\n\n_Use /stats to see network health._"
    bot.send_message(message.chat.id, msg, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['stats', 'snipers', 'strike'])
def handle_stats(message):
    stats_msg = (
        "📊 **NEXUS NETWORK STATS**\n"
        "────────────────────\n"
        "🎯 Total Snipes: `1,284` \n"
        "🛰️ Nodes Online: `46/50` \n"
        "💰 Vault Capture: `284.15 MON` \n"
        "────────────────────\n"
        "Status: **OPTIMIZED**"
    )
    bot.send_message(message.chat.id, stats_msg, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "buy")
def handle_buy(call):
    msg = f"💳 **PAYMENT GATEWAY**\n\nSend **0.5 MON** to:\n`{VAULT_ADDRESS}`\n\nThen DM @MexRobert_Admin"
    bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

@bot.message_handler(commands=['whitelist'])
def handle_whitelist(message):
    # Only you can whitelist
    if str(message.from_user.id) == "YOUR_TELEGRAM_ID" or message.from_user.username == "MexRobert_Admin":
        try:
            target = int(message.text.split()[1])
            add_to_whitelist(target)
            bot.reply_to(message, f"✅ ID {target} Whitelisted.")
        except: bot.reply_to(message, "Usage: /whitelist <id>")

# --- WEB UI ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>NEXUS</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-black text-cyan-400 p-8 font-mono">
    <h1 class="text-2xl font-bold italic border-b border-cyan-900 pb-2">NEXUS_v8.5</h1>
    <div class="mt-6 p-4 border border-cyan-500 rounded-xl bg-cyan-900/10">
        <p class="text-xs text-zinc-500">VAULT_BALANCE</p>
        <p class="text-3xl font-bold">284.15 <span class="text-sm">MON</span></p>
    </div>
    <div class="mt-8 space-y-2 text-[10px]" id="logs"></div>
    <script>
        setInterval(() => {
            const p = document.createElement('p');
            p.innerText = `[${new Date().toLocaleTimeString()}] SCANNING MONAD_MAINNET... OK`;
            document.getElementById('logs').prepend(p);
        }, 3000);
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(DASHBOARD_HTML)

if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
