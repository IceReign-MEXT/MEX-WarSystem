import telebot
import os
import threading
import json
import traceback
import time
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# --- FIREBASE SETUP ---
db = None
try:
    if not firebase_admin._apps:
        service_account_info = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if service_account_info:
            cleaned_info = service_account_info.strip()
            if cleaned_info.startswith(("'", '"')): cleaned_info = cleaned_info[1:-1]
            info = json.loads(cleaned_info)
            if "private_key" in info: info["private_key"] = info["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(info)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("✅ MONOLITH_DB_CONNECTED")
except Exception as e:
    print(f"❌ DB_CRITICAL: {e}")

# --- BOT CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")
APP_ID = os.environ.get("__app_id", "mex-war-system")
# Use single-threaded mode to prevent internal race conditions
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- UTILS ---
def check_auth(user_id):
    if not db: return False
    try:
        doc = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('verified_users').document(str(user_id)).get()
        return doc.to_dict() if doc.exists else False
    except: return False

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "❄️ ICE_GODS // MONOLITH_V2\nStatus: ONLINE\n\nCommands:\n/strike - Verify Node\n/snipe - Target Token\n/raid - Social Ops")

@bot.message_handler(commands=['strike', 'status'])
def strike(message):
    auth_data = check_auth(message.from_user.id)
    if auth_data:
        msg = f"🎯 NODE_ACTIVE: {message.from_user.id}\nSUB: {auth_data.get('subscription', 'PREMIUM')}\nSYSTEM: OPTIMAL"
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, "❌ UNAUTHORIZED: Activate your node via the Dashboard (0.5 SOL) first.")

# --- RUNTIME & CONFLICT RESOLUTION ---
app = Flask(__name__)
@app.route('/health')
def health():
    return {"status": "online"}, 200

def run_health():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def start_polling():
    print(f"🚀 [SYSTEM] CLEARING SESSIONS FOR {APP_ID}...")
    # Force delete webhook to clear the line
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(5)
    except:
        pass

    while True:
        try:
            print("📡 [NET] ATTEMPTING_POLLING_LOCK...")
            bot.polling(none_stop=True, interval=5, timeout=20)
        except Exception as e:
            error_msg = str(e)
            if "Conflict" in error_msg:
                print("⚠️ [CONFLICT] OTHER_INSTANCE_DETECTED. WAITING_FOR_SIGTERM (20s)...")
                # Wait longer than Render's health check cycle
                time.sleep(20)
            else:
                print(f"❌ [ERROR] {error_msg}")
                time.sleep(10)

if __name__ == "__main__":
    if TOKEN:
        threading.Thread(target=run_health, daemon=True).start()
        start_polling()
