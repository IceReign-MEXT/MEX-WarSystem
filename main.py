#!/usr/bin/env python3
"""
MEX WAR SYSTEM V2 - VISUAL WARLORD
Features: Image Alerts, High Frequency Scans, Auto-Payment
"""

import os
import asyncio
import threading
import requests
import asyncpg
import random
from decimal import Decimal
from dotenv import load_dotenv
from flask import Flask

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Web3
from web3 import Web3

# --- 1. CONFIGURATION ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ETH_MAIN = os.getenv("ETH_MAIN", "").lower()
RPC_URL = os.getenv("ETHEREUM_RPC")
DATABASE_URL = os.getenv("DATABASE_URL")
VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID")
ADMIN_ID = os.getenv("ADMIN_ID")

# --- 2. ASSETS (The Professional Look) ---
IMAGES = {
    "whale": "https://cdn.pixabay.com/photo/2020/08/09/14/25/business-5475661_1280.jpg",
    "contract": "https://cdn.pixabay.com/photo/2016/11/27/21/42/stock-1863880_1280.jpg",
    "war": "https://cdn.pixabay.com/photo/2017/08/30/01/05/milky-way-2695569_1280.jpg"
}

# --- 3. FLASK SERVER ---
flask_app = Flask(__name__)
@flask_app.route("/")
def health(): return "WAR SYSTEM VISUALS ACTIVE ⚔️", 200
def run_web(): flask_app.run(host="0.0.0.0", port=8080)

# --- 4. DATABASE ---
pool = None
async def init_db():
    global pool
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        print("✅ War DB Linked")
    except: print("⚠️ DB Syncing...")

# --- 5. WAR ENGINE (The Content Generator) ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))

async def eth_radar(app: Application):
    print("⚔️ WAR SYSTEM: Scanning Mempool...")
    last_block = 0

    while True:
        try:
            if VIP_CHANNEL_ID and w3.is_connected():
                current_block = w3.eth.block_number

                if current_block > last_block:
                    block = w3.eth.get_block(current_block, full_transactions=True)
                    last_block = current_block

                    for tx in block.transactions:
                        # 1. NEW CONTRACT (Sniper Alert)
                        if tx['to'] is None:
                            hash_link = f"https://etherscan.io/tx/{tx['hash'].hex()}"
                            caption = (
                                f"🛡️ **NEW CONTRACT DEPLOYED**\n\n"
                                f"🧱 **Block:** {current_block}\n"
                                f"⛽ **Gas:** {tx['gas']}\n"
                                f"🔗 [View on Etherscan]({hash_link})\n\n"
                                f"⚠️ *MexWarSystem Analysis: Pending Safety Scan...*"
                            )
                            # Post 1 per block max to avoid flooding
                            if random.randint(1,5) == 1:
                                try:
                                    await app.bot.send_photo(VIP_CHANNEL_ID, photo=IMAGES["contract"], caption=caption, parse_mode=ParseMode.MARKDOWN)
                                except: pass

                        # 2. WHALE MOVEMENT (> 10 ETH) - Lowered for more activity
                        val_eth = float(Web3.from_wei(tx['value'], 'ether'))
                        if val_eth > 10:
                            caption = (
                                f"🐋 **ETH WHALE MOVEMENT**\n\n"
                                f"💰 **Amount:** {val_eth:,.2f} ETH\n"
                                f"🧱 **Block:** {current_block}\n\n"
                                f"🤖 **AI Tracking:** Large capital flow detected.\n"
                                f"🔗 [View Transaction](https://etherscan.io/tx/{tx['hash'].hex()})"
                            )
                            try:
                                await app.bot.send_photo(VIP_CHANNEL_ID, photo=IMAGES["whale"], caption=caption, parse_mode=ParseMode.MARKDOWN)
                            except: pass

            await asyncio.sleep(10)
        except Exception as e:
            print(f"Radar Error: {e}")
            await asyncio.sleep(5)

# --- 6. TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("⚔️ JOIN WAR ROOM ($100)", callback_data="buy_war")]]
    await update.message.reply_photo(
        photo=IMAGES["war"],
        caption=(
            f"⚔️ **MEX WAR SYSTEM V2** ⚔️\n\n"
            "Ethereum Mempool Surveillance Unit.\n\n"
            "📡 **Capabilities:**\n"
            "• New Contract Sniffer\n"
            "• Gas War Detection\n"
            "• Whale Tracking\n\n"
            "👇 **Initialize Protocol:**"
        ),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=ParseMode.MARKDOWN
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if "buy_war" in q.data:
        # DB Log
        try:
            if pool:
                tid = str(q.from_user.id)
                await pool.execute("INSERT INTO cp_users (telegram_id, username, plan_id, expiry_date) VALUES ($1, $2, $3, 0) ON CONFLICT (telegram_id) DO UPDATE SET plan_id = $3", tid, q.from_user.username, "war_room")
        except: pass

        await q.message.reply_markdown(
            f"🧾 **WAR ROOM INVOICE**\n\n"
            f"💰 **Price:** $100 USD (ETH)\n"
            f"🏦 **Deposit:**\n`{ETH_MAIN}`\n\n"
            f"⚠️ **Reply:** `/confirm <TX_HASH>`"
        )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ Usage: /confirm 0xHash")
    tx = context.args[0]
    msg = await update.message.reply_text("🛰 **Scanning Mempool...**")

    try:
        t = w3.eth.get_transaction(tx)
        if t.to.lower() != ETH_MAIN:
            await msg.edit_text("❌ Wrong Address.")
            return

        # Get Price
        price = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd").json()["ethereum"]["usd"]
        val_usd = float(Web3.from_wei(t.value, 'ether')) * price

        if val_usd >= 95: # $95 tolerance
            if pool:
                await pool.execute("INSERT INTO cp_payments (telegram_id, tx_hash, amount_usd, chain, created_at) VALUES ($1, $2, $3, 'ETH-WAR', $4)", str(update.effective_user.id), tx, 100, int(time.time()))

            try: link = await context.bot.create_chat_invite_link(VIP_CHANNEL_ID, member_limit=1).invite_link
            except: link = "Contact Admin (Bot not Admin)"

            await msg.edit_text(f"⚔️ **ACCESS GRANTED.**\n\n🔗 {link}")
            if ADMIN_ID: await context.bot.send_message(ADMIN_ID, f"💰 **WAR ROOM:** ${val_usd:.2f} from @{update.effective_user.username}")
        else:
            await msg.edit_text(f"❌ Insufficient Funds: ${val_usd:.2f}")

    except Exception as e: await msg.edit_text(f"⚠️ Error: {e}")

# --- MAIN ---
def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try: loop.run_until_complete(init_db())
    except: pass

    loop.create_task(eth_radar(app))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CallbackQueryHandler(button))

    print("⚔️ MEX WAR SYSTEM LIVE...")
    app.run_polling()

if __name__ == "__main__":
    main()
