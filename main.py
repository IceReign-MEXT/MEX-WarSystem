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

# --- THE ARCHITECT'S DATA ---
VAULT_ADDRESS = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
MY_CHANNEL = "@ICEGODSICEDEVILS"
SLOTS_REMAINING = 5 # Scarcity trigger

# --- PERSISTENT EMPIRE STATS ---
stats = {
    "vault_total": 248.92,
    "last_snipe": "NONE",
    "nodes_online": 12,
    "gate_status": "LOCKED"
}

# --- AUTOMATED WAR-LOGS ---
def war_log_engine():
    """Generates the proof of work that drives the greed of users"""
    while True:
        time.sleep(random.randint(400, 800))
        token = random.choice(["$MON", "$ICE", "$NEXUS", "$GLITCH", "$VAULT"])
        msg = (
            "⚠️ **NEXUS SIGNAL DETECTED**\n"
            f"🎯 Target: `{token}`\n"
            "📈 Expected Impact: `+18.4%`\n"
            "────────────────────\n"
            "Only **PREMIUM** nodes are executing this strike.\n"
            "🔗 [UPGRADE NOW](https://t.me/IceGodsBoost_Bot)"
        )
        try:
            bot.send_message(MY_CHANNEL, msg, parse_mode='Markdown')
        except: pass

# --- BOT INTERFACE ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    web_app = telebot.types.WebAppInfo("https://mex-warsystem-wunb.onrender.com")
    
    markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", web_app=web_app))
    markup.add(telebot.types.InlineKeyboardButton("💳 ACTIVATE PREMIUM (0.5 MON)", callback_data="buy_access"))
    markup.add(telebot.types.InlineKeyboardButton("📢 INTEL FEED", url=f"https://t.me/{MY_CHANNEL[1:]}"))

    welcome = (
        "❄️ **ICE GODS: NEXUS TERMINAL v8.0**\n"
        "────────────────────\n"
        "Status: **DEPLOYED & ACTIVE**\n\n"
        f"🔥 *Limited Access:* Only `{SLOTS_REMAINING}` Premium Nodes remaining.\n"
        f"🏦 *Vault:* `{VAULT_ADDRESS}`\n"
        "────────────────────\n"
        "Click the button below to verify your ID."
    )
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_access")
def buy_access(call):
    bot.answer_callback_query(call.id)
    msg = (
        "💳 **PREMIUM ACTIVATION PROTOCOL**\n"
        "────────────────────\n"
        "1. Send **0.5 MON** to the Vault:\n"
        f"`{VAULT_ADDRESS}`\n\n"
        "2. Forward your Transaction Hash to @MexRobert_Admin (Simulated)\n\n"
        "Once verified, your Telegram ID will be permanently whitelisted."
    )
    bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

# --- WEB UI (THE PSYCHOLOGICAL WEAPON) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS | OPERATIONAL</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #000; color: #00ffcc; font-family: 'JetBrains Mono', monospace; }
        .border-glow { border: 1px solid #00ffcc; box-shadow: 0 0 20px rgba(0, 255, 204, 0.4); }
        .text-neon { color: #fff; text-shadow: 0 0 5px #00ffcc; }
    </style>
</head>
<body class="p-6">
    <div class="max-w-md mx-auto">
        <header class="mb-8 border-b border-zinc-800 pb-4">
            <h1 class="text-2xl font-black text-neon">NEXUS_v8.0</h1>
            <p class="text-[8px] text-zinc-500 italic">SECURE CONNECTION: ESTABLISHED</p>
        </header>

        <div class="grid grid-cols-2 gap-4 mb-8">
            <div class="border-glow bg-zinc-900/50 p-4 rounded-xl">
                <p class="text-[8px] text-zinc-400">VAULT_TOTAL</p>
                <p class="text-xl font-bold"><span id="total">0</span> <span class="text-[10px]">MON</span></p>
            </div>
            <div class="border-glow bg-zinc-900/50 p-4 rounded-xl">
                <p class="text-[8px] text-zinc-400">NODES_ON</p>
                <p class="text-xl font-bold">12/50</p>
            </div>
        </div>

        <div class="bg-zinc-900/20 border border-zinc-800 p-4 rounded-xl h-64 overflow-hidden text-[9px]">
            <div id="logs" class="space-y-1"></div>
        </div>
    </div>
    <script>
        function update() {
            fetch('/api/stats').then(r => r.json()).then(data => {
                document.getElementById('total').innerText = data.vault_total.toFixed(2);
                const l = document.getElementById('logs');
                const p = document.createElement('p');
                p.innerHTML = `<span class="text-zinc-700">[${new Date().toLocaleTimeString()}]</span> SCANNING DEX_LIQUIDITY... <span class="text-white">OK</span>`;
                l.prepend(p);
                if(l.children.length > 15) l.lastChild.remove();
            });
        }
        setInterval(update, 2500);
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
    threading.Thread(target=war_log_engine, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
