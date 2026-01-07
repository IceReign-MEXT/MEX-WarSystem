import telebot
import os
import threading
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# --- FIREBASE INITIALIZATION ---
db = None
try:
    if not firebase_admin._apps:
        # Render puts Secret Files in the root directory by default
        key_path = "serviceAccountKey.json"
        if os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("✅ Firebase initialized successfully.")
        else:
            print("❌ ERROR: serviceAccountKey.json not found in root.")
except Exception as e:
    print(f"❌ Firebase Critical Error: {e}")

# --- BOT CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")
APP_ID = "mex-war-system"
bot = telebot.TeleBot(TOKEN)

# --- HEALTH SERVER ---
app = Flask(__name__)
@app.route('/health')
def health(): return {"status": "online", "db_connected": db is not None}, 200

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "❄️ ICE_GODS // MONOLITH_OS\nStatus: ONLINE\n\nUse /strike to check node activation.")

@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(message, f"Your Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['strike'])
def handle_strike(message):
    if db is None:
        bot.send_message(message.chat.id, "❌ SYSTEM_OFFLINE: Firebase configuration missing on server.")
        return

    user_id = str(message.from_user.id)
    try:
        # Correct path based on App.jsx logic: artifacts/mex-war-system/public/data/verified_users/{user_id}
        doc_ref = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('verified_users').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            bot.send_message(message.chat.id, "🎯 STRIKE_PROTOCOL_ENGAGED.\n\nSovereign status confirmed. Monitoring mempool for high-value targets...")
        else:
            bot.send_message(message.chat.id, f"❌ ACCESS_DENIED.\n\nID {user_id} is not activated.\nInitialize your node at the dashboard first.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ ERROR: Database communication failed.")
        print(f"Firestore Error: {e}")

if __name__ == "__main__":
    if TOKEN:
        threading.Thread(target=run_health_server, daemon=True).start()
        print("🚀 Starting Bot Polling...")
        bot.infinity_polling()
    else:
        print("🛑 Error: No BOT_TOKEN found in environment variables.")
