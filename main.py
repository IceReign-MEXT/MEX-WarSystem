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

OPERATOR = "Mex Robert"
VAULT = os.getenv("ADMIN_WALLET", "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F")
# Global state for the "Live Strike" animation
last_strike_time = 0

# --- TELEGRAM LOGIC ---
@bot.message_handler(commands=['start', 'status'])
def handle_start(message):
    response = (
        "❄️ *ICE GODS WAR-SYSTEM v4.0*\n"
        "────────────────────\n"
        f"👤 *Operator:* {OPERATOR}\n"
        "🛰️ *Status:* ONLINE\n"
        f"🏦 *Vault:* `{VAULT}`\n"
        "🔗 [LIVE DASHBOARD](https://mex-warsystem-wunb.onrender.com)\n"
        "────────────────────\n"
        "Ready for volume strikes. Send /strike to begin."
    )
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['strike'])
def handle_strike(message):
    global last_strike_time
    last_strike_time = time.time() # This triggers the animation on the web
    bot.reply_to(message, "🚀 *STRIKE INITIATED:* Injecting volume into Monad Testnet...\n\n_Check the Dashboard for live logs!_", parse_mode='Markdown')

# --- WEB UI WITH LIVE LOGS ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ICE GODS | @IceGodsBoost_Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #020617; color: #22d3ee; font-family: monospace; }
        .neon-border { border: 1px solid #06b6d4; box-shadow: 0 0 15px #06b6d4; }
        .strike-active { background: rgba(6, 182, 212, 0.2); border-color: #f0f; box-shadow: 0 0 25px #f0f; }
    </style>
</head>
<body class="p-4 md:p-10 flex flex-col items-center justify-center min-h-screen">
    <div id="status-card" class="max-w-3xl w-full neon-border bg-black p-8 rounded-3xl text-center transition-all duration-500">
        <h1 class="text-4xl font-black text-white">ICE GODS BOOST</h1>
        <p class="text-cyan-600 mb-2 uppercase tracking-widest">Bot: @IceGodsBoost_Bot</p>
        
        <div class="grid grid-cols-2 gap-4 my-6">
            <div class="bg-slate-900 p-4 rounded-xl">
                <p class="text-[10px] text-slate-500">LAST STRIKE</p>
                <p id="strike-clock" class="text-xl font-bold">NEVER</p>
            </div>
            <div class="bg-slate-900 p-4 rounded-xl">
                <p class="text-[10px] text-slate-500">VAULT YIELD</p>
                <p class="text-xl font-bold">2.0% TAX</p>
            </div>
        </div>

        <div id="logs" class="text-left bg-black p-6 rounded-2xl text-[10px] text-cyan-500 font-mono space-y-1 h-48 overflow-y-hidden border border-cyan-900/30">
            <p>> [SYSTEM] WAITING FOR OPERATOR COMMAND...</p>
        </div>
    </div>

    <script>
        let lastStrike = 0;
        function checkStrike() {
            fetch('/strike_data').then(res => res.json()).then(data => {
                if(data.time > lastStrike) {
                    lastStrike = data.time;
                    triggerAnimation();
                }
            });
        }

        function triggerAnimation() {
            const card = document.getElementById('status-card');
            const logs = document.getElementById('logs');
            const clock = document.getElementById('strike-clock');
            
            card.classList.add('strike-active');
            clock.innerText = "JUST NOW";
            
            const p = document.createElement('p');
            p.className = "text-white font-bold animate-pulse";
            p.innerHTML = "> [" + new Date().toLocaleTimeString() + "] 🔥 VOLUME STRIKE INJECTED BY OPERATOR";
            logs.prepend(p);
            
            setTimeout(() => {
                card.classList.remove('strike-active');
            }, 5000);
        }

        setInterval(checkStrike, 2000);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML, operator=OPERATOR, vault=VAULT)

@app.route('/strike_data')
def strike_data():
    return jsonify({"time": last_strike_time})

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
