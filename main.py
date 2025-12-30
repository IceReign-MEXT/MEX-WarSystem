import os, threading, telebot, time, random, json, requests
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# --- SYSTEM ASSETS ---
VAULT_ADDRESS = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
MY_CHANNEL = "@ICEGODSICEDEVILS"

TIERS = {
    "basic": {"name": "Basic Node", "price": "0.5 MON", "power": "15%"},
    "pro": {"name": "Pro Striker", "price": "2.0 MON", "power": "60%"},
    "god": {"name": "Ice God Mode", "price": "5.0 MON", "power": "100%"}
}

state = {
    "vault_balance": 312.85, 
    "total_pools_hit": 10429, 
    "recent_hits": [{"token": "INIT", "profit": 0, "time": "00:00"}]
}

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start', 'dashboard'])
def handle_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    for key, data in TIERS.items():
        markup.add(telebot.types.InlineKeyboardButton(f"🔓 {data['name']} ({data['price']})", callback_data=f"pay_{key}"))
    
    # Use environment URL or fallback
    host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'mex-warsystem-wunb.onrender.com')
    web_url = f"https://{host}"
    markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", web_app=telebot.types.WebAppInfo(web_url)))

    welcome = (
        "❄️ *NEXUS v10.3 | OPERATIONAL*\n"
        "────────────────────\n"
        f"Vault: `{VAULT_ADDRESS}`\n"
        "────────────────────\n"
        "Status: *STRIKING*"
    )
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_payment(call):
    tier = TIERS.get(call.data.split('_')[1])
    msg = f"💳 *{tier['name'].upper()}*\n\nSend `{tier['price']}` to:\n`{VAULT_ADDRESS}`\n\nContact @MexRobert_Admin"
    bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

# --- ENGINES ---
def autonomous_engine():
    while True:
        time.sleep(random.randint(600, 1200))
        token = random.choice(["$MON", "$ICE", "$NEXUS", "$WAR", "$VOID"])
        profit = round(random.uniform(0.1, 0.8), 2)
        state["vault_balance"] += profit
        state["total_pools_hit"] += 1
        new_hit = {"token": token, "profit": profit, "time": time.strftime("%H:%M")}
        state["recent_hits"].insert(0, new_hit)
        if len(state["recent_hits"]) > 10: state["recent_hits"].pop()
        try:
            bot.send_message(MY_CHANNEL, f"🎯 *STRIKE:* `{token}`\nProfit: `+{profit} MON`", parse_mode='Markdown')
        except: pass

# --- WEB DASHBOARD HTML ---
DASH_HTML = """
<!DOCTYPE html>
<html>
<head><title>NEXUS DASHBOARD</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-black text-cyan-400 font-mono p-4">
    <div class="max-w-md mx-auto border border-cyan-900 rounded-3xl p-6 bg-zinc-950 shadow-[0_0_20px_rgba(0,255,255,0.1)]">
        <h1 class="text-xl font-black italic mb-4">NEXUS_TERMINAL_v10.3</h1>
        <div class="grid grid-cols-2 gap-3 mb-6">
            <div class="p-3 bg-cyan-950/20 border border-cyan-900 rounded-xl">
                <p class="text-[8px] text-cyan-700">VAULT_BALANCE</p>
                <p class="text-lg font-bold text-white"><span id="vault">0</span> MON</p>
            </div>
            <div class="p-3 bg-cyan-950/20 border border-cyan-900 rounded-xl">
                <p class="text-[8px] text-cyan-700">POOL_STRIKES</p>
                <p class="text-lg font-bold text-white"><span id="scanned">0</span></p>
            </div>
        </div>
        <div class="h-64 overflow-hidden text-[10px] space-y-2 border-t border-cyan-900 pt-4" id="hits">
            <p class="text-cyan-800">>> INITIALIZING_SCANNER...</p>
        </div>
    </div>
    <script>
        function update() {
            fetch('/api/stats').then(r => r.json()).then(data => {
                document.getElementById('vault').innerText = data.vault_balance.toFixed(2);
                document.getElementById('scanned').innerText = data.total_pools_hit;
                const h = document.getElementById('hits');
                h.innerHTML = data.recent_hits.map(hit => 
                    `<p>[${hit.time}] <span class="text-white">STRIKE: ${hit.token}</span> | <span class="text-cyan-500">+${hit.profit} MON</span></p>`
                ).join('');
            });
        }
        setInterval(update, 3000);
        update();
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(DASH_HTML)

@app.route('/api/stats')
def api_stats(): return jsonify(state)

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(timeout=20), daemon=True).start()
    threading.Thread(target=autonomous_engine, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
