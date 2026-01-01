import os, threading, telebot, time, random, json, requests
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")

# Initialize bot with a longer timeout for Render's network
bot = telebot.TeleBot(TOKEN, threaded=False)

VAULT_ADDRESS = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
RENDER_URL = "https://mex-warsystem-wunb.onrender.com"

# Shared System State
state = {
    "vault_balance": 314.15,
    "total_pools_hit": 10512,
    "recent_hits": [{"token": "$MON", "profit": 0.15, "time": "12:00"}]
}

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start', 'dashboard'])
def handle_start(message):
    try:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="🌐 OPEN TERMINAL", web_app=telebot.types.WebAppInfo(url=RENDER_URL)))
        markup.add(telebot.types.InlineKeyboardButton(text="🔓 BASIC NODE (0.5 MON)", callback_data="pay_0.5"))
        
        welcome = (
            "NEXUS TERMINAL v10.7\n"
            "--------------------\n"
            "STATUS: ACTIVE\n"
            f"VAULT: {VAULT_ADDRESS}\n"
            "--------------------\n"
            "Click below to initialize terminal:"
        )
        bot.send_message(message.chat.id, welcome, reply_markup=markup)
    except Exception as e:
        print(f"Bot Error: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    bot.send_message(call.message.chat.id, f"PAYMENT GATEWAY\n\nSend to:\n{VAULT_ADDRESS}")

# --- WEB UI ---
DASH_HTML = """
<!DOCTYPE html>
<html>
<head><title>NEXUS</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-black text-cyan-500 font-mono p-4">
    <div class="max-w-md mx-auto border border-cyan-900 rounded-3xl p-6 bg-zinc-950">
        <h1 class="text-xl font-black italic mb-4">NEXUS_v10.7</h1>
        <div class="grid grid-cols-2 gap-3 mb-6">
            <div class="p-3 bg-cyan-950/20 border border-cyan-900 rounded-xl">
                <p class="text-[8px] text-cyan-700">VAULT</p>
                <p class="text-lg font-bold text-white"><span id="vault">0.00</span></p>
            </div>
            <div class="p-3 bg-cyan-950/20 border border-cyan-900 rounded-xl">
                <p class="text-[8px] text-cyan-700">STRIKES</p>
                <p class="text-lg font-bold text-white"><span id="scanned">0</span></p>
            </div>
        </div>
        <div class="h-48 overflow-hidden text-[10px] space-y-1" id="hits"></div>
    </div>
    <script>
        function update() {
            fetch('/api/stats').then(r => r.json()).then(data => {
                document.getElementById('vault').innerText = data.vault_balance.toFixed(2);
                document.getElementById('scanned').innerText = data.total_pools_hit;
                document.getElementById('hits').innerHTML = data.recent_hits.map(h => 
                    `<p>[${h.time}] STRIKE: ${h.token} | +${h.profit}</p>`).join('');
            });
        }
        setInterval(update, 3000); update();
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(DASH_HTML)

@app.route('/health')
def health(): return "OK", 200

@app.route('/api/stats')
def api_stats(): return jsonify(state)

# --- ENGINE ---
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            time.sleep(5)

def run_sim():
    while True:
        time.sleep(60)
        state["vault_balance"] += 0.05
        state["total_pools_hit"] += 1

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=run_sim, daemon=True).start()
    # Port must be 10000 for Render
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
