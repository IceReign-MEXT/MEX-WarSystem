import os, threading, time, telebot, random, requests, base64
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
GEMINI_API_KEY = "AIzaSyBKuQjUPi9WK2c66r7L_weuj7CD8PtpUo4"
TOKEN = os.getenv("BOT_TOKEN")
VAULT = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- STATE ---
state = {"vault": 314.55, "nodes": 42}

# --- VOICE ENGINE ---
def generate_tactical_audio(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}}
        }
    }
    try:
        res = requests.post(url, json=payload, timeout=12)
        if res.status_code == 200:
            audio_b64 = res.json()['candidates'][0]['content']['parts'][0]['inlineData']['data']
            return base64.b64decode(audio_b64)
    except:
        return None

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 LIVE TERMINAL", url="https://mex-warsystem.onrender.com"),
        telebot.types.InlineKeyboardButton("🔊 VOICE BRIEFING", callback_data="voice_intel")
    )
    bot.reply_to(message, "❄️ **ICEBOYS SOVEREIGN v15.4**\nSystem Online.", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "voice_intel")
def voice_callback(call):
    bot.answer_callback_query(call.id, "🛰️ DECODING...")
    audio = generate_tactical_audio(f"Commander, vault balance is {state['vault']} SOL. Fleet is vibrant.")
    if audio:
        bot.send_voice(call.message.chat.id, audio, caption="🛡️ **SOVEREIGN VOICE UPLINK**")
    else:
        bot.send_message(call.message.chat.id, "📡 **SIGNAL WEAK.** Try again.")

# --- FULL DASHBOARD HTML ---
@app.route('/')
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>ICE GODS | Sovereign Terminal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #020617; color: #22d3ee; font-family: monospace; }
        .glow { box-shadow: 0 0 20px rgba(34, 211, 238, 0.2); border: 1px solid rgba(34, 211, 238, 0.4); }
    </style>
</head>
<body class="p-4 flex flex-col items-center justify-center min-h-screen">
    <div class="w-full max-w-2xl mb-6 p-4 border border-cyan-900/30 rounded-xl bg-slate-900/50 flex justify-between items-center">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-cyan-500 rounded-lg flex items-center justify-center text-black font-black text-xl">I</div>
            <h2 class="text-white font-bold text-sm tracking-widest">ICEGODS_BOOST_BOT</h2>
        </div>
        <a href="https://t.me/IceGodsBoostBot" class="bg-cyan-500 text-black px-4 py-2 rounded-full text-xs font-black">LAUNCH BOT</a>
    </div>
    <div class="glow bg-black p-10 rounded-[3rem] w-full max-w-xl text-center">
        <h1 class="text-4xl font-black italic mb-2 text-white">SOVEREIGN_v15.4</h1>
        <p class="text-[10px] tracking-[0.5em] mb-10 text-cyan-800 uppercase font-bold">Monad Strike Infrastructure</p>
        <div class="grid grid-cols-2 gap-4 mb-8">
            <div class="p-4 bg-cyan-950/20 rounded-2xl border border-cyan-900/50">
                <p class="text-[9px] text-cyan-700 font-bold mb-1">VAULT_RESERVE</p>
                <p class="text-2xl font-bold text-white">{{ v }} SOL</p>
            </div>
            <div class="p-4 bg-cyan-950/20 rounded-2xl border border-cyan-900/50">
                <p class="text-[9px] text-cyan-700 font-bold mb-1">ACTIVE_NODES</p>
                <p class="text-2xl font-bold text-white">{{ n }}/42</p>
            </div>
        </div>
        <div class="text-[10px] text-cyan-900 animate-pulse">>> MONITORING_SOLANA_MAINNET_WSS...</div>
    </div>
    <script>setTimeout(()=>location.reload(), 5000)</script>
</body>
</html>
    """, v=state['vault'], n=state['nodes_online'] if "nodes_online" in state else state['nodes'])

@app.route('/health')
def health(): return "OK", 200

if __name__ == '__main__':
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
