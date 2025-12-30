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

# --- EMPIRE ASSETS ---
VAULT_ADDRESS = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
MY_CHANNEL = "@ICEGODSICEDEVILS"
DB_FILE = "whitelist.json"

# --- SUBSCRIPTION TIERS (The Money Maker) ---
TIERS = {
    "basic": {"name": "Basic Node", "price": "0.5 MON", "power": "15%"},
    "pro": {"name": "Pro Striker", "price": "2.0 MON", "power": "60%"},
    "god": {"name": "Ice God Mode", "price": "5.0 MON", "power": "100%"}
}

# --- GLOBAL POOL SCANNER (Autonomous Logic) ---
market_state = {
    "vault_balance": 312.85,
    "pools_scanned": 10429,
    "total_revenue": 14.2,
    "recent_hits": []
}

def global_scanner_engine():
    """Simulates scanning the whole world's liquidity pools"""
    while True:
        time.sleep(random.randint(200, 500))
        token = random.choice(["$BOLT", "$FURY", "$NEXUS", "$GLITCH", "$VOID"])
        profit = round(random.uniform(0.1, 1.5), 2)
        
        hit = {"token": token, "profit": profit, "time": time.strftime("%H:%M:%S")}
        market_state["recent_hits"].insert(0, hit)
        market_state["pools_scanned"] += random.randint(5, 50)
        market_state["vault_balance"] += profit * 0.02 # 2% tax logic
        
        # Automatic Channel Flex
        msg = f"🛰️ **GLOBAL POOL STRIKE**\n\nAsset: `{token}`\nProfit: `+{profit} MON`\nSystem Load: `98%` (High Frequency)\n\n[UPGRADE NODE](https://t.me/IceGodsBoost_Bot)"
        try:
            bot.send_message(MY_CHANNEL, msg, parse_mode='Markdown')
        except: pass

# --- BOT INTERFACE ---
@bot.message_handler(commands=['start', 'upgrade'])
def handle_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # Subscription Tier Buttons
    for key, data in TIERS.items():
        markup.add(telebot.types.InlineKeyboardButton(f"🔓 {data['name']} ({data['price']})", callback_data=f"pay_{key}"))
    
    web_app = telebot.types.WebAppInfo("https://mex-warsystem-wunb.onrender.com")
    markup.add(telebot.types.InlineKeyboardButton("🌐 ENTER GLOBAL TERMINAL", web_app=web_app))

    welcome = (
        "❄️ **ICE GODS: GLOBAL STRIKE v10.0**\n"
        "────────────────────\n"
        "The world's liquidity is now under your control.\n\n"
        f"🏦 **VAULT:** `{VAULT_ADDRESS}`\n"
        "────────────────────\n"
        "Select your Node Tier to begin striking:"
    )
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_payment_request(call):
    tier_key = call.data.split('_')[1]
    tier = TIERS[tier_key]
    msg = (
        f"💳 **{tier['name'].upper()} ACTIVATION**\n"
        f"Price: `{tier['price']}`\n"
        f"Power: `{tier['power']}`\n\n"
        f"Send funds to:\n`{VAULT_ADDRESS}`\n\n"
        "Once sent, DM @MexRobert_Admin with Hash."
    )
    bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

# --- WEB DASHBOARD (THE GLOBAL VIEW) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>GLOBAL TERMINAL</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-black text-green-400 font-mono p-4">
    <div class="max-w-md mx-auto border-2 border-green-900 rounded-3xl p-6 bg-zinc-950">
        <h1 class="text-xl font-black italic mb-4">GLOBAL_NEXUS_v10</h1>
        <div class="grid grid-cols-2 gap-2 mb-4">
            <div class="p-3 bg-green-900/10 border border-green-900 rounded-xl">
                <p class="text-[8px] text-green-700">TOTAL_VAULT</p>
                <p class="text-lg font-bold text-white"><span id="vault">0</span> MON</p>
            </div>
            <div class="p-3 bg-green-900/10 border border-green-900 rounded-xl">
                <p class="text-[8px] text-green-700">POOLS_SCANNED</p>
                <p class="text-lg font-bold text-white"><span id="scanned">0</span></p>
            </div>
        </div>
        <div class="h-48 overflow-hidden text-[9px] border-t border-green-900 pt-4" id="hits">
            <p class="text-green-800">>> INITIALIZING GLOBAL SCANNER...</p>
        </div>
    </div>
    <script>
        function update() {
            fetch('/api/stats').then(r => r.json()).then(data => {
                document.getElementById('vault').innerText = data.vault_balance.toFixed(2);
                document.getElementById('scanned').innerText = data.pools_scanned;
                const h = document.getElementById('hits');
                h.innerHTML = data.recent_hits.map(hit => 
                    `<p>[${hit.time}] STRIKE: <span class="text-white">${hit.token}</span> | PROFIT: <span class="text-white">+${hit.profit}</span></p>`
                ).join('') + h.innerHTML;
            });
        }
        setInterval(update, 3000);
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def api_stats(): return jsonify(market_state)

if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    threading.Thread(target=global_scanner_engine, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
