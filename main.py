import os, threading, time, telebot, random
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- SYSTEM DATABASE (State) ---
VAULT = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
state = {
    "vault_balance": 314.15,
    "total_scanned": 12405,
    "active_snipers": 84,
    "raids_completed": 122
}

# --- BOT COMMANDS (RESTORED) ---

@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", url="https://mex-warsystem-wunb.onrender.com"))
    msg = "⚔️ **MEX WAR-SYSTEM v10.8**\nStatus: `ACTIVE`\n\nCommands: /strike, /snipers, /raid, /stats, /roadmap"
    bot.reply_to(message, msg, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['strike', 'snipers'])
def cmd_snipers(message):
    msg = (
        "🔫 **SNIPER ENGINE STATUS**\n"
        "────────────────────\n"
        f"Active Nodes: `{state['active_snipers']}`\n"
        "Targeting: `MONAD_TESTNET`\n"
        "Status: `WAITING_FOR_LIQUIDITY`\n\n"
        "Type /raid to join the current strike."
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['raid'])
def cmd_raid(message):
    msg = (
        "⚔️ **RAID IN PROGRESS**\n"
        "────────────────────\n"
        f"Total Raiders: `412`\n"
        f"Successful Raids: `{state['raids_completed']}`\n\n"
        "Target: `0x...` (Scanning...)\n"
        "Support the war: @ICEGODSICEDEVILS"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    msg = (
        "📊 **WAR STATISTICS**\n"
        "────────────────────\n"
        f"Vault: `{state['vault_balance']} MON`\n"
        f"Pools Scanned: `{state['total_scanned']}`\n"
        f"Total Users: `1.2k`"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['roadmap'])
def cmd_roadmap(message):
    msg = (
        "🗺️ **NEXUS ROADMAP**\n"
        "────────────────────\n"
        "Phase 1: Terminal Launch (DONE)\n"
        "Phase 2: Global Strike Engine (ACTIVE)\n"
        "Phase 3: Multi-Chain Dominance (Q1 2026)"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

# --- WEB DASHBOARD ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>NEXUS TERMINAL</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-black text-emerald-500 font-mono flex flex-col items-center justify-center min-h-screen p-4">
    <div class="border border-emerald-900 p-8 rounded-3xl bg-zinc-950 shadow-[0_0_50px_rgba(16,185,129,0.1)] w-full max-w-sm">
        <h1 class="text-2xl font-black italic mb-6 tracking-tighter">MEX_WAR.SYS</h1>
        <div class="space-y-4">
            <div class="bg-black p-4 rounded-xl border border-emerald-900/40">
                <p class="text-[10px] text-emerald-800 font-bold uppercase">Vault_Reserves</p>
                <p class="text-xl font-bold text-white" id="vault">{{ vault_balance }} MON</p>
            </div>
            <div class="bg-black p-4 rounded-xl border border-emerald-900/40">
                <p class="text-[10px] text-emerald-800 font-bold uppercase">System_Strikes</p>
                <p class="text-xl font-bold text-white" id="scan">{{ total_scanned }}</p>
            </div>
        </div>
        <div class="mt-6 text-[9px] text-emerald-900 animate-pulse text-center">
            >> SYSTEM_CONNECTED_TO_MONAD_MAIN_NODE
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home(): 
    return render_template_string(DASHBOARD_HTML, **state)

@app.route('/health')
def health(): return "OK", 200

def run_bot():
    while True:
        try: bot.polling(none_stop=True, interval=1, timeout=20)
        except: time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
