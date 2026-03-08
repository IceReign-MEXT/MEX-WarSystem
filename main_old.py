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

# VIRAL MECHANICS CONFIG
FAKE_SCARCITY = True  # Show "X spots left"
FAKE_SOCIAL_PROOF = True  # Show "Y people joined today"
URGENCY_TIMER = True  # Countdown to price increase
REFERRAL_REWARD = 3  # Days per referral

# ═══════════════════════════════════════════════════════════════════════
# IN-MEMORY DATABASE (with viral tracking)
# ═══════════════════════════════════════════════════════════════════════

class ViralDB:
    def __init__(self):
        self.admins = {}
        self.payments = []
        self.visits_today = 0
        self.joins_today = 0
        self.spots_remaining = 50  # Fake scarcity
        self.price_increase_time = datetime.utcnow() + timedelta(hours=24)
        self.success_stories = [
            {"name": "CryptoWhale", "profit": 45.5, "time": "2 hours ago"},
            {"name": "SolanaKing", "profit": 128.0, "time": "5 hours ago"},
            {"name": "DeFiQueen", "profit": 67.2, "time": "1 day ago"},
        ]
        self.last_alert = None
    
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
# VIRAL CONTENT GENERATOR
# ═══════════════════════════════════════════════════════════════════════

def generate_fomo_text():
    """Generate urgency/scarcity messages"""
    texts = [
        f"🔥 {random.randint(3, 8)} people joined in the last hour",
        f"⚡ Only {db.spots_remaining} spots left at this price",
        f"📈 Price increases in {random.randint(2, 8)} hours",
        f"💎 {random.choice(db.success_stories)['name']} just earned {random.choice(db.success_stories)['profit']} SOL",
        f"🚀 {db.joins_today} entrepreneurs joined today",
    ]
    return random.choice(texts)

def get_countdown():
    """Get time until price increase"""
    remaining = db.price_increase_time - datetime.utcnow()
    hours = int(remaining.total_seconds() / 3600)
    return max(0, hours)

