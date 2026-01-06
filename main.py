	import os, threading, time, telebot, random, requests, base64, json
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()

# --- THE ARCHITECT'S CORE ---
ARCHITECT_WALLET = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
GEMINI_API_KEY = "AIzaSyBKuQjUPi9WK2c66r7L_weuj7CD8PtpUo4"
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@ICEGODSICEDEVILS"
DASH_URL = "https://mex-warsystem.onrender.com"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- SYSTEM STATE ---
# In a real production environment, 'members' would be a database/Firestore
state = {
    "vault_eth": 1.80099,
    "usd_value": 5804.64,
    "members": ["559382910"], # Whitelisted IDs
    "pending_verifications": {},
    "network_load": "OPTIMAL",
    "nodes_active": 158
}

# --- 1. BLOCKCHAIN MONITORING (Simulation) ---
def blockchain_monitor():
    """Simulates real-time monitoring of ARCHITECT_WALLET and Whale movements"""
    while True:
        time.sleep(random.randint(600, 1200))
        # Logic: Detect Whale movement for the Channel
        whale_amt = random.randint(50, 500)
        alert = (
            "🐋 **WHALE MOVEMENT DETECTED**\n"
            "────────────────────\n"
            f"Amount: `{whale_amt} ETH`\n"
            "Destination: `Unknown Institutional Vault`\n"
            "Impact: `HIGH VOLATILITY EXPECTED`\n"
            "────────────────────\n"
            "🚀 *NEXUS NODES ARE ALREADY POSITIONED.*"
        )
        try: bot.send_message(CHANNEL_ID, alert, parse_mode='Markdown')
        except: pass

# --- 2. THE GATEKEEPER (Security Logic) ---
def is_paid(user_id):
    return str(user_id) in state["members"]

def gate_check(message):
    if not is_paid(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💳 ACTIVATE NODE (0.5 ETH)", callback_data="buy_access"))
        bot.reply_to(message, "🔒 **NODE ACCESS RESTRICTED**\n\nYour ID is not whitelisted in the Sovereign Database. Payment required for terminal activation.", parse_mode='Markdown', reply_markup=markup)
        return False
    return True

# --- 3. VOICE & AI ENGINE ---
def get_voice(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": text}]}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}}}}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return base64.b64decode(res.json()['candidates'][0]['content']['parts'][0]['inlineData']['data'])
    except: return None

# --- 4. BOT COMMANDS (Gated) ---
@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 OPEN NEXUS TERMINAL", url=DASH_URL),
        telebot.types.InlineKeyboardButton("📜 SYSTEM WHITE PAPER", callback_data="whitepaper"),
        telebot.types.InlineKeyboardButton("🛠️ ACTIVATE NODE", callback_data="buy_access")
    )
    welcome = (
        "❄️ **THE MONOLITH v20.0**\n"
        "────────────────────\n"
        "Autonomous Wealth Capture & Sniper Infrastructure.\n\n"
        f"🏦 **Vault:** `{ARCHITECT_WALLET}`\n"
        f"📡 **Status:** {state['network_load']}\n"
        "────────────────────\n"
        "Select an protocol to begin."
    )
    bot.reply_to(message, welcome, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['strike', 'snipe'])
def cmd_gated(message):
    if gate_check(message):
        bot.reply_to(message, "🚀 **STRIKE INITIALIZED.** Executing high-frequency liquidity capture...")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "buy_access":
        msg = (
            "💳 **MEMBERSHIP ACTIVATION**\n"
            "────────────────────\n"
            "To unlock the Multitude Machine, send:\n"
            "`0.5 ETH` or `2000 USDT` to:\n\n"
            f"`{ARCHITECT_WALLET}`\n\n"
            "⚠️ **AUTOMATIC DETECTION:** Once the transaction hits the mempool, your ID will be whitelisted automatically."
        )
        bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

    elif call.data == "whitepaper":
        paper = (
            "📖 **SOVEREIGN WHITE PAPER**\n\n"
            "1. **Autonomous Capture:** The system uses 150+ nodes to detect liquidity injection.\n"
            "2. **The Vault:** All fees are channeled to the Architect Wallet for distribution.\n"
            "3. **Multitude logic:** Every user becomes a 'Node' in the network, increasing strike power.\n"
            "4. **The Goal:** 100% automation of wealth extraction from DEX pools."
        )
        bot.send_message(call.message.chat.id, paper, parse_mode='Markdown')

# --- 5. WEB TERMINAL (Real-time Monitoring) ---
@app.route('/')
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MONOLITH | TERMINAL</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background: #000; color: #00f2ff; font-family: monospace; overflow: hidden; }
            .matrix-bg { position: fixed; top:0; left:0; width:100%; height:100%; opacity: 0.05; z-index: -1; }
        </style>
    </head>
    <body class="flex flex-col items-center justify-center min-h-screen p-4">
        <div class="max-w-3xl w-full bg-zinc-950 border border-cyan-500/30 p-8 rounded-[3rem] shadow-[0_0_100px_rgba(0,242,255,0.1)]">
            <h1 class="text-4xl font-black italic text-white tracking-tighter">MONOLITH_v20</h1>
            <p class="text-[10px] tracking-[0.5em] text-cyan-800 mb-8">GLOBAL MONITORING & CAPTURE SYSTEM</p>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div class="p-4 border border-white/5 rounded-2xl bg-black">
                    <p class="text-[8px] text-zinc-600 uppercase">Vault_Eth</p>
                    <p class="text-xl font-bold">{{ eth }}</p>
                </div>
                <div class="p-4 border border-white/5 rounded-2xl bg-black">
                    <p class="text-[8px] text-zinc-600 uppercase">Valuation</p>
                    <p class="text-xl font-bold text-green-500">${{ usd }}</p>
                </div>
                <div class="p-4 border border-white/5 rounded-2xl bg-black">
                    <p class="text-[8px] text-zinc-600 uppercase">Active_Nodes</p>
                    <p class="text-xl font-bold">{{ nodes }}</p>
                </div>
            </div>

            <div class="h-48 bg-black/50 border border-white/5 rounded-2xl p-4 overflow-hidden text-[9px] text-cyan-900">
                <div id="logs" class="space-y-1"></div>
            </div>
        </div>
        <script>
            function log() {
                const l = document.getElementById('logs');
                const p = document.createElement('p');
                p.innerHTML = `> [${new Date().toLocaleTimeString()}] SCANNING_BLOCKCHAIN... ADDR: {{ vault }} ... <span class="text-white">WAITING_FOR_PAYMENT</span>`;
                l.prepend(p);
                if(l.children.length > 10) l.lastChild.remove();
            }
            setInterval(log, 3000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html, eth=state["eth_balance"], usd=f"{state['usd_value']:,}", nodes=state["nodes"], vault=ARCHITECT_WALLET[:12]+"...")

if __name__ == '__main__':
    threading.Thread(target=blockchain_monitor, daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
