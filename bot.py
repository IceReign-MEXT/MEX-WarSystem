import telebot
import os
import threading
import json
import time
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# --- INITIALIZATION ---
db = None
try:
    if not firebase_admin._apps:
        service_account_info = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if service_account_info:
            cleaned = service_account_info.strip()
            if cleaned.startswith(("'", '"')): cleaned = cleaned[1:-1]
            info = json.loads(cleaned)
            if "private_key" in info: info["private_key"] = info["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(info)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("✅ MONOLITH_DB_LINKED")
except Exception as e:
    print(f"❌ STARTUP_ERR: {e}")

TOKEN = os.environ.get("BOT_TOKEN")
APP_ID = os.environ.get("__app_id", "mex-war-system")
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- SECURITY ---
def check_auth(user_id):
    if not db: return None
    try:
        doc = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('verified_users').document(str(user_id)).get()
        return doc.to_dict() if doc.exists else None
    except: return None

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "❄️ ICE_GODS // MONOLITH_V2\nStatus: ONLINE\n\nCommands:\n/strike - Node Status\n/snipe - Sniper Engine\n/raid - X-Raid Tool\n/id - Show My ID")

@bot.message_handler(commands=['id'])
def my_id(message):
    bot.reply_to(message, f"Terminal ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['strike', 'status'])
def strike(message):
    user_data = check_auth(message.from_user.id)
    if user_data:
        msg = f"🎯 NODE_ACTIVE\nID: {message.from_user.id}\nLEVEL: {user_data.get('subscription', 'PREMIUM')}\nSTATUS: OPTIMAL"
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, "❌ UNAUTHORIZED\nActivate your ID on the Dashboard first.")

@bot.message_handler(commands=['snipe'])
def snipe(message):
    if not check_auth(message.from_user.id):
        bot.send_message(message.chat.id, "❌ SUBSCRIPTION_REQUIRED")
        return
    bot.send_message(message.chat.id, "🔭 SNIPER_READY\nSend Token CA to initiate lock.")

@bot.message_handler(commands=['raid'])
def raid(message):
    if not check_auth(message.from_user.id):
        bot.send_message(message.chat.id, "❌ SUBSCRIPTION_REQUIRED")
        return
    bot.send_message(message.chat.id, "📣 RAID_ENGINE_ONLINE\nSend Twitter link to begin coordination.")

# --- SERVER ---
app = Flask(__name__)
@app.route('/health')
def health(): return {"status": "online"}, 200

def run_srv():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def run_bot():
    print("🚀 Bot starting...")
    bot.delete_webhook(drop_pending_updates=True)
    while True:
        try:
            bot.polling(none_stop=True, interval=5, timeout=20)
        except Exception as e:
            if "Conflict" in str(e): time.sleep(15)
            else: time.sleep(5)

if __name__ == "__main__":
    if TOKEN:
        threading.Thread(target=run_srv, daemon=True).start()
        run_bot()





