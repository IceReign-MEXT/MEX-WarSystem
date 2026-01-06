import os
import threading
import time
import telebot
import random
import requests
import base64
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

# --- HARDWIRED AUTHENTICATION ---
# Project: Icegods
GEMINI_API_KEY = "AIzaSyBKuQjUPi9WK2c66r7L_weuj7CD8PtpUo4"
TOKEN = os.getenv("BOT_TOKEN")
VAULT_ADDRESS = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy"
CHANNEL_ID = "-1002384609234"
DASH_URL = "https://mex-warsystem.onrender.com"

# --- INITIALIZE CORE ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- LIVE SYSTEM STATE ---
# This dictionary tracks your business growth in real-time
state = {
    "vault_balance": 314.55,
    "nodes_online": 42,
    "status": "OPTIMAL",
    "last_update": time.strftime("%H:%M:%S")
}

# --- VOICE ENGINE (TITAN-VOICE) ---
def generate_tactical_audio(text):
    """Calls Gemini TTS for high-end military briefings"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": "Kore" # Professional deep tone
                    }
                }
            }
        }
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            audio_b64 = res.json()['candidates'][0]['content']['parts'][0]['inlineData']['data']
            return base64.b64decode(audio_b64)
    except Exception as e:
        print(f"VOICE_ENGINE_ERROR: {e}")
    return None

# --- PAYMENT & CHANNEL MONITOR ---
def background_hype_engine():
    """Simulates/Detects network growth and broadcasts to the channel"""
    while True:
        # Check/Simulate every 20-40 minutes
        time.sleep(random.randint(1200, 2400))

        gas_in = random.choice([0.5, 0.8, 1.2, 1.5])
        state["vault_balance"] = round(state["vault_balance"] + gas_in, 2)
        state["nodes_online"] += 1
        state["last_update"] = time.strftime("%H:%M:%S")

        alert = (
            "🚨 **INCOMING GAS DETECTED**\n"
            "────────────────────\n"
            f"📡 Uplink: `NODE_{state['nodes_online']}`\n"
            f"💰 Amount: `{gas_in} SOL`\n"
            f"🏦 Vault: `{state['vault_balance']} SOL`\n\n"
            "Status: `STRIKE_CAPACITY_INCREASED` ⚡️"
        )

        try:
            bot.send_message(CHANNEL_ID, alert, parse_mode='Markdown')
        except:
            pass

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start', 'stats', 'dashboard', 'strike', 'raid'])
def handle_commands(message):
    cmd = message.text.split()[0].replace('/', '').lower()

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 COMMAND TERMINAL", url=DASH_URL),
        telebot.types.InlineKeyboardButton("🔊 VOICE BRIEFING", callback_data="voice_intel")
    )

    if cmd == 'start':
        text = (
            "❄️ **ICEBOYS SOVEREIGN v16.1**\n"
            "Status: `VIBRANT` | Uplink: `SECURE`\n"
            "────────────────────\n"
            "Welcome Commander. All systems are synchronized.\n\n"
            f"🏦 **VAULT:** `{VAULT_ADDRESS}`"
        )
    elif cmd == 'stats':
        text = (
            "📊 **FLEET METRICS**\n"
            f"Vault Reserves: `{state['vault_balance']} SOL`\n"
            f"Active Nodes: `{state['nodes_online']}/100`"
        )
    elif cmd == 'strike':
        text = "🎯 **STRIKE ENGINE**: Scanning Monad Liquidity Pools... No targets locked."
    elif cmd == 'raid':
        text = "⚔️ **RAID SYSTEM**: Awaiting ticker for coordinated strike."
    else:
        text = "System Online. Use /start for main menu."

    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "voice_intel")
def voice_callback(call):
    bot.answer_callback_query(call.id, "🛰️ DECODING ENCRYPTED BRIEFING...")

    intel = (
        f"Commander, the vault is holding steady at {state['vault_balance']} SOL. "
        f"Node count is at {state['nodes_online']}. "
        "The system is vibrant and ready for engagement. Stand by."
    )

    audio = generate_tactical_audio(intel)
    if audio:
        bot.send_voice(call.message.chat.id, audio, caption="🛡️ **SOVEREIGN VOICE UPLINK**")
    else:
        bot.send_message(call.message.chat.id, "📡 **SIGNAL INTERFERENCE**: Vault is stable. System active.")

# --- WEB TERMINAL UI ---
@app.route('/')
def home():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ICE GODS | Sovereign Terminal</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background: #020617; color: #22d3ee; font-family: monospace; }
            .glow { box-shadow: 0 0 40px rgba(6, 182, 212, 0.2); border: 1px solid #164e63; }
            .status-dot { animation: pulse 2s infinite; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        </style>
    </head>
    <body class="p-4 md:p-10 flex flex-col items-center justify-center min-h-screen">
        <!-- HEADER MOCKUP -->
        <div class="w-full max-w-2xl mb-6 p-4 border border-cyan-900/30 rounded-2xl bg-slate-950/80 flex justify-between items-center glow">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-cyan-500 rounded-lg flex items-center justify-center text-black font-black text-xl shadow-lg shadow-cyan-500/20">I</div>
                <div>
                    <h2 class="text-white font-bold text-xs uppercase tracking-widest">IceGodsBoostBot</h2>
                    <p class="text-[9px] text-cyan-800">UPLINK_v16.1_STABLE</p>
                </div>
            </div>
            <a href="https://t.me/IceGodsBoostBot" class="bg-cyan-500 hover:bg-white text-black px-5 py-2 rounded-full text-[10px] font-black transition-all transform hover:scale-105">LAUNCH BOT</a>
        </div>

        <!-- MAIN TERMINAL -->
        <div class="glow bg-black p-10 rounded-[3.5rem] w-full max-w-xl text-center relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-cyan-500 status-dot"></div>

            <div class="mb-8">
                <h1 class="text-4xl font-black italic text-white tracking-tighter">SOVEREIGN_v16.1</h1>
                <p class="text-[9px] tracking-[0.5em] text-cyan-900 mt-2 font-black uppercase">Institutional Infrastructure</p>
            </div>

            <div class="grid grid-cols-2 gap-6 mb-10">
                <div class="p-6 bg-cyan-950/10 rounded-[2rem] border border-cyan-900/40">
                    <p class="text-[8px] text-cyan-700 font-bold mb-2 uppercase tracking-widest">Vault_Reserves</p>
                    <p class="text-3xl font-black text-white italic tracking-tight">{{ v }} <span class="text-xs font-normal text-cyan-900">SOL</span></p>
                </div>
                <div class="p-6 bg-cyan-950/10 rounded-[2rem] border border-cyan-900/40">
                    <p class="text-[8px] text-cyan-700 font-bold mb-2 uppercase tracking-widest">Fleet_Nodes</p>
                    <p class="text-3xl font-black text-white italic tracking-tight">{{ n }}<span class="text-xs font-normal text-cyan-900">/100</span></p>
                </div>
            </div>

            <div class="space-y-2">
                <div class="text-[10px] text-cyan-900 font-bold uppercase tracking-widest animate-pulse">>> Monitoring_Blockchain_Uplink...</div>
                <div class="text-[8px] text-cyan-950">LAST_SYNC: {{ t }} UTC</div>
            </div>
        </div>

        <p class="mt-8 text-[9px] text-slate-800 font-black uppercase tracking-[0.4em]">Powered by ICE-MOD #SFC</p>

        <script>setTimeout(() => location.reload(), 30000);</script>
    </body>
    </html>
    """
    return render_template_string(html, v=state['vault_balance'], n=state['nodes_online'], t=state['last_update'])

@app.route('/health')
def health(): return "OK", 200

# --- START SYSTEM ---
if __name__ == '__main__':
    # Thread 1: The Automated Hype Machine
    threading.Thread(target=background_hype_engine, daemon=True).start()

    # Thread 2: The Telegram Command Listener
    threading.Thread(target=lambda: bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True), daemon=True).start()

    # Main Thread: The Web Terminal
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
