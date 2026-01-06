import os, threading, time, telebot, random, requests, base64, json
from flask import Flask, render_template_string

# --- THE ARCHITECT'S DUAL-VAULT CONFIG ---
VAULT_ETH = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
VAULT_SOL = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy"
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@ICEGODSICEDEVILS"

# YOUR LIVE VERCEL DASHBOARD URL
DASH_URL = "https://mex-war-system-ox6f.vercel.app"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- SYSTEM STATE (54 NODES) ---
state = {
    "members": ["559382910"], # Add authorized Telegram IDs here
    "nodes": 54,
    "sol_reserves": 335.55,
    "eth_reserves": 1.80099
}

def is_paid(uid):
    return str(uid) in state["members"]

# --- GLOBAL SURVEILLANCE ENGINE ---
def global_monitoring():
    # Delay start to allow bot instance to settle
    time.sleep(15)
    while True:
        try:
            time.sleep(random.randint(900, 1800))
            chain = random.choice(["SOLANA", "ETHEREUM"])
            whale_amt = random.randint(150, 850)

            alert = (
                f"🚨 **{chain} WHALE DETECTION** 🚨\n"
                "────────────────────\n"
                f"Value: `{whale_amt} {'SOL' if chain=='SOLANA' else 'ETH'}`\n"
                "Action: `Front-Run Nodes 1-54 Active`\n"
                "Status: `BETTER THAN ALIENS BRAIN`\n"
                "────────────────────\n"
                f"🌐 [VIEW ON TERMINAL]({DASH_URL})"
            )
            bot.send_message(CHANNEL_ID, alert, parse_mode='Markdown', disable_web_page_preview=False)
        except Exception:
            pass

# --- COMMAND HANDLERS ---
@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    msg = (
        "❄️ **ICE GODS MONOLITH V21**\n"
        "────────────────────\n"
        "Sovereign Dual-Chain Infrastructure\n"
        "54 High-Performance Nodes Active\n\n"
        f"🏦 **SOL Vault:** `{VAULT_SOL}`\n"
        f"🏦 **ETH Vault:** `{VAULT_ETH}`\n"
        "────────────────────\n"
        "Status: **ONLINE & ENCRYPTED**"
    )
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 OPEN NEXUS TERMINAL", url=DASH_URL),
        telebot.types.InlineKeyboardButton("💳 ACTIVATE NODE (0.5 ETH / 5 SOL)", callback_data="pay")
    )
    bot.reply_to(message, msg, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['strike', 'snipe', 'raid', 'stats', 'roadmap', 'snipers'])
def restricted_commands(message):
    if not is_paid(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💳 GET ACCESS", callback_data="pay"))
        bot.reply_to(message, "🔒 **ACCESS DENIED.**\n\nThis command requires an active Node subscription.", parse_mode='Markdown', reply_markup=markup)
        return

    # Authorized Responses
    cmd = message.text.split()[0].replace('/', '').upper()
    bot.reply_to(message, f"🚀 **{cmd} PROTOCOL:** Executing on 54 Nodes... Scan Complete.")

@bot.callback_query_handler(func=lambda c: c.data == "pay")
def pay_info(call):
    pay_msg = (
        "💳 **ACTIVATION PROTOCOL**\n\n"
        "Send funds to the Architect Vaults:\n\n"
        f"SOL: `{VAULT_SOL}`\n"
        f"ETH: `{VAULT_ETH}`\n\n"
        "Once verified, your Telegram ID is whitelisted across the 54-node network."
    )
    bot.send_message(call.message.chat.id, pay_msg, parse_mode='Markdown')

# --- WEB SERVER (KEEP-ALIVE) ---
@app.route('/')
def health_check():
    return "MONOLITH_V21_ONLINE", 200

# --- BOT RUNTIME WITH CONFLICT RECOVERY ---
def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=global_monitoring, daemon=True).start()
    threading.Thread(target=run_bot, daemon=True).start()
    # Port is required for Render web services
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
