import telebot
import os
import threading
import json
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# --- FIREBASE INITIALIZATION ---
db = None
try:
    if not firebase_admin._apps:
        # Priority 1: Environment Variable (Best for Render)
        service_account_info = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

        if service_account_info:
            try:
                # Handle potential quotes or string issues from env
                info = json.loads(service_account_info)
                cred = credentials.Certificate(info)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print("✅ Firebase initialized via Environment Variable.")
            except Exception as json_err:
                print(f"❌ JSON Parsing Error for FIREBASE_SERVICE_ACCOUNT: {json_err}")

        # Priority 2: Local File (Fallback for Termux)
        elif os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("✅ Firebase initialized via serviceAccountKey.json file.")
        else:
            print("⚠️ WARNING: No Firebase credentials found (Env or File).")
except Exception as e:
    print(f"❌ Firebase Critical Error: {e}")

# --- BOT CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")
APP_ID = os.environ.get("__app_id", "mex-war-system")
bot = telebot.TeleBot(TOKEN)

# --- HEALTH SERVER ---
app = Flask(__name__)
@app.route('/health')
def health():
    return {
        "status": "online",
        "db_connected": db is not None,
        "app_id": APP_ID
    }, 200

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
        bot.send_message(message.chat.id, "❌ SYSTEM_OFFLINE: Firebase credentials missing.")
        return

    user_id = str(message.from_user.id)
    try:
        # Path: artifacts/{APP_ID}/public/data/verified_users/{user_id}
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
        print(f"🚀 Starting Bot Polling for {APP_ID}...")
        bot.infinity_polling()
    else:
        print("🛑 Error: No BOT_TOKEN found.")
