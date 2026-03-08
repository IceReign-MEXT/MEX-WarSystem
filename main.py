#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS v6.2-SIMPLE - Guaranteed Working Version
Minimal features but fully operational
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import asyncio
import threading
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify

# Simple in-memory storage (works immediately)
memory_db = {
    'admins': {},
    'payments': [],
    'stats': {'total_revenue': 0.0, 'total_admins': 0}
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MASTER_WALLET = os.getenv("MASTER_WALLET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "10000"))

app = Flask(__name__)
application = None
bot_loop = None

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Master admin
    if user.id == ADMIN_ID:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Stats", callback_data="stats")],
            [InlineKeyboardButton("💰 Wallet", callback_data="wallet")]
        ])
        
        await update.message.reply_text(
            f"""👑 MASTER DASHBOARD

✅ Bot: ONLINE (Memory Mode)
💰 Revenue: {memory_db['stats']['total_revenue']:.2f} SOL
👥 Admins: {memory_db['stats']['total_admins']}

Wallet: `{MASTER_WALLET[:20]}...`

⚡ All systems operational!""",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return
    
    # Regular user
    admin = memory_db['admins'].get(user.id)
    
    if admin and admin.get('expires_at') and admin['expires_at'] > datetime.utcnow():
        days = (admin['expires_at'] - datetime.utcnow()).days
        await update.message.reply_text(
            f"""⚡ YOUR DASHBOARD

✅ Status: ACTIVE
⏰ Expires: {days} days

🚀 Features:
• Deploy white-label bots
• Auto token detection  
• Airdrop distribution
• Revenue sharing

Click buttons below 👇""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Deploy Bot", callback_data="deploy")],
                [InlineKeyboardButton("💎 Referral", callback_data="referral")]
            ])
        )
    else:
        # New user
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Monthly (5 SOL)", callback_data="pay_monthly")],
            [InlineKeyboardButton("👑 Yearly (50 SOL)", callback_data="pay_yearly")]
        ])
        
        await update.message.reply_text(
            f"""🚀 ICEGODS Bot Platform

Deploy professional token alert bots!

💎 FEATURES:
✅ Auto-detect new launches
✅ VIP/Whale/Premium tiers
✅ Automatic airdrops
✅ You keep 80% revenue

📊 PRICING:
• Monthly: 5 SOL
• Yearly: 50 SOL

⚡ Limited spots available!

👇 Click to subscribe""",
            reply_markup=keyboard
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "pay_monthly":
        await query.message.edit_text(
            f"""🧾 PAYMENT: Monthly Plan

Amount: 5 SOL
Duration: 30 days

SEND TO:
`{MASTER_WALLET}`

After paying:
/confirm TRANSACTION_HASH

⚡ Instant activation!""",
            parse_mode='Markdown'
        )
    elif query.data == "stats":
        await query.message.edit_text(
            f"""📊 PLATFORM STATS

Admins: {memory_db['stats']['total_admins']}
Revenue: {memory_db['stats']['total_revenue']:.2f} SOL

Status: ✅ ONLINE"""
        )

def run_bot():
    global application, bot_loop
    asyncio.set_event_loop(asyncio.new_event_loop())
    bot_loop = asyncio.get_event_loop()
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    bot_loop.run_until_complete(application.initialize())
    
    if WEBHOOK_URL:
        webhook_path = f"/webhook/{BOT_TOKEN.split(':')[1]}"
        bot_loop.run_until_complete(application.bot.set_webhook(url=f"{WEBHOOK_URL}{webhook_path}"))
    
    bot_loop.run_until_complete(application.start())
    bot_loop.run_forever()

@app.route("/")
def health():
    return jsonify({
        "status": "ICEGODS v6.2-SIMPLE ONLINE",
        "mode": "memory",
        "admins": len(memory_db['admins']),
        "time": datetime.utcnow().isoformat()
    })

@app.route(f"/webhook/{BOT_TOKEN.split(':')[1]}", methods=['POST'])
def webhook():
    if not application:
        return jsonify({"error": "Not ready"}), 503
    
    try:
        data = request.get_json()
        update = Update.de_json(data, application.bot)
        
        # Process in bot's loop
        future = asyncio.run_coroutine_threadsafe(
            application.process_update(update),
            bot_loop
        )
        future.result(timeout=10)
        
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

def main():
    # Start bot thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Wait for ready
    import time
    time.sleep(3)
    
    # Start Flask
    app.run(host="0.0.0.0", port=PORT, threaded=False)

if __name__ == "__main__":
    main()

