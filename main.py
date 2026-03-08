#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS v7.0 - VIRAL GROWTH WEAPON
Auto-recruits users, creates FOMO, generates content, tracks everything
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import asyncio
import threading
import logging
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MASTER_WALLET = os.getenv("MASTER_WALLET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "10000"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "ICEMEXWarSystem_Bot")

# ═══════════════════════════════════════════════════════════════════════
# IN-MEMORY DATABASE
# ═══════════════════════════════════════════════════════════════════════

class ViralDB:
    def __init__(self):
        self.admins = {}
        self.payments = []
        self.visits_today = 0
        self.joins_today = 0
        self.spots_remaining = 47
        self.price_increase_time = datetime.utcnow() + timedelta(hours=24)
        self.success_stories = [
            {"name": "CryptoWhale", "profit": 45.5, "time": "2 hours ago"},
            {"name": "SolanaKing", "profit": 128.0, "time": "5 hours ago"},
            {"name": "DeFiQueen", "profit": 67.2, "time": "1 day ago"},
        ]
    
    def get_or_create_admin(self, user_id, username=None, first_name=None):
        if user_id not in self.admins:
            import secrets
            self.admins[user_id] = {
                'id': user_id,
                'username': username,
                'first_name': first_name,
                'referral_code': secrets.token_hex(4),
                'referrals': 0,
                'expires_at': None,
                'joined_at': datetime.utcnow(),
                'bots_deployed': 0,
                'earnings': 0.0
            }
            self.joins_today += 1
            self.spots_remaining = max(0, self.spots_remaining - 1)
        return self.admins[user_id]
    
    def get_stats(self):
        active = sum(1 for a in self.admins.values() if a.get('expires_at') and a['expires_at'] > datetime.utcnow())
        total_revenue = sum(p['amount'] for p in self.payments)
        return {
            'total': len(self.admins),
            'active': active,
            'revenue': total_revenue,
            'visits_today': self.visits_today,
            'joins_today': self.joins_today,
            'spots_left': self.spots_remaining
        }

db = ViralDB()

# ═══════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Viral entry point"""
    user = update.effective_user
    db.visits_today += 1
    
    # Track referral
    if context.args:
        source = context.args[0]
        if source.startswith("ref_"):
            referrer_id = int(source.replace("ref_", ""))
            if referrer_id in db.admins and referrer_id != user.id:
                db.admins[referrer_id]['referrals'] += 1
                try:
                    await context.bot.send_message(
                        referrer_id,
                        f"🎉 @{user.username or user.first_name} joined via your link!"
                    )
                except:
                    pass
    
    admin = db.get_or_create_admin(user.id, user.username, user.first_name)
    
    # MASTER PANEL
    if user.id == ADMIN_ID:
        stats = db.get_stats()
        await update.message.reply_text(
            f"""👑 MASTER CONTROL

📊 METRICS:
• Users: {stats['total']} (Active: {stats['active']})
• Revenue: {stats['revenue']:.2f} SOL
• Today: {stats['visits_today']} visits, {stats['joins_today']} joins
• Spots Left: {stats['spots_left']}

💰 Wallet: `{MASTER_WALLET[:20]}...`

⚡ Status: ONLINE""",
            parse_mode='Markdown'
        )
        return
    
    # CHECK SUBSCRIPTION
    if admin.get('expires_at') and admin['expires_at'] > datetime.utcnow():
        await show_dashboard(update, context, admin)
        return
    
    # VIRAL LANDING
    countdown = int((db.price_increase_time - datetime.utcnow()).total_seconds() / 3600)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 CLAIM SPOT NOW", callback_data="buy_monthly")],
        [InlineKeyboardButton("👑 Yearly (Save 20%)", callback_data="buy_yearly")],
        [InlineKeyboardButton("📊 See Demo", url="https://t.me/Icegods_Bridge_bot")],
        [InlineKeyboardButton("💬 Join Channel", url="https://t.me/ICEGODSICEDEVIL")]
    ])
    
    await update.message.reply_text(
        f"""🚀 ICEGODS BOT PLATFORM

🔥 {random.choice(db.success_stories)['name']} earned {random.choice(db.success_stories)['profit']} SOL today!
⚡ Only {db.spots_remaining} spots left!
⏰ Price increases in {max(0, countdown)} hours!

💎 WHAT YOU GET:
━━━━━━━━━━━━━━━━━━━━━
✅ White-label token alert bot
✅ Auto-detect 100x gems
✅ VIP/Whale/Premium tiers
✅ Automatic SOL payments
✅ Airdrop distribution
✅ 80% revenue share

💰 EXAMPLE EARNINGS:
100 subscribers = 56 SOL/month ≈ $8,400

🎁 REFER 3 FRIENDS = FREE ACCESS

👇 CLICK BELOW TO START 👇""",
        reply_markup=keyboard
    )

