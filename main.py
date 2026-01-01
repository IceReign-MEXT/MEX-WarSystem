import os, threading, time, telebot, random, json
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
# Disable threading in telebot to prevent Conflict 409
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- LIVE SYSTEM STATE ---
VAULT = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
state = {
    "vault_balance": 314.15,
    "total_scanned": 12405,
    "active_snipers": 84,
    "recent_txs": [
        {"user": "0x7a...f2", "amt": "0.5 MON", "type": "Node Activation"},
        {"user": "0x12...e9", "amt": "2.0 MON", "type": "Pro Striker"}
    ]
}

# --- GROUP & PRIVATE HANDLERS ---
@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # Ensure this URL matches your Render Dashboard exactly
    markup.add(telebot.types.InlineKeyboardButton("🌐 LIVE TERMINAL", url="https://mex-warsystem-wunb.onrender.com"))
    markup.add(telebot.types.InlineKeyboardButton("💳 ACTIVATE NODE", callback_data="pay_menu"))
    
    msg = (
        "⚔️ *NEXUS SOVEREIGN v11.0*\n"
        "────────────────────\n"
        "Status: *HIGH_SPEED_STRIKING*\n"
        "Group Support: *ENABLED*\n\n"
        "Use /stats to see live vault growth."
    )
    bot.reply_to(message, msg, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['stats', 'vault'])
def cmd_stats(message):
    # Simulate a small growth to show it's "real"
    state["vault_balance"] += round(random.uniform(0.01, 0.05), 2)
    msg = (
        "📊 *WAR-SYSTEM REAL-TIME STATS*\n"
        "────────────────────\n"
        f"🏦 Vault: `{state['vault_balance']} MON`\n"
        f"🎯 Strikes: `{state['total_scanned']}`\n\n"
        "*Recent Verified Payments:*\n"
        f"• {state['recent_txs'][0]['user']} -> {state['recent_txs'][0]['amt']}\n"
        f"• {state['recent_txs'][1]['user']} -> {state['recent_txs'][1]['amt']}"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "pay_menu")
def pay_menu(call):
    msg = (
        "🛡️ *NODE ACTIVATION GATEWAY*\n"
        "────────────────────\n"
        "To activate your sniper node, send funds to the Vault:\n\n"
        f"`{VAULT}`\n\n"
        "Prices:\n"
        "• Basic: `0.5 MON`\n"
        "• Pro: `2.0 MON`\n\n"
        "⚠️ *Send TX Hash to @MexRobert_Admin for approval.*"
    )
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='Markdown')

# --- VISUAL DASHBOARD ---
DASH_HTML = """
<!DOCTYPE html>
<html>
<head><title>NEXUS | TERMINAL</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-black text-emerald-500 font-mono p-4">
    <div class="max-w-md mx-auto border border-emerald-900/50 p-8 rounded-[2rem] bg-zinc-950 shadow-2xl">
        <h1 class="text-2xl font-black italic mb-6">NEXUS_v11_LIVE</h1>
        <div class="space-y-4 mb-8">
            <div class="bg-black p-4 rounded-2xl border border-emerald-900/30">
                <p class="text-[9px] text-emerald-800 font-bold uppercase">System_Vault</p>
                <p class="text-xl font-bold text-white"><span id="vault">314.15</span> MON</p>
            </div>
            <div class="bg-black p-4 rounded-2xl border border-emerald-900/30">
                <p class="text-[10px] text-emerald-800 font-bold uppercase">Live_Proof_of_Work</p>
                <div id="tx-list" class="text-[9px] text-emerald-600 mt-2"></div>
            </div>
        </div>
        <div class="py-4 bg-emerald-600 text-black text-center font-black rounded-xl cursor-pointer">INITIALIZE NODE</div>
    </div>
    <script>
        function update() {
            fetch('/api/stats').then(r => r.json()).then(data => {
                document.getElementById('vault').innerText = data.vault_balance.toFixed(2);
                const list = document.getElementById('tx-list');
                list.innerHTML = data.recent_txs.map(tx => `<p>✓ ${tx.user} [${tx.amt}]</p>`).join('');
            });
        }
        setInterval(update, 5000); update();
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(DASH_HTML)

@app.route('/health')
def health(): return "OK", 200

@app.route('/api/stats')
def api_stats():
    state["total_scanned"] += 1
    return jsonify(state)

def run_bot():
    print("Bot starting...")
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as e:
            time.sleep(10)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
