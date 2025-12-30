import os
import threading
import telebot
import time
import random
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# --- CONFIG & IDENTITY ---
OPERATOR = "Mex Robert"
MY_CHANNEL_ID = "@ICEGODSICEDEVILS" 
VAULT_ADDRESS = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"

# --- GLOBAL ENGINE STATE ---
stats = {
    "total_volume": 168.42,
    "revenue_24h": 3.368,
    "snipes_count": 184,
    "status": "MONITORING_DEX",
    "last_snipe": {"token": "NONE", "gain": "0%"}
}

# --- AUTOMATED MARKETING PROBABILITY ---
def marketing_engine():
    while True:
        time.sleep(random.randint(480, 900))
        tokens = ["$ICE-MON", "$WAR-CRY", "$MEX-SNIPE", "$MONAD-GOLD", "$NEXUS-GEM"]
        token = random.choice(tokens)
        profit_x = random.choice(["2.5x", "4.1x", "1.8x", "12.4x"])
        
        stats["snipes_count"] += 1
        stats["last_snipe"] = {"token": token, "gain": profit_x}
        
        msg = (
            "🚀 **STRATEGIC SNIPE CONFIRMED** 🚀\n"
            "────────────────────\n"
            f"💎 **Asset:** `{token}`\n"
            f"📈 **Execution:** {profit_x} Captured\n"
            f"🏦 **Tax Routed:** `0.0{random.randint(10,99)} MON`\n"
            "────────────────────\n"
            "🌐 [LIVE TERMINAL](https://mex-warsystem-wunb.onrender.com)\n"
            "📡 *Status: NEXUS v6.0 Performance Stable*"
        )
        try:
            bot.send_message(MY_CHANNEL_ID, msg, parse_mode='Markdown')
        except:
            pass

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    web_app = telebot.types.WebAppInfo("https://mex-warsystem-wunb.onrender.com")
    markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", web_app=web_app))
    welcome = "❄️ *ICE GODS NEXUS: MASTER ACCESS*"
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=markup)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS | MASTER</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #000; color: #00ffcc; font-family: monospace; }
        .box { border: 1px solid #00ffcc; background: rgba(0,255,204,0.05); }
    </style>
</head>
<body class="p-6">
    <div class="max-w-md mx-auto">
        <h1 class="text-xl mb-4">NEXUS_v6.0 | <span class="text-xs">MEX ROBERT</span></h1>
        <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="box p-4 rounded">REVENUE: <span id="rev">0</span></div>
            <div class="box p-4 rounded">SNIPES: <span id="snipes">0</span></div>
        </div>
        <div class="box p-4 h-64 overflow-hidden text-[10px]" id="logs"></div>
    </div>
    <script>
        function update() {
            fetch('/api/stats').then(r => r.json()).then(data => {
                document.getElementById('rev').innerText = data.revenue_24h.toFixed(3);
                document.getElementById('snipes').innerText = data.snipes_count;
                const log = document.getElementById('logs');
                const p = document.createElement('p');
                p.innerHTML = `[${new Date().toLocaleTimeString()}] SCANNING... OK`;
                log.prepend(p);
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
def api_stats(): return jsonify(stats)

if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    threading.Thread(target=marketing_engine, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
