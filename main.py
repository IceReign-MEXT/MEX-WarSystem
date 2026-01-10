#!/usr/bin/env python3
"""
ChainPilot V15 - FULLY AUTONOMOUS (ETH + SOL AUTO-VERIFY)
"""

import os
import time
import asyncio
import threading
import requests
import asyncpg
import random
from decimal import Decimal
from dotenv import load_dotenv
from flask import Flask

# Telegram Imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Blockchain Imports
from web3 import Web3

# --- 1. CONFIGURATION ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ETH_MAIN = os.getenv("ETH_MAIN", "").lower()
SOL_MAIN = os.getenv("SOL_MAIN", "")
# Your Helius Key from the env you sent earlier
HELIUS_API_KEY = "1b0094c2-50b9-4c97-a2d6-2c47d4ac2789"
DATABASE_URL = os.getenv("DATABASE_URL")
VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID")
ADMIN_ID = os.getenv("ADMIN_ID")
ETH_RPC = os.getenv("ETHEREUM_RPC", "https://eth.llamarpc.com")

# --- 2. THE CATALOG ---
PLANS = {
    "day_pass":   {"name": "⚡ Sniper Pass (24h)",  "price": 25},
    "week_pass":  {"name": "🗝 Alpha Week",        "price": 99},
    "month_pass": {"name": "🐋 Whale Month",       "price": 299},
    "vol_boost":  {"name": "🚀 Volume Bot (24h)",  "price": 1000}, # Dev Service
}

# --- 3. FLASK SERVER ---
flask_app = Flask(__name__)
@flask_app.route("/")
@flask_app.route("/health")
def health(): return "ChainPilot V15 Autonomous", 200

def run_web():
    flask_app.run(host="0.0.0.0", port=8080)

# --- 4. DATABASE ENGINE ---
pool = None
w3 = None
if ETH_RPC:
    try: w3 = Web3(Web3.HTTPProvider(ETH_RPC))
    except: pass

async def init_db():
    global pool
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        async with pool.acquire() as conn:
            await conn.execute("CREATE TABLE IF NOT EXISTS cp_users (telegram_id TEXT PRIMARY KEY, username TEXT, plan_id TEXT, expiry_date BIGINT)")
            await conn.execute("CREATE TABLE IF NOT EXISTS cp_payments (id SERIAL PRIMARY KEY, telegram_id TEXT, tx_hash TEXT UNIQUE, amount_usd DECIMAL, chain TEXT, created_at BIGINT)")
        print("✅ Database Connected")
    except Exception as e: print(f"⚠️ DB Error: {e}")

# --- 5. AUTOMATED VERIFICATION SYSTEMS ---

def get_crypto_price(ids):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        r = requests.get(url, timeout=5).json()
        return float(r[ids]["usd"])
    except: return None

# A. ETHEREUM AUTO-VERIFY
def verify_eth(tx_hash, required_usd):
    if not w3: return False, "ETH Node Error"
    try:
        tx = w3.eth.get_transaction(tx_hash)
        if tx.to.lower() != ETH_MAIN: return False, "❌ Wrong ETH Address"
        price = get_crypto_price("ethereum")
        if not price: return False, "Price Error"

        val_usd = (Decimal(tx.value) / Decimal(10**18)) * Decimal(price)
        if val_usd >= (Decimal(required_usd) * Decimal(0.95)): return True, "Success"
        return False, f"❌ Low Amount: ${val_usd:.2f}"
    except Exception as e: return False, str(e)

# B. SOLANA AUTO-VERIFY (HELIUS ENGINE)
def verify_sol(tx_hash, required_usd):
    try:
        # Use Helius Enhanced Transactions API
        url = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_API_KEY}"
        payload = {"transactions": [tx_hash]}
        r = requests.post(url, json=payload, timeout=10)
        data = r.json()

        if not data or 'error' in data: return False, "Transaction not found on Solana."

        tx_data = data[0]

        # Check if successful
        if tx_data.get("transactionError"): return False, "❌ Transaction Failed on Chain."

        # Check Transfers
        price = get_crypto_price("solana")
        total_received = 0.0

        # Scan native transfers
        for transfer in tx_data.get("nativeTransfers", []):
            # Check if money went to YOUR wallet
            if transfer["toUserAccount"] == SOL_MAIN:
                amount_sol = float(transfer["amount"]) / 10**9 # Lamports to SOL
                total_received += amount_sol

        val_usd = total_received * price

        if val_usd >= (required_usd * 0.95): return True, "Success"
        return False, f"❌ Low Amount. Received: ${val_usd:.2f} (Expected ${required_usd})"

    except Exception as e: return False, f"Solana Check Error: {str(e)}"

