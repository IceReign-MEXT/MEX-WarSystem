import os, threading, time, telebot, random, requests, base64
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
# YOUR ACTUAL RENDER URL
DASH_URL = "https://mex-warsystem.onrender.com"
VAULT = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy"
# Your Channel IDs
CHANNEL_ID = "-1002384609234" 

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- SYSTEM STATE ---
state = {
    "vault_balance": 314.55,
    "nodes_online": 42,
    "status": "OPTIMAL",
    "last_tx": "None"
}

# --- AUDIO GENERATION (TTS) ---
def get_audio_benefit(text):
    """Generates a professional voice briefing using Gemini TTS"""
    api_key = "" # Environment provides this
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": f"Commander, here is your update: {text}"}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}}
        }
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        audio_data = res.json()['candidates'][0]['content']['parts'][0]['inlineData']['data']
        return base64.b64decode(audio_data)
    except:
        return None

# --- BOT COMMANDS ---
@bot.message_handler(commands=['start', 'dashboard'])
def cmd_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌐 LIVE DASHBOARD", url=DASH_URL))
    markup.add(telebot.types.InlineKeyboardButton("🔊 VOICE BRIEFING", callback_data="get_audio"))
    
    msg = (
        "❄️ **ICEBOYS SOVEREIGN V15.1**\n"
        "Status: `OPTIMAL` | Nodes: `42/42`\n"
        "────────────────────\n"
        "Institutional engine online. Commander, select sequence.\n\n"
        f"🏦 **VAULT:** `{VAULT}`"
    )
    bot.reply_to(message, msg, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "get_audio")
def audio_callback(call):
    bot.answer_callback_query(call.id, "Generating Tactical Audio...")
    audio = get_audio_benefit(f"The sovereign fleet is synchronized. Vault balance is {state['vault_balance']} SOL. Standing by for engagement.")
    if audio:
        bot.send_voice(call.message.chat.id, audio, caption="🛡️ **SOVEREIGN VOICE UPLINK**")
    else:
        bot.send_message(call.message.chat.id, "❌ **UPLINK TIMEOUT:** Signal weak. Try again.")

# --- AUTO-DETECTION SIMULATOR (Broadcasting to Group) ---
def auto_detector():
    while True:
        time.sleep(random.randint(600, 1200)) # Randomly detect "payments"
        amt = random.choice([0.5, 0.8, 1.5])
        state["vault_balance"] += amt
        
        alert = (
            "🚨 **INCOMING GAS DETECTED**\n"
            "────────────────────\n"
            f"Amount: `{amt} SOL`\n"
            "Action: `NODE_ACTIVATION`\n"
            "Status: `ENGAGING_RAYDIUM_LP`"
        )
        try:
            bot.send_message(CHANNEL_ID, alert, parse_mode='Markdown')
        except:
            pass

# --- DASHBOARD HTML ---
@app.route('/')
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head><title>ICEBOYS TERMINAL</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-black text-cyan-500 font-mono p-10 flex flex-col items-center justify-center min-h-screen">
        <div class="border-2 border-cyan-900 p-10 rounded-[3rem] bg-zinc-950 shadow-[0_0_50px_rgba(0,255,255,0.1)]">
            <h1 class="text-3xl font-black italic mb-6">ICEBOYS_SOVEREIGN</h1>
            <div class="grid grid-cols-2 gap-6">
                <div class="p-4 bg-cyan-950/20 rounded-2xl border border-cyan-900">
                    <p class="text-[10px] text-cyan-700 font-bold">VAULT_TOTAL</p>
                    <p class="text-2xl font-bold text-white">{{ v }} SOL</p>
                </div>
                <div class="p-4 bg-cyan-950/20 rounded-2xl border border-cyan-900">
                    <p class="text-[10px] text-cyan-700 font-bold">FLEET_NODES</p>
                    <p class="text-2xl font-bold text-white">{{ n }}</p>
                </div>
            </div>
            <p class="mt-8 text-center text-[10px] animate-pulse">>> MONITORING_SOLANA_MAINNET_WSS...</p>
        </div>
        <script>setTimeout(()=>location.reload(), 5000)</script>
    </body>
    """, v=state['vault_balance'], n=state['nodes_online'])

@app.route('/health')
def health(): return "OK", 200

if __name__ == '__main__':
    threading.Thread(target=auto_detector, daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
