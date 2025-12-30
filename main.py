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

# --- CONFIG & BRANDING ---
OPERATOR = "Mex Robert"
MY_CHANNEL = "https://t.me/ICEGODSICEDEVILS"
VAULT = os.getenv("ADMIN_WALLET", "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F")

# --- EMPIRE STATE ---
empire_data = {
    "status": "SCANNING_DEX",
    "active_pools": ["WETH/MON", "USDC/MON", "IBS/WETH"],
    "total_sniped": 142,
    "revenue_24h": 1.84,
    "roadmap_progress": 88,
    "last_event": "Initializing Global Dex-Bridge..."
}

# --- TELEGRAM COMMANDS ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome = (
        "❄️ *ICE GODS EMPIRE: WAR-SYSTEM v5.0*\n"
        "────────────────────\n"
        "The Builder has initiated the Global Nexus.\n\n"
        "📊  - Access live terminal\n"
        "🎯  - High-frequency volume injection\n"
        "🔫  - View active pool snipers\n"
        "🗺️  - View project evolution\n"
        "────────────────────\n"
        "📢 *OFFICIAL CHANNEL:* [JOIN NOW](" + MY_CHANNEL + ")\n"
        "────────────────────\n"
        "_This system is exclusive. Famo-style users are barred._"
    )
    bot.reply_to(message, welcome, parse_mode='Markdown', disable_web_page_preview=True)

@bot.message_handler(commands=['dashboard'])
def send_dash(message):
    bot.reply_to(message, f"🌐 *LIVE TERMINAL:* https://mex-warsystem-wunb.onrender.com\n\n_Monitor the war in real-time._")

@bot.message_handler(commands=['roadmap'])
def roadmap(message):
    road = (
        "🗺️ *WAR-SYSTEM ROADMAP*\n"
        "────────────────────\n"
        "✅ v1: Bot Architecture\n"
        "✅ v2: Web Dashboard\n"
        "✅ v3: Nexus Revenue Capture\n"
        "🚀 v4: Multi-Pool Sniper (ACTIVE)\n"
        "🔥 v5: Automated Dex-Listing Strike\n"
        "────────────────────\n"
        "Builder: Mex Robert"
    )
    bot.reply_to(message, road, parse_mode='Markdown')

# --- WEB TERMINAL (THE EMPIRE VIEW) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ICE GODS | GLOBAL NEXUS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
        body { background: #000; color: #00ffcc; font-family: 'JetBrains Mono', monospace; }
        .border-glow { border: 1px solid #00ffcc; box-shadow: 0 0 10px #00ffcc; }
        .roadmap-bar { height: 4px; background: #111; position: relative; overflow: hidden; }
        .roadmap-fill { height: 100%; background: #00ffcc; box-shadow: 0 0 10px #00ffcc; }
    </style>
</head>
<body class="p-4 md:p-10">
    <div class="max-w-6xl mx-auto">
        <header class="flex justify-between items-center border-b border-gray-800 pb-5 mb-8">
            <div>
                <h1 class="text-3xl font-black italic tracking-tighter">ICE GODS <span class="text-white">NEXUS</span></h1>
                <p class="text-[10px] text-gray-500 uppercase tracking-widest">Operator: {{ operator }}</p>
            </div>
            <a href="""" + MY_CHANNEL + """" class="bg-cyan-900/30 border border-cyan-500/50 px-4 py-2 rounded-full text-[10px] hover:bg-cyan-500 hover:text-black transition">JOIN CHANNEL</a>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="border-glow bg-black/50 p-6 rounded-2xl">
                <p class="text-[10px] text-gray-500 mb-1">SNIPER_TOTAL</p>
                <p id="total-sniped" class="text-2xl font-bold">142</p>
            </div>
            <div class="border-glow bg-black/50 p-6 rounded-2xl">
                <p class="text-[10px] text-gray-500 mb-1">24H_REVENUE</p>
                <p class="text-2xl font-bold text-white"><span id="rev">1.84</span> MON</p>
            </div>
            <div class="md:col-span-2 border-glow bg-black/50 p-6 rounded-2xl">
                <p class="text-[10px] text-gray-500 mb-1">ROADMAP_v5_PROGRESS</p>
                <div class="roadmap-bar mt-3"><div class="roadmap-fill" style="width: 88%"></div></div>
                <p class="text-[10px] text-right mt-1 text-cyan-700">88% COMPLETE</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="md:col-span-2 border border-gray-800 bg-gray-900/10 p-6 rounded-2xl h-96 overflow-hidden relative">
                <h3 class="text-xs font-bold mb-4 opacity-50">REAL-TIME DATA STREAM</h3>
                <div id="logs" class="text-[10px] space-y-2">
                    <p class="text-cyan-800">> NEXUS v5.0 ONLINE...</p>
                </div>
            </div>
            <div class="border border-gray-800 bg-gray-900/10 p-6 rounded-2xl">
                <h3 class="text-xs font-bold mb-4 opacity-50">ACTIVE POOLS</h3>
                <div id="pools" class="text-[10px] space-y-3">
                    <div class="flex justify-between border-b border-gray-800 pb-2"><span>WETH/MON</span><span class="text-green-500">LIVE</span></div>
                    <div class="flex justify-between border-b border-gray-800 pb-2"><span>USDC/MON</span><span class="text-green-500">LIVE</span></div>
                    <div class="flex justify-between border-b border-gray-800 pb-2"><span>IBS/WETH</span><span class="text-yellow-500">SCANNING</span></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function update() {
            fetch('/api/v1/nexus').then(r => r.json()).then(data => {
                document.getElementById('total-sniped').innerText = data.total_sniped;
                document.getElementById('rev').innerText = data.revenue_24h.toFixed(2);
                
                const l = document.getElementById('logs');
                const p = document.createElement('p');
                p.innerHTML = "> [" + new Date().toLocaleTimeString() + "] " + data.last_event;
                l.prepend(p);
                if(l.children.length > 15) l.lastChild.remove();
            });
        }

        setInterval(update, 3000);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML, operator=OPERATOR)

@app.route('/api/v1/nexus')
def api():
    global empire_data
    events = [
        "Sniper bot triggered on WETH pool",
        "Volume Strike confirmed: +0.45 MON",
        "Tax Revenue routed to Vault",
        "Scanning Monad Testnet for New Listings...",
        "Roadmap v5: Updating Liquidity Bridge",
        "Bot Intelligence training on Pool 0x...A1"
    ]
    empire_data["last_event"] = random.choice(events)
    empire_data["total_sniped"] += random.randint(0, 1)
    empire_data["revenue_24h"] += random.uniform(0.01, 0.05)
    return jsonify(empire_data)

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
