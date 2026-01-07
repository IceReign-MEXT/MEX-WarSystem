import telebot
import os
import threading
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# --- FIREBASE INITIALIZATION ---
# This looks for your serviceAccountKey.json in the root directory
try:
    if not firebase_admin._apps:
        # Check if file exists to prevent crash
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        else:
            print("⚠️ WARNING: serviceAccountKey.json not found. Firebase features will fail.")

    db = firestore.client()
    print("✅ Firebase Connected")
except Exception as e:
    print(f"❌ Firebase Error: {e}")

# --- BOT CONFIG ---
# We use os.environ.get to pull the token safely from Render's Environment settings
TOKEN = os.environ.get("BOT_TOKEN")
APP_ID = "mex-war-system"

if not TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(TOKEN)

# --- HEALTH SERVER (To keep Render alive and happy) ---
app = Flask(__name__)

@app.route('/health')
@app.route('/')
def health():
    return {"status": "Sovereign OS Active", "bot_connected": bool(TOKEN)}, 200

def run_health_server():
    # Render provides the PORT variable automatically
    port = int(os.environ.get("PORT", 8080))
    print(f"📡 Health Server starting on port {port}")
    app.run(host='0.0.0.0', port=port)

# --- BOT COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "❄️ ICE_GODS // MONOLITH_OS\n\n"
        "Sovereign status detected. Syncing with Dashboard...\n\n"
        "Available Commands:\n"
        "/strike - Execute liquidity attack\n"
        "/status - Check node activation\n"
        "/id     - Get your Telegram ID"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(message, f"Your Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['strike'])
def handle_strike(message):
    user_id = str(message.from_user.id)

    try:
        # Check shared Firebase collection: artifacts -> mex-war-system -> public -> data -> verified_users -> {user_id}
        doc_ref = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('verified_users').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            bot.send_message(message.chat.id, "🎯 STRIKE_PROTOCOL_ENGAGED. Monitoring mempool for high-value targets. Standing by...")
        else:
            bot.send_message(message.chat.id, f"❌ ACCESS_DENIED.\n\nYour ID ({user_id}) is not activated.\nUse the dashboard to initialize your node.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ SYSTEM_ERROR: Unable to reach Firebase. Contact Administrator.")
        print(f"Firestore Error: {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    if TOKEN:
        # Start Health Server in background thread
        threading.Thread(target=run_health_server, daemon=True).start()

        print("🚀 Starting Bot Polling...")
        # infinity_polling handles network flickers and prevents the 409 Conflict loop
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    else:
        print("🛑 Bot cannot start without TOKEN. Check Render Environment Variables.")
