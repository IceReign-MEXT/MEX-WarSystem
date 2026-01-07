import telebot
from telebot import types
import os
import threading
import json
import time
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# --- ENV SETUP ---
TOKEN = os.environ.get("BOT_TOKEN")
# Your Channel ID (e.g., -100123456789)
CHANNEL_ID = os.environ.get("CHANNEL_ID")
APP_ID = "mex-war-system"
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- DB INIT ---
db = None
try:
    if not firebase_admin._apps:
        service_account_info = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        info = json.loads(service_account_info.strip().strip("'\""))
        cred = credentials.Certificate(info)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
except: pass

def check_auth(uid):
    if not db: return None
    doc = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('verified_users').document(str(uid)).get()
    return doc.to_dict() if doc.exists else None

# --- INSTANT NOTIFICATION ---
def broadcast(msg):
    if CHANNEL_ID:
        try: bot.send_message(CHANNEL_ID, f"⚡ *MONOLITH_FEED:*\n{msg}", parse_mode="Markdown")
        except: pass

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('🚀 ACTIVATE_SNIPER', '📊 WALLET_TRACKER', '🆔 GET_ID', '💎 PREMIUM_INFO')
    bot.send_message(message.chat.id, "❄️ *MONOLITH_V2: MULTI-CHAIN WARFARE*\nDual-Engine (SOL/ETH) Online.", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = message.from_user.id
    if message.text == '🆔 GET_ID':
        bot.reply_to(message, f"Terminal ID: `{uid}`")

    elif message.text == '🚀 ACTIVATE_SNIPER':
        user = check_auth(uid)
        if user:
            bot.send_message(message.chat.id, "✅ *SNIPER_ACTIVE*\nEngine: Dual SOL/ETH\nStatus: Scanning for Targets...")
            broadcast(f"Operator {uid} has engaged the Sniper Engine! 🔭")
        else:
            bot.send_message(message.chat.id, "❌ *ACCESS_DENIED*\nPlease activate your Node ID on the Dashboard first.")

    elif message.text == '📊 WALLET_TRACKER':
        user = check_auth(uid)
        if user:
            bot.send_message(message.chat.id, f"🔍 *MONITORING_WALLET:*\n`{user.get('wallet')}`\nInstant notifications enabled.")
        else:
            bot.send_message(message.chat.id, "❌ Activation Required.")

# --- FLASK ---
app = Flask(__name__)
@app.route('/health')
def health(): return {"status": "online"}, 200

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.polling(none_stop=True)