# ═══════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Viral entry point with maximum conversion optimization"""
    user = update.effective_user
    db.visits_today += 1
    
    # Track source
    source = "direct"
    if context.args:
        source = context.args[0]
        if source.startswith("ref_"):
            referrer_id = int(source.replace("ref_", ""))
            if referrer_id in db.admins and referrer_id != user.id:
                db.admins[referrer_id]['referrals'] += 1
                # Notify referrer
                try:
                    await context.bot.send_message(
                        referrer_id,
                        f"🎉 @{user.username or user.first_name} joined via your link!\n"
                        f"⏰ +{REFERRAL_REWARD} days added when they pay!"
                    )
                except:
                    pass
    
    admin = db.get_or_create_admin(user.id, user.username, user.first_name)
    
    # MASTER ADMIN PANEL
    if user.id == ADMIN_ID:
        stats = db.get_stats()
        await update.message.reply_text(
            f"""👑 MASTER CONTROL

📊 VIRAL METRICS:
• Total Users: {stats['total']}
• Active: {stats['active']}
• Revenue: {stats['revenue']:.2f} SOL
• Today's Visits: {stats['visits_today']}
• Today's Joins: {stats['joins_today']}
• Spots Left: {stats['spots_left']}

🧪 A/B TESTING:
• Fake Scarcity: {'ON' if FAKE_SCARCITY else 'OFF'}
• Social Proof: {'ON' if FAKE_SOCIAL_PROOF else 'OFF'}
• Urgency Timer: {'ON' if URGENCY_TIMER else 'OFF'}

💰 Wallet: `{MASTER_WALLET[:20]}...`""",
            parse_mode='Markdown'
        )
        return
    
    # CHECK IF SUBSCRIBED
    if admin.get('expires_at') and admin['expires_at'] > datetime.utcnow():
        await show_dashboard(update, context, admin)
        return
    
    # VIRAL LANDING PAGE (non-subscribers)
    fomo_line = generate_fomo_text() if FAKE_SOCIAL_PROOF else ""
    countdown = get_countdown()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 CLAIM YOUR SPOT NOW", callback_data="buy_monthly")],
        [InlineKeyboardButton("👑 Yearly (Save 20%)", callback_data="buy_yearly")],
        [InlineKeyboardButton("📊 See Live Demo", url="https://t.me/Icegods_Bridge_bot")],
        [InlineKeyboardButton("💬 Join Community", url="https://t.me/CHINACRYPTOCROSSCHAINSNETWORKS")]
    ])
    
    # Build viral landing text
    text = f"""🚀 ICEGODS BOT PLATFORM

{fomo_line}

💎 WHAT YOU GET:
━━━━━━━━━━━━━━━━━━━━━
✅ White-label token alert bot (YOUR brand)
✅ Auto-detect 100x gems before Twitter knows
✅ VIP/Whale/Premium subscription tiers
✅ Automatic SOL payment collection
✅ Built-in airdrop distribution
✅ 80% revenue share (you keep most!)

💰 REVENUE EXAMPLE:
• 50 VIP subscribers × 0.5 SOL = 25 SOL/month
• 20 Whale subscribers × 1 SOL = 20 SOL/month  
• 10 Premium × 2.5 SOL = 25 SOL/month
• YOUR PROFIT (80%): 56 SOL/month ≈ $8,400

⚡ LIMITED OFFER:
⏰ Price increases in {countdown} hours!
🔥 Only {db.spots_remaining} spots left at 5 SOL/month

🎁 VIRAL BONUS:
Refer 3 friends → Get FREE access forever!

👇 CLICK BELOW TO SECURE YOUR SPOT 👇"""
    
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def show_dashboard(update, context, admin):
    """Show active user dashboard"""
    days_left = (admin['expires_at'] - datetime.utcnow()).days
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Deploy Bot", callback_data="deploy")],
        [InlineKeyboardButton("💎 Referral Link", callback_data="referral")],
        [InlineKeyboardButton("💰 Earnings", callback_data="earnings")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ])
    
    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{admin['id']}"
    
    await update.message.reply_text(
        f"""⚡ YOUR DASHBOARD

✅ Status: ACTIVE
⏰ Expires: {days_left} days
🤖 Bots: {admin['bots_deployed']}/10
💰 Earned: {admin['earnings']:.2f} SOL
👥 Referrals: {admin['referrals']}

🔗 YOUR VIRAL LINK:
`{referral_link}`

📈 REFER & EARN:
• 3 referrals = FREE subscription
• 10 referrals = +5 bot slots
• 25 referrals = Featured partner

🚀 Deploy your first bot to start earning!""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all buttons"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "buy_monthly":
        await show_payment_page(query, "monthly", 5.0, 30)
    elif data == "buy_yearly":
        await show_payment_page(query, "yearly", 50.0, 365)
    elif data == "referral":
        await show_referral(query, user_id)
    elif data == "deploy":
        await start_deploy(query, user_id)
    elif data == "earnings":
        await show_earnings(query, user_id)
    elif data == "main_menu":
        # Trigger start
        class FakeUpdate:
            def __init__(self, msg):
                self.message = msg
                self.effective_user = msg.from_user
        await cmd_start(FakeUpdate(query.message), context)

async def show_payment_page(query, plan, amount, days):
    """Payment page with urgency"""
    countdown = get_countdown()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I SENT PAYMENT", callback_data=f"paid_{plan}")],
        [InlineKeyboardButton("❓ Need Help", url=f"https://t.me/{os.getenv('SUPPORT_USERNAME', 'MexRobert')}")]
    ])
    
    await query.message.edit_text(
        f"""🧾 SECURE YOUR {plan.upper()} ACCESS

⚡ PRICE INCREASES IN {countdown} HOURS!

━━━━━━━━━━━━━━━━━━━━━
Plan: {plan.upper()}
Duration: {days} days  
Amount: {amount} SOL
You Save: {'17%' if plan == 'yearly' else '0%'}
━━━━━━━━━━━━━━━━━━━━━

📤 SEND {amount} SOL TO:
`{MASTER_WALLET}`

⚠️ IMPORTANT:
• Send EXACTLY {amount} SOL
• Only SOL (not USDC or tokens)
• Save your transaction hash

✅ AFTER PAYING:
Use command:
/confirm YOUR_TX_HASH

🔒 SECURE CHECKOUT
⏰ Spots remaining: {db.spots_remaining}

💬 Issues? Contact @MexRobert""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def show_referral(query, user_id):
    """Show referral page"""
    admin = db.admins.get(user_id, {})
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Share to Telegram", url=f"https://t.me/share/url?url={link}&text=🔥 I just found this bot platform for crypto alerts - you can deploy your own and earn SOL!")],
        [InlineKeyboardButton("🐦 Share to Twitter", url=f"https://twitter.com/intent/tweet?text=Just%20found%20this%20insane%20bot%20platform%20for%20crypto%20alerts%20-%20earn%20passive%20SOL!%20{link}")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        f"""🎁 VIRAL REFERRAL PROGRAM

🔗 YOUR UNIQUE LINK:
`{link}`

📊 YOUR STATS:
• Referrals: {admin.get('referrals', 0)}
• Free Days Earned: {admin.get('referrals', 0) * 3}
• Next Reward: {3 - (admin.get('referrals', 0) % 3)} more for +3 days

🎯 REWARD TIERS:
• 3 referrals = +3 days free
• 10 referrals = FREE forever + 5 bots
• 25 referrals = Partner status (20% commission!)

📈 TOP PERFORMERS:
@CryptoWhale - 47 referrals
@SolanaKing - 32 referrals  
@DeFiQueen - 28 referrals

🚀 Share everywhere:
• Crypto Telegram groups
• Twitter/X threads
• Discord communities
• Reddit r/Solana""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def start_deploy(query, user_id):
    """Start bot deployment"""
    await query.message.edit_text(
        """🚀 BOT DEPLOYMENT WIZARD

Step 1/3: Get Bot Token

1. Message @BotFather
2. Send /newbot
3. Name your bot (e.g., "AlphaAlertsBot")
4. Copy the token (looks like: 123456:ABC...)

Send me your bot token:
(Or click /cancel to exit)"""
    )

async def show_earnings(query, user_id):
    """Show earnings with projections"""
    admin = db.admins.get(user_id, {})
    
    # Fake projection based on their potential
    potential = 50.0  # SOL per month if they get 100 subs
    
    await query.message.edit_text(
        f"""💰 EARNINGS DASHBOARD

Current: {admin.get('earnings', 0):.2f} SOL

📈 PROJECTIONS:
If you deploy 1 bot with:
• 50 VIP (0.5 SOL) = 25 SOL/month
• 20 Whale (1 SOL) = 20 SOL/month
• 10 Premium (2.5 SOL) = 25 SOL/month
━━━━━━━━━━━━━━━━━━━━━
Total: 70 SOL/month
Your 80%: 56 SOL ≈ $8,400/month

🎯 TO REACH THIS:
1. Deploy bot (Step 1)
2. Post in 5 crypto groups daily
3. Offer first week free
4. Use referral system

⚡ START NOW: /deploy""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Deploy Now", callback_data="deploy")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
    )

# ═══════════════════════════════════════════════════════════════════════
# AUTO-MARKETING SYSTEM
# ═══════════════════════════════════════════════════════════════════════

async def auto_marketing_loop():
    """Post to channels automatically"""
    while True:
        try:
            # Every 2 hours, post success story
            await asyncio.sleep(7200)
            
            story = random.choice(db.success_stories)
            messages = [
                f"🔥 @{story['name']} just made {story['profit']} SOL with their bot! Deploy yours: https://t.me/{BOT_USERNAME}",
                f"⚡ New token detected 10 minutes before 50x pump! Get early access: https://t.me/{BOT_USERNAME}",
                f"💎 {db.joins_today} entrepreneurs joined ICEGODS today. Only {db.spots_remaining} spots left!",
            ]
            
            msg = random.choice(messages)
            logger.info(f"Auto-marketing: {msg[:50]}...")
            
            # In production, this posts to your channels
            # await bot.send_message("@yourchannel", msg)
            
        except Exception as e:
            logger.error(f"Marketing error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# WEB SERVER
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)

@app.route("/")
def health():
    stats = db.get_stats()
    return jsonify({
        "status": "ICEGODS v7.0 VIRAL MODE",
        "users": stats['total'],
        "active": stats['active'],
        "revenue": stats['revenue'],
        "visits_today": stats['visits_today'],
        "spots_left": stats['spots_left'],
        "viral_mechanics": {
            "scarcity": FAKE_SCARCITY,
            "social_proof": FAKE_SOCIAL_PROOF,
            "urgency": URGENCY_TIMER
        }
    })

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    logger.info("=" * 60)
    logger.info("ICEGODS v7.0 - VIRAL GROWTH WEAPON")
    logger.info("=" * 60)
    
    # Setup bot
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start polling (simple, no webhook needed for testing)
    async def run():
        await application.initialize()
        await application.start()
        
        # Start auto-marketing
        asyncio.create_task(auto_marketing_loop())
        
        # Start polling
        await application.updater.start_polling()
        logger.info("✅ Bot polling started")
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
    
    # Run in thread
    def bot_thread():
        asyncio.run(run())
    
    threading.Thread(target=bot_thread, daemon=True).start()
    
    # Wait then start Flask
    import time
    time.sleep(2)
    
    logger.info(f"Starting web server on {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=False)

if __name__ == "__main__":
    main()

