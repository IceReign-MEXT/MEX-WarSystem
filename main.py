import os, threading, time, telebot, random, requests, base64
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

# --- HARDWIRED AUTH (Project: Icegods) ---
GEMINI_API_KEY = "AIzaSyBKuQjUPi9WK2c66r7L_weuj7CD8PtpUo4"
TOKEN = os.getenv("BOT_TOKEN")
DASH_URL = "https://mex-warsystem.onrender.com"
VAULT = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- STATE ---
state = {"vault": 314.55, "nodes": 42}

def generate_tactical_audio(text):
    """Direct Uplink to Gemini TTS Engine"""
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
    except Exception as e:
        print(f"DEBUG: Audio Fail - {e}")
    return None

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 LIVE TERMINAL", url=DASH_URL),
        telebot.types.InlineKeyboardButton("🔊 VOICE BRIEFING", callback_data="voice_intel")
    )
    msg = (
        "❄️ **ICEBOYS SOVEREIGN v15.3**\n"
        "Uplink: `ENCRYPTED` | Status: `OPTIMAL`\n"
        "────────────────────\n"
        "Voice engine active. Awaiting authorization.\n\n"
        f"🏦 **VAULT:** `{VAULT}`"
    )
    bot.reply_to(message, msg, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "voice_intel")
def voice_callback(call):
    bot.answer_callback_query(call.id, "🛰️ DECODING VOICE UPLINK...")
    intel = f"Commander, the vault is secure at {state['vault']} SOL. All nodes are reporting peak signal. System is vibrant."
    audio = generate_tactical_audio(intel)
    if audio:
        bot.send_voice(call.message.chat.id, audio, caption="🛡️ **SOVEREIGN VOICE UPLINK**")
    else:
        bot.send_message(call.message.chat.id, "❌ **UPLINK TIMEOUT.** (Signal Weak)")

@app.route('/')
def home(): return "ICE_GODS_TERMINAL_ONLINE"

@app.route('/health')
def health(): return "OK", 200

if __name__ == '__main__':
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
