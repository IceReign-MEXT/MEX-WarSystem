import telebot
import os
import threading
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# --- FIREBASE INITIALIZATION ---
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Connected")
except Exception as e:
    print(f"❌ Firebase Error: {e}")

# --- BOT CONFIG ---
TOKEN = "7622869925:AAH_O_M1_I8_4-8_j-XN-uK481t6W0p96qU"
bot = telebot.TeleBot(TOKEN)
APP_ID = "mex-war-system"

# --- HEALTH SERVER (To keep Render alive) ---
app = Flask(__name__)

@app.route('/health')
@app.route('/')
def health():
    return {"status": "Sovereign OS Active"}, 200

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "❄️ ICE_GODS // MONOLITH_OS\n\nSovereign status detected. Syncing with Dashboard...\n\nCommands:\n/strike - Execute liquidity attack\n/status - Check node activation")

@bot.message_handler(commands=['strike'])
def handle_strike(message):
    user_id = str(message.from_user.id)
    # Check shared Firebase collection
    doc_ref = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('verified_users').document(user_id)
    doc = doc_ref.get()

    if doc.exists:
        bot.send_message(message.chat.id, "🎯 STRIKE_PROTOCOL_ENGAGED. Monitoring mempool for high-value targets.")
    else:
        bot.send_message(message.chat.id, "❌ ACCESS_DENIED. Your node is not activated. Use the dashboard to initialize.")

# --- EXECUTION ---
if __name__ == "__main__":
    # Start Health Server in background
    threading.Thread(target=run_health_server, daemon=True).start()
    print("📡 Health Server running. Starting Bot Polling...")
    # Infinity polling with conflict handling
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
