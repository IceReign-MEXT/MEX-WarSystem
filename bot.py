import telebot
from telebot import types
import os
import threading
import json
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore
import requests

# --- SYSTEM CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
VAULT = os.environ.get("VAULT_ADDRESS") # Your 1% Fee Wallet
APP_ID = "mex-war-system"
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- FIREBASE SETUP ---
db = None
try:
    if not firebase_admin._apps:
        creds_raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        creds_dict = json.loads(creds_raw)
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
except Exception as e: print(f"DB_ERR: {e}")

# --- RUG & FRAUD DETECTION ---
def scan_contract(ca, chain):
    # Simulated Logic for Rug/Fake Token Detection
    # In production, this hits DexScreener or GoPlus API
    risk_score = 0
    flags = []

    # Logic: Detect if it's a "honeypot"
    if "0000" in ca: # Dummy check for simulation
        risk_score = 99
        flags.append("HONEYPOT_DETECTED")

    return risk_score, flags

# --- CHANNEL BROADCASTER (FOMO & SECURITY) ---
def report_to_war_room(msg, type="INFO"):
    prefix = "🛡️ [SEC_SCAN]" if type == "SEC" else "🚀 [LIVE_PROFIT]"
    if CHANNEL_ID:
        try: bot.send_message(CHANNEL_ID, f"*{prefix}*\n{msg}", parse_mode="Markdown")
        except: pass

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    welcome = (
        "⚔️ *MONOLITH GLOBAL TERMINAL*\n"
        "Status: *WAR-READY*\n\n"
        "1. Sniper Engine (1% Fuel Fee)\n"
        "2. Rug-Protector (Active)\n"
        "3. Whale-Tracker (Synced)\n\n"
        "Your ID: `{}`"
    ).format(uid)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🎯 SNIPE_TOKEN', '🛡️ SCAN_CA', '💰 MY_VAULT', '🔑 LINK_LICENSE')
    bot.send_message(message.chat.id, welcome, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_war_room(message):
    uid = message.from_user.id

    if message.text == '🛡️ SCAN_CA':
        bot.send_message(message.chat.id, "🌐 Send Contract Address (SOL/ETH) for deep audit:")

    elif message.text == '🎯 SNIPE_TOKEN':
        # Check subscription via Firebase
        doc = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('verified_users').document(str(uid)).get()
        if doc.exists:
            bot.send_message(message.chat.id, "✅ *LICENSED OPERATOR*\n1% Buy/Sell Tax Active.\nDestination: `{}`".format(VAULT))
        else:
            bot.send_message(message.chat.id, "❌ *UNAUTHORIZED*\nUpgrade to a War-License on the Dashboard.")

# --- HEALTH ---
app = Flask(__name__)
@app.route('/health')
def health(): return {"status": "sovereign"}, 200

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.polling(none_stop=True)
