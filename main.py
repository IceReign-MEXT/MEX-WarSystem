#!/usr/bin/env python3
"""
MEX WAR SYSTEM - ETHEREUM MEMPOOL WARLORD
Features: New Contract Sniping, Whale Monitor, Gas Tracker
"""

import os
import time
import asyncio
import threading
import requests
import asyncpg
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

# --- 2. PRICING ---
PRICE_WAR_ROOM = 100 # $100 for ETH Alpha Access

# --- 3. FLASK SERVER ---
flask_app = Flask(__name__)
@flask_app.route("/")
def health(): return "MEX WAR SYSTEM ONLINE ⚔️", 200
def run_web(): flask_app.run(host="0.0.0.0", port=8080)

# --- 4. DATABASE ---
pool = None
async def init_db():
    global pool
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        print("✅ War System Database Linked")
    except: print("⚠️ DB Syncing...")

# --- 5. ETHEREUM WAR ENGINE (The Weapon) ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))

async def eth_radar(app: Application):
    print("⚔️ WAR SYSTEM: Scanning Ethereum Mempool...")
    last_block = 0

    while True:
        try:
            if VIP_CHANNEL_ID and w3.is_connected():
                current_block = w3.eth.block_number

                if current_block > last_block:
                    # Get Block Data
                    block = w3.eth.get_block(current_block, full_transactions=True)
                    last_block = current_block

                    # 1. SCAN FOR NEW CONTRACTS (Sniping)
                    # (Simplified: looking for tx with no 'to' address)
                    for tx in block.transactions:
                        # CHECK 1: New Contract Deployment
                        if tx['to'] is None:
                            hash_link = f"https://etherscan.io/tx/{tx['hash'].hex()}"
                            msg = (
                                f"🛡️ **NEW CONTRACT DEPLOYED**\n\n"
                                f"🧱 **Block:** {current_block}\n"
                                f"⛽ **Gas:** {tx['gas']}\n"
                                f"🔗 [Etherscan]({hash_link})\n\n"
                                f"⚠️ *Analyzing Code...* (Pending)"
                            )
                            # Only post 1 per block to avoid spam, or filtering for high value
                            if tx['value'] > 0: 
                                await app.bot.send_message(VIP_CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

                        # CHECK 2: Whale Movement (> 50 ETH)
                        val_eth = float(Web3.from_wei(tx['value'], 'ether'))
                        if val_eth > 50:
                            msg = (
                                f"🐋 **ETH WHALE MOVEMENT**\n\n"
                                f"💰 **Amount:** {val_eth:,.2f} ETH\n"
                                f"🧱 **Block:** {current_block}\n"
                                f"🔗 [View Transaction](https://etherscan.io/tx/{tx['hash'].hex()})"
                            )
                            await app.bot.send_message(VIP_CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

            await asyncio.sleep(10) # Poll every 10-12s (Block time)
        except Exception as e:
            print(f"Radar Jammed: {e}")
            await asyncio.sleep(5)

# --- 6. HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("⚔️ JOIN WAR ROOM ($100)", callback_data="buy_war")]]
    await update.message.reply_markdown(
        f"⚔️ **MEX WAR SYSTEM** ⚔️\n\n"
        "Ethereum Mempool Surveillance Unit.\n\n"
        "📡 **Capabilities:**\n"
        "• New Contract Sniffer\n"
        "• Gas War Detection\n"
        "• Whale Tracking (>50 ETH)\n\n"
        "👇 **Initialize Protocol:**",
        reply_markup=InlineKeyboardMarkup(kb)
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
            f"💰 **Price:** ${PRICE_WAR_ROOM} USD (ETH)\n"
            f"🏦 **Deposit:**\n`{ETH_MAIN}`\n\n"
            f"⚠️ **Reply:** `/confirm <TX_HASH>`"
        )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ Usage: /confirm 0xHash")
    tx = context.args[0]
    msg = await update.message.reply_text("🛰 **Scanning Mempool...**")

    # Simple Verification
    try:
        t = w3.eth.get_transaction(tx)
        if t.to.lower() != ETH_MAIN:
            await msg.edit_text("❌ Wrong Address.")
            return

        # Calculate Value
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd").json()
        price = r["ethereum"]["usd"]
        val_usd = float(Web3.from_wei(t.value, 'ether')) * price

        if val_usd >= (PRICE_WAR_ROOM * 0.95):
            # Success
            if pool:
                await pool.execute("INSERT INTO cp_payments (telegram_id, tx_hash, amount_usd, chain, created_at) VALUES ($1, $2, $3, 'ETH-WAR', $4)", str(update.effective_user.id), tx, PRICE_USD, int(time.time()))

            try: link = await context.bot.create_chat_invite_link(VIP_CHANNEL_ID, member_limit=1).invite_link
            except: link = "Contact Admin"

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
