import os, threading, time, telebot, random
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# Initialize bot with a single-thread to prevent API Conflicts
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- LIVE STATE ---
VAULT = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
state = {"vault": 314.55, "scans": 12405, "nodes": 142}

# --- COMMANDS ---
@bot.message_handler(commands=['start', 'dashboard', 'strike', 'raid', 'stats', 'roadmap'])
def handle_all_commands(message):
    cmd = message.text.split()[0].replace('/', '')
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", url="https://mex-warsystem-wunb.onrender.com"))
    
    responses = {
        "start": f"⚔️ **MEX WAR-SYSTEM v12.5**\nStatus: `WEAPONIZED`\nVault: `{VAULT}`",
        "strike": "🔫 **STRIKE ENGINE**: `ACTIVE`\nTarget: `MONAD_DEVNET`\nStatus: `SCANNING_LIQUIDITY`",
        "raid": "⚔️ **RAID STATUS**: `122 COMPLETED`\nNext Target: `CALCULATING...`",
        "stats": f"📊 **STATS**\nVault: `{state['vault']} MON`\nNodes: `{state['nodes']}`",
        "roadmap": "🗺️ **ROADMAP**\nPhase 2: Global Strike Engine (ACTIVE)"
    }
    
    text = responses.get(cmd, "System Online. Use /start to view menu.")
    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=markup)

# --- WEB DASHBOARD ---
@app.route('/')
def home():
    return render_template_string("""
    <body style="background:#000;color:#0f0;font-family:monospace;padding:40px;text-align:center;">
        <h1 style="border:1px solid #0f0;padding:20px;display:inline-block;">NEXUS_WAR_TERMINAL_v12.5</h1>
        <div style="margin-top:20px;">
            <p>SYSTEM_STATUS: <span style="color:#fff;">VIBRANT</span></p>
            <p>VAULT_RESERVE: <span style="color:#fff;">{{v}} MON</span></p>
            <p>ACTIVE_STRIKES: <span style="color:#fff;">{{s}}</span></p>
        </div>
        <script>setTimeout(()=>location.reload(), 5000)</script>
    </body>
    """, v=state['vault'], s=state['scans'])

@app.route('/health')
def health(): return "OK", 200

# --- RUNNERS ---
def run_bot():
    print("LOG: Starting Bot Polling...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    print(f"LOG: Starting Web Server on Port {PORT}...")
    app.run(host='0.0.0.0', port=PORT)
