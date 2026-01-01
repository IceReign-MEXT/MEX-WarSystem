import os, threading, time, telebot
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Shared Data
system_data = {
    "status": "OPERATIONAL",
    "vault_balance": "314.15 MON",
    "total_scanned": 12405,
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", url="https://mex-warsystem-wunb.onrender.com"))
    bot.reply_to(message, "⚔️ MEX WAR-SYSTEM ONLINE\nNexus Terminal v10.7 is active.", reply_markup=markup)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>MEX WAR-SYSTEM</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-black text-emerald-500 font-mono flex items-center justify-center min-h-screen">
    <div class="border border-emerald-900 p-8 rounded-3xl bg-zinc-900 shadow-2xl w-80">
        <h1 class="text-xl font-bold italic mb-4">MEX_WAR.SYS</h1>
        <div class="space-y-4">
            <div class="bg-black p-3 rounded-lg border border-emerald-900/50">
                <p class="text-[10px] text-emerald-700">VAULT_BALANCE</p>
                <p class="text-white font-bold" id="vault">314.15 MON</p>
            </div>
            <div class="bg-black p-3 rounded-lg border border-emerald-900/50">
                <p class="text-[10px] text-emerald-700">STRIKES_TOTAL</p>
                <p class="text-white font-bold" id="scan">12405</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(DASHBOARD_HTML)

@app.route('/health')
def health(): return "OK", 200

@app.route('/api/stats')
def api_stats():
    system_data["total_scanned"] += 1
    return jsonify(system_data)

def run_bot():
    while True:
        try: bot.polling(none_stop=True, interval=2, timeout=20)
        except: time.sleep(10)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
