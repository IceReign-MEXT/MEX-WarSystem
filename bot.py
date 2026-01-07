import telebot
import os
import threading
import json
import traceback
import time
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# --- FIREBASE INITIALIZATION ---
db = None
try:
    if not firebase_admin._apps:
        service_account_info = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if service_account_info:
            try:
                cleaned_info = service_account_info.strip()
                if (cleaned_info.startswith("'") and cleaned_info.endswith("'")) or \
                   (cleaned_info.startswith('"') and cleaned_info.endswith('"')):
                    cleaned_info = cleaned_info[1:-1]

                info = json.loads(cleaned_info)
                if "private_key" in info:
                    info["private_key"] = info["private_key"].replace("\\n", "\n")

                cred = credentials.Certificate(info)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print("✅ Firebase initialized successfully.")
            except Exception as json_err:
                print(f"❌ JSON Parsing Error: {json_err}")
except Exception as e:
    print(f"❌ Firebase Critical Error: {e}")

# --- BOT CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")
APP_ID = os.environ.get("__app_id", "mex-war-system")
bot = telebot.TeleBot(TOKEN, threaded=False) # Disable threading to prevent race conditions

# --- HEALTH SERVER ---
app = Flask(__name__)
@app.route('/health')
def health(): return {"status": "online", "db_connected": db is not None}, 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "❄️ ICE_GODS // MONOLITH_OS\nStatus: ONLINE\n\nUse /strike to check node activation.")

@bot.message_handler(commands=['strike'])
def handle_strike(message):
    if db is None:
        bot.send_message(message.chat.id, "❌ SYSTEM_OFFLINE: Database not connected.")
        return
    user_id = str(message.from_user.id)
    try:
        doc_ref = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('verified_users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            bot.send_message(message.chat.id, "🎯 STRIKE_PROTOCOL_ENGAGED.\n\nSovereign status confirmed.")
        else:
            bot.send_message(message.chat.id, f"❌ ACCESS_DENIED.\n\nID {user_id} not activated.")
    except Exception as e:
        traceback.print_exc()
        bot.send_message(message.chat.id, "❌ ERROR: Database communication failed.")

# --- THE CLEAN POLLING LOOP ---
def start_polling():
    print(f"🚀 Initializing Clean Polling for {APP_ID}...")
    # Force drop everything before starting
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(5) # Give Telegram time to breathe

    while True:
        try:
            # Use single-threaded polling with long intervals to resolve 409
            bot.polling(none_stop=True, interval=5, timeout=30)
        except Exception as e:
            if "Conflict" in str(e):
                print("⚠️ Conflict detected. Sleeping 15s to allow old instance to die...")
                time.sleep(15)
            else:
                print(f"⚠️ Polling issue: {e}")
                time.sleep(5)

if __name__ == "__main__":
    if TOKEN:
        threading.Thread(target=run_health_server, daemon=True).start()
        start_polling()
