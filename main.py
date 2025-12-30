import os
import threading
import telebot
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

OPERATOR = "Mex Robert"
VAULT = os.getenv("ADMIN_WALLET", "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F")

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
    bot.reply_to(message, "🚀 *STRIKE INITIATED:* Injecting volume into Monad Testnet...", parse_mode='Markdown')

# --- WEB UI ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ICE GODS | @IceGodsBoost_Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #020617; color: #22d3ee; font-family: monospace; }
        .neon-border { border: 1px solid #06b6d4; box-shadow: 0 0 15px #06b6d4; }
    </style>
</head>
<body class="p-10 flex items-center justify-center min-h-screen">
    <div class="max-w-2xl w-full neon-border bg-black p-8 rounded-3xl text-center">
        <h1 class="text-4xl font-black text-white">ICE GODS BOOST</h1>
        <p class="text-cyan-600 mb-2 uppercase tracking-widest">Bot: @IceGodsBoost_Bot</p>
        <p class="text-xs text-slate-500 mb-8 uppercase">Operator: {{ operator }}</p>
        <div class="text-left bg-slate-900/50 p-6 rounded-2xl text-[10px] text-cyan-400 font-mono space-y-1">
            <p>> [BOT] TELEGRAM_POLLING_ACTIVE</p>
            <p>> [WEB] DASHBOARD_ONLINE</p>
            <p>> [NET] MONAD_TESTNET_BRIDGE_STABLE</p>
            <p>> [VAULT] {{ vault }}</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML, operator=OPERATOR, vault=VAULT)

def run_bot():
    print("📡 Bot Polling started...")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