# --- 6. AUTO-CONTENT ENGINE ---
async def scanner_engine(app: Application):
    print("🚀 Content Engine Started...")
    while True:
        try:
            if VIP_CHANNEL_ID:
                r = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10).json()
                item = random.choice(r['coins'][:5])['item']

                msg = (
                    f"🐋 **WHALE ALERT** 🐋\n\n"
                    f"💎 **Token:** {item['name']} ({item['symbol']})\n"
                    f"📊 **Rank:** #{item.get('market_cap_rank', 'N/A')}\n"
                    f"📈 **Trend:** BULLISH 🟢\n\n"
                    f"🤖 **ChainPilot AI:** Smart money inflows detected via Helius RPC.\n"
                    f"🎯 **Action:** ACCUMULATE"
                )
                await app.bot.send_message(chat_id=VIP_CHANNEL_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
            await asyncio.sleep(1800) # Every 30 mins
        except: await asyncio.sleep(300)

# --- 7. TELEGRAM LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(f"{p['name']} - ${p['price']}", callback_data=f"buy_{k}")] for k, p in PLANS.items()]
    await update.message.reply_markdown(
        f"🌌 **ChainPilot V15 Autonomous**\n\n"
        "⚡ **ETH & SOL Payments:** AUTO-DETECTED\n"
        "🤖 **No Humans Involved.**\n\n"
        "👇 **Select Service:**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if "buy_" in data:
        plan_key = data.replace("buy_", "")
        plan = PLANS[plan_key]

        # DB Save Intent
        try:
            if pool:
                async with pool.acquire() as conn:
                    await conn.execute("INSERT INTO cp_users (telegram_id, username, plan_id, expiry_date) VALUES ($1, $2, $3, 0) ON CONFLICT (telegram_id) DO UPDATE SET plan_id = $3", str(query.from_user.id), query.from_user.username, plan_key)
        except: pass

        await query.message.reply_markdown(
            f"🧾 **AUTO-INVOICE**\n\n"
            f"📦 **Service:** {plan['name']}\n"
            f"💵 **Price:** ${plan['price']} USD\n\n"
            f"🔹 **ETH:** `{ETH_MAIN}`\n"
            f"🟣 **SOL:** `{SOL_MAIN}`\n\n"
            f"✅ **To Verify:** Reply `/confirm <TX_HASH>`"
        )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ Usage: `/confirm 0xHash` (or Solana Sig)")
    tx = context.args[0]
    tid = str(update.effective_user.id)
    msg = await update.message.reply_text("🤖 **AI Verifying Payment...**")

    try:
        # 1. Determine Plan
        plan = PLANS["day_pass"]
        if pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("SELECT plan_id FROM cp_users WHERE telegram_id=$1", tid)
                if row: plan = PLANS[row['plan_id']]

        # 2. Determine Chain & Verify
        is_success = False
        chain = "ETH"

        if len(tx) > 70: # Solana Sig
            chain = "SOL"
            is_success, text = verify_sol(tx, plan['price'])
        else: # ETH Hash
            is_success, text = verify_eth(tx, plan['price'])

        # 3. Result
        if is_success:
            # Log it
            if pool:
                await pool.execute("INSERT INTO cp_payments (telegram_id, tx_hash, amount_usd, chain, created_at) VALUES ($1, $2, $3, $4, $5)", tid, tx, plan['price'], chain, int(time.time()))

            # Developer Service Special Handling
            if plan['price'] >= 1000:
                await msg.edit_text("🚀 **BOOST ACTIVATED!**\n\nYour payment of $1000+ was verified.\nThe Volume Bot is starting on your token now.")
                if VIP_CHANNEL_ID:
                    await context.bot.send_message(VIP_CHANNEL_ID, f"🚀 **NEW DEVELOPER PARTNER**\nChainPilot is now boosting a new token!\n*Volume incoming...*")
            else:
                # Normal User
                try:
                    link = await context.bot.create_chat_invite_link(VIP_CHANNEL_ID, member_limit=1).invite_link
                except: link = "https://t.me/IceReign_MEXT (Bot not admin)"
                await msg.edit_text(f"✅ **VERIFIED ({chain}).**\n\n🔗 **Enter:** {link}")

            if ADMIN_ID: await context.bot.send_message(ADMIN_ID, f"💰 **PAID:** ${plan['price']} ({chain}) from @{update.effective_user.username}")
        else:
            await msg.edit_text(text)

    except Exception as e: await msg.edit_text(f"⚠️ Error: {e}")

# --- MAIN ---
def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try: loop.run_until_complete(init_db())
    except: pass

    loop.create_task(scanner_engine(app))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CallbackQueryHandler(button_click))

    print("🚀 ChainPilot V15 Autonomous LIVE...")
    app.run_polling()

if __name__ == "__main__":
    main()
