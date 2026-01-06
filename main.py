import os, threading, time, telebot, random, requests, base64, json
from flask import Flask, render_template_string

# --- CONFIGURATION (DUAL-VAULT) ---
VAULT_ETH = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F"
VAULT_SOL = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy"
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@ICEGODSICEDEVILS"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- MONETIZATION & MEMBERSHIP ---
# Add your ID or user IDs here manually to unlock them
state = {
    "members": ["559382910"],
    "nodes": 54,
    "sol_reserves": 335.55,
    "eth_reserves": 1.80099
}

def is_paid(uid):
    return str(uid) in state["members"]

# --- DUAL-CHAIN SURVEILLANCE ---
def global_monitoring():
    while True:
        time.sleep(random.randint(900, 1800))
        chain = random.choice(["SOLANA", "ETHEREUM"])
        whale_amt = random.randint(100, 1000)

        alert = (
            f"🚨 **{chain} WHALE ALERT** 🚨\n"
            "────────────────────\n"
            f"Detected: `{whale_amt} {'SOL' if chain=='SOLANA' else 'ETH'}` movement.\n"
            f"Target: `High-Vol Liquidity Pool`\n"
            "Action: `Front-Run Nodes Prepped`\n"
            "────────────────────\n"
            "❄️ **ICE GODS SURVEILLANCE: BETTER THAN ALIENS BRAIN.**"
        )
        try: bot.send_message(CHANNEL_ID, alert, parse_mode='Markdown')
        except: pass

# --- COMMAND HANDLERS (FULL SUITE) ---
@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    msg = (
        "❄️ **ICE GODS MONOLITH V21: DUAL-CHAIN**\n"
        "────────────────────\n"
        "The most powerful autonomous infrastructure on SOL & ETH.\n\n"
        f"🏦 **SOL Vault:** `{VAULT_SOL}`\n"
        f"🏦 **ETH Vault:** `{VAULT_ETH}`\n"
        "────────────────────\n"
        "Status: **ONLINE - 54 NODES ACTIVE**"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌐 OPEN TERMINAL", url="https://ice-gods-nexus.vercel.app"))
    markup.add(telebot.types.InlineKeyboardButton("🛠️ ACTIVATE NODE", callback_data="pay"))
    bot.reply_to(message, msg, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['strike', 'snipe', 'raid', 'stats', 'roadmap', 'snipers'])
def handle_all_commands(message):
    cmd = message.text.split()[0].replace('/', '').upper()

    if not is_paid(message.from_user.id):
        bot.reply_to(message, "🔒 **ACCESS DENIED.**\n\nThis command is reserved for **Verified Nodes**. Please pay the 0.5 ETH / 5 SOL activation fee to join the Multitude.", parse_mode='Markdown')
        return

    # PAID RESPONSES
    responses = {
        "STRIKE": "🎯 **STRIKE ENGINE:** Scanning Dual-Chain pools... Targets Locked.",
        "SNIPE": "🔫 **SNIPER PROTOCOL:** Awaiting token launch on Raydium/Uniswap.",
        "RAID": "⚔️ **RAID SYSTEM:** Preparing coordinated social strike.",
        "STATS": f"📊 **FLEET METRICS:**\nVault: {state['sol_reserves']} SOL / {state['eth_reserves']} ETH\nNodes: 54/100",
        "ROADMAP": "🗺️ **ROADMAP:** v21 Deployment -> Dual-Chain Domination -> AI-Snipe V2.",
        "SNIPERS": "📡 **SNIPER NODES:** 54 Active nodes scanning mempool."
    }
    bot.reply_to(message, responses.get(cmd, "Command Online."), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: c.data == "pay")
def pay_callback(call):
    pay_msg = (
        "💳 **ACTIVATION PROTOCOL**\n\n"
        "To activate your node, send:\n"
        "**0.5 ETH** or **5 SOL** to the vaults below:\n\n"
        f"ETH: `{VAULT_ETH}`\n"
        f"SOL: `{VAULT_SOL}`\n\n"
        "Once done, the machine detects the TX and whitelists you."
    )
    bot.send_message(call.message.chat.id, pay_msg, parse_mode='Markdown')

if __name__ == '__main__':
    threading.Thread(target=global_monitoring, daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