async def show_dashboard(update, context, admin):
    """Active user dashboard"""
    days_left = (admin['expires_at'] - datetime.utcnow()).days
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Deploy Bot", callback_data="deploy")],
        [InlineKeyboardButton("💎 Referral Link", callback_data="referral")],
        [InlineKeyboardButton("💰 Earnings", callback_data="earnings")]
    ])
    
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{admin['id']}"
    
    await update.message.reply_text(
        f"""⚡ YOUR DASHBOARD

✅ Active | {days_left} days left
🤖 Bots: {admin['bots_deployed']}/10
💰 Earned: {admin['earnings']:.2f} SOL
👥 Referrals: {admin['referrals']}

🔗 YOUR LINK:
`{link}`

🎯 Refer 3 = FREE subscription!

🚀 Deploy bot to start earning!""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buttons"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "buy_monthly":
        await show_payment(query, "monthly", 5.0)
    elif query.data == "buy_yearly":
        await show_payment(query, "yearly", 50.0)
    elif query.data == "referral":
        await show_referral(query, user_id)
    elif query.data == "deploy":
        await query.message.edit_text("🚀 Send your bot token from @BotFather:")
    elif query.data == "earnings":
        await query.message.edit_text("💰 Deploy a bot first to see earnings!")
    elif query.data == "main_menu":
        await cmd_start(update, context)

async def show_payment(query, plan, amount):
    """Payment page"""
    await query.message.edit_text(
        f"""🧾 {plan.upper()} PLAN

Amount: {amount} SOL
Wallet: `{MASTER_WALLET}`

Send SOL, then:
/confirm TRANSACTION_HASH

⚡ Only {db.spots_remaining} spots left!""",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Help", url="https://t.me/MexRobert")]
        ])
    )

async def show_referral(query, user_id):
    """Referral page"""
    admin = db.admins.get(user_id, {})
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    
    await query.message.edit_text(
        f"""🎁 REFERRAL PROGRAM

🔗 Your Link:
`{link}`

👥 Referrals: {admin.get('referrals', 0)}
🎯 Next: {3 - (admin.get('referrals', 0) % 3)} more = +3 days!

Share to:
• Telegram groups
• Twitter/X
• Discord

🔙 Back: /start""",
        parse_mode='Markdown'
    )

# ═══════════════════════════════════════════════════════════════════════
# WEB SERVER
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)

@app.route("/")
def health():
    stats = db.get_stats()
    return jsonify({
        "status": "ICEGODS v7.0 ONLINE",
        "users": stats['total'],
        "revenue": stats['revenue'],
        "spots_left": stats['spots_left']
    })

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    logger.info("🚀 ICEGODS v7.0 STARTING")
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    async def run():
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        logger.info("✅ Bot polling started!")
        while True:
            await asyncio.sleep(3600)
    
    def bot_thread():
        asyncio.run(run())
    
    threading.Thread(target=bot_thread, daemon=True).start()
    
    import time
    time.sleep(2)
    
    logger.info(f"🌐 Web server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=False)

if __name__ == "__main__":
    main()
