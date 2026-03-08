#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS BOT PLATFORM v6.0 - PRODUCTION SaaS WITH AIRDROP SYSTEM
Master bot that deploys white-label client bots + automatic token distribution
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import asyncio
import threading
import logging
import aiohttp
import json
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify

# Import our modules
from database import init_db, SessionLocal, get_or_create_admin, check_subscription, add_referral_reward, get_stats, Admin, Payment, ClientBot
from airdrop_manager import AirdropManager, run_airdrop_scheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION FROM ENVIRONMENT
# ═══════════════════════════════════════════════════════════════════════

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MASTER_WALLET = os.getenv("MASTER_WALLET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))
HELIUS_KEY = os.getenv("HELIUS_API_KEY")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@MexRobert")

SAAS_MONTHLY = float(os.getenv("SAAS_MONTHLY_PRICE", 5.0))
SAAS_YEARLY = float(os.getenv("SAAS_YEARLY_PRICE", 50.0))
REFERRAL_REWARD_DAYS = int(os.getenv("REFERRAL_REWARD_DAYS", 3))
MAX_CLIENTS_PER_ADMIN = int(os.getenv("MAX_CLIENTS_PER_ADMIN", 10))

if not all([BOT_TOKEN, ADMIN_ID, MASTER_WALLET]):
    raise ValueError("Missing required environment variables!")

# ═══════════════════════════════════════════════════════════════════════
# GLOBALS
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
application = None
bot_loop = None

# ═══════════════════════════════════════════════════════════════════════
# HELIUS PAYMENT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

async def verify_payment_by_tx(tx_hash, expected_amount):
    """Verify Solana transaction via Helius"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_KEY}"
            payload = {"transactions": [tx_hash]}
            
            async with session.post(url, json=payload, timeout=30) as resp:
                if resp.status != 200:
                    return False, 0
                
                data = await resp.json()
                if not data or not isinstance(data, list):
                    return False, 0
                
                tx = data[0]
                transfers = tx.get('nativeTransfers', [])
                
                for transfer in transfers:
                    if transfer.get('toUserAccount') == MASTER_WALLET:
                        amount_sol = transfer.get('amount', 0) / 1_000_000_000
                        if abs(amount_sol - expected_amount) < 0.01:
                            return True, amount_sol
                
                return False, 0
                
    except Exception as e:
        logger.error(f"Verify error: {e}")
        return False, 0

# ═══════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main entry point with viral referral system"""
    user = update.effective_user
    db = SessionLocal()
    
    try:
        # Check for referral code in deep link
        referral_code = None
        if context.args and len(context.args) > 0:
            referral_code = context.args[0]
        
        # Get or create admin
        admin = get_or_create_admin(db, user.id, user.username, user.first_name)
        
        # Process referral if new user
        if referral_code and admin.created_at > datetime.utcnow() - timedelta(minutes=1):
            referrer = db.query(Admin).filter(Admin.referral_code == referral_code).first()
            if referrer and referrer.telegram_id != user.id:
                add_referral_reward(db, referrer.telegram_id, REFERRAL_REWARD_DAYS)
                await context.bot.send_message(
                    referrer.telegram_id,
                    f"🎉 New referral! @{user.username or user.id} joined using your code!\n"
                    f"⏰ +{REFERRAL_REWARD_DAYS} days added to your subscription!"
                )
        
        # Master admin panel
        if user.id == ADMIN_ID:
            stats = get_stats(db)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Stats", callback_data="master_stats")],
                [InlineKeyboardButton("💰 Revenue", callback_data="master_revenue")],
                [InlineKeyboardButton("👥 Admins", callback_data="master_admins")],
                [InlineKeyboardButton("🤖 Deployments", callback_data="master_bots")]
            ])
            
            await update.message.reply_text(
                f"""👑 ICEGODS MASTER DASHBOARD

💎 Platform Statistics:
• Total Admins: {stats['total_admins']}
• Active Subs: {stats['active_admins']}
• Bots Deployed: {stats['total_bots']}
• Revenue: {stats['total_revenue_sol']:.2f} SOL

💳 Master Wallet:
`{MASTER_WALLET[:20]}...`

⚡ Status: ONLINE
🔄 Airdrop System: ACTIVE""",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            return
        
        # Check subscription status
        is_active, days_left = check_subscription(db, user.id)
        
        if is_active:
            bots_count = len(admin.client_bots)
            max_bots = admin.max_clients
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Deploy New Bot", callback_data="deploy_bot")],
                [InlineKeyboardButton("⚙️ My Bots", callback_data="my_bots")],
                [InlineKeyboardButton("🎁 Create Airdrop", callback_data="create_airdrop")],
                [InlineKeyboardButton("📢 Marketing Tools", callback_data="marketing")],
                [InlineKeyboardButton("💎 Referral Program", callback_data="referral")]
            ])
            
            await update.message.reply_text(
                f"""⚡ ADMIN PANEL

✅ Status: ACTIVE
⏰ Expires: {days_left} days
🤖 Bots: {bots_count}/{max_bots}
💰 Earned: {admin.total_earned_sol:.2f} SOL

🔗 Your Referral Code: `{admin.referral_code}`
👥 Referrals: {admin.referral_count}

🚀 Deploy your white-label bot and start earning!""",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            # New or expired - show pricing with referral option
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💎 Monthly ({SAAS_MONTHLY} SOL)", callback_data="sub_monthly")],
                [InlineKeyboardButton(f"👑 Yearly ({SAAS_YEARLY} SOL)", callback_data="sub_yearly")],
                [InlineKeyboardButton("🎁 Have Referral Code?", callback_data="enter_referral")]
            ])
            
            await update.message.reply_text(
                f"""🚀 ICEGODS Bot Platform

Deploy your own token alert bot empire!

💎 WHAT YOU GET:
✅ White-label Telegram bot (your brand)
✅ Automated token alerts (DexScreener)
✅ Subscription management (VIP/Whale/Premium)
✅ Automatic airdrop distribution
✅ Revenue dashboard (you keep 80%)

💰 YOUR EARNINGS:
• Set your own prices (VIP/Whale/Premium)
• Keep 80% of all subscriber payments
• Passive SOL income 24/7

📊 PRICING:
• Monthly: {SAAS_MONTHLY} SOL
• Yearly: {SAAS_YEARLY} SOL (Save 17%)

🔥 VIRAL BONUS:
Refer 3 friends = +3 days free + 1 extra bot slot!

Tap below to start 👇""",
                reply_markup=keyboard
            )
    
    finally:
        db.close()

async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify payment and activate subscription"""
    user = update.effective_user
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            """🛰 PAYMENT VERIFICATION

Usage: /confirm TRANSACTION_HASH

After sending SOL, paste your transaction hash here."""
        )
        return
    
    tx_hash = context.args[0].strip()
    
    if len(tx_hash) < 80:
        await update.message.reply_text("❌ Invalid transaction hash")
        return
    
    await update.message.reply_text("🛰 Verifying on Solana blockchain...")
    
    db = SessionLocal()
    try:
        # Check if tx already used
        existing = db.query(Payment).filter(Payment.tx_hash == tx_hash).first()
        if existing:
            await update.message.reply_text("❌ This transaction was already used!")
            return
        
        # Try monthly then yearly
        for plan_type, amount, days in [
            ('monthly', SAAS_MONTHLY, 30),
            ('yearly', SAAS_YEARLY, 365)
        ]:
            success, actual_amount = await verify_payment_by_tx(tx_hash, amount)
            
            if success:
                admin = get_or_create_admin(db, user.id, user.username, user.first_name)
                
                # Set expiration
                if admin.expires_at and admin.expires_at > datetime.utcnow():
                    admin.expires_at += timedelta(days=days)
                else:
                    admin.expires_at = datetime.utcnow() + timedelta(days=days)
                
                admin.plan_type = plan_type
                admin.is_active = True
                
                # Record payment
                payment = Payment(
                    admin_id=user.id,
                    amount_sol=actual_amount,
                    plan_type=plan_type,
                    tx_hash=tx_hash,
                    status='confirmed',
                    confirmed_at=datetime.utcnow()
                )
                db.add(payment)
                db.commit()
                
                await update.message.reply_text(
                    f"""✅ PAYMENT VERIFIED!

🎉 Subscription: {plan_type.upper()}
⏰ Duration: {days} days
📅 Expires: {admin.expires_at.strftime('%Y-%m-%d')}
💰 Amount: {actual_amount:.4f} SOL

🚀 Click /start to access your dashboard!"""
                )
                
                # Notify master
                await context.bot.send_message(
                    ADMIN_ID,
                    f"💰 NEW SUB!\nUser: {user.id}\nPlan: {plan_type}\nAmount: {actual_amount:.4f} SOL"
                )
                return
        
        await update.message.reply_text(
            """❌ PAYMENT NOT FOUND

Check:
• Did you send exactly 5 or 50 SOL?
• Is it confirmed? (wait 1-2 min)
• Correct wallet? 

Support: """ + SUPPORT_USERNAME
        )
    
    finally:
        db.close()

async def cmd_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral status"""
    db = SessionLocal()
    try:
        admin = get_or_create_admin(db, update.effective_user.id)
        
        referral_link = f"https://t.me/{context.bot.username}?start={admin.referral_code}"
        
        await update.message.reply_text(
            f"""🎁 REFERRAL PROGRAM

🔗 Your Link:
`{referral_link}`

📊 Stats:
• Referrals: {admin.referral_count}
• Next Reward: {3 - (admin.referral_count % 3)} more for +3 days

💎 Rewards:
• Each referral = +3 days subscription
• Every 3 referrals = +1 bot slot (max {MAX_CLIENTS_PER_ADMIN})

Share your link to earn free access!""",
            parse_mode='Markdown'
        )
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════════════════
# BUTTON HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline buttons"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    db = SessionLocal()
    try:
        if data == "sub_monthly":
            await show_payment_invoice(query, user_id, "monthly", SAAS_MONTHLY, 30)
        elif data == "sub_yearly":
            await show_payment_invoice(query, user_id, "yearly", SAAS_YEARLY, 365)
        elif data == "deploy_bot":
            await start_deployment(query, user_id)
        elif data == "create_airdrop":
            await show_airdrop_menu(query, user_id)
        elif data == "referral":
            await show_referral_status(query, user_id)
        elif data == "master_stats":
            await show_master_stats(query)
        elif data.startswith("deploy_"):
            await process_deployment_step(query, user_id, data, context)
        elif data == "main_menu":
            await back_to_main(query, context)
    
    finally:
        db.close()

async def show_payment_invoice(query, user_id, plan_type, amount, days):
    """Show payment instructions"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I've Paid - Confirm", callback_data=f"confirm_{plan_type}")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        f"""🧾 INVOICE

Plan: {plan_type.upper()}
Duration: {days} days
Amount: {amount} SOL

═══════════════════
SEND EXACTLY {amount} SOL TO:
`{MASTER_WALLET}`
═══════════════════

⚠️ Send ONLY SOL (SPL tokens not accepted)

After sending, use:
/confirm YOUR_TX_HASH

Or click "I've Paid" and paste your hash.""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def start_deployment(query, user_id):
    """Start bot deployment wizard"""
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == user_id).first()
        
        if not admin or not admin.expires_at or admin.expires_at < datetime.utcnow():
            await query.message.edit_text("❌ Active subscription required!")
            return
        
        if len(admin.client_bots) >= admin.max_clients:
            await query.message.edit_text(
                f"""❌ Bot Limit Reached

You have {len(admin.client_bots)}/{admin.max_clients} bots.

Upgrade options:
• Refer 3 friends = +1 slot
• Contact {SUPPORT_USERNAME} for upgrade"""
            )
            return
        
        # Start deployment wizard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Start Setup", callback_data="deploy_step1")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")]
        ])
        
        await query.message.edit_text(
            """🚀 BOT DEPLOYMENT WIZARD

I'll create your white-label bot in 3 steps:

1️⃣ Bot Token (from @BotFather)
2️⃣ Channel ID (for alerts)
3️⃣ Your Wallet (for payments)

⚡ Takes 2 minutes to go live!

Ready?""",
            reply_markup=keyboard
        )
    
    finally:
        db.close()

async def show_airdrop_menu(query, user_id):
    """Show airdrop creation interface"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 New Airdrop", callback_data="airdrop_new")],
        [InlineKeyboardButton("📊 History", callback_data="airdrop_history")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        """🎁 AIRDROP MANAGER

Distribute tokens automatically to your subscribers!

Features:
• Auto-distribute by tier (VIP/Whale/Premium)
• Schedule for token launch day
• Track delivery status
• Anti-sybil protection

Select an option:""",
        reply_markup=keyboard
    )

async def show_referral_status(query, user_id):
    """Show referral dashboard"""
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == user_id).first()
        bot_username = query.message.bot.username
        referral_link = f"https://t.me/{bot_username}?start={admin.referral_code}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={referral_link}&text=Join%20ICEGODS%20Bot%20Platform%20-%20Deploy%20your%20own%20token%20alert%20bot!")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
        
        await query.message.edit_text(
            f"""🎁 YOUR REFERRAL DASHBOARD

🔗 Your Link:
`{referral_link}`

📊 Statistics:
• Total Referrals: {admin.referral_count}
• Free Days Earned: {admin.referral_count * 3} days
• Bot Slots Earned: {admin.referral_count // 3}

🎯 Next Reward:
Refer {3 - (admin.referral_count % 3)} more = +3 days + 1 bot slot!

Share to crypto groups, Twitter, Discord!""",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    finally:
        db.close()

async def show_master_stats(query):
    """Master admin statistics"""
    db = SessionLocal()
    try:
        stats = get_stats(db)
        
        await query.message.edit_text(
            f"""📊 PLATFORM STATISTICS

👥 Users:
• Total Admins: {stats['total_admins']}
• Active: {stats['active_admins']}

🤖 Bots:
• Deployed: {stats['total_bots']}
• Active: {stats['active_bots']}

💰 Revenue:
• Total: {stats['total_revenue_sol']:.2f} SOL

⚡ System Status: ONLINE"""
        )
    finally:
        db.close()

async def back_to_main(query, context):
    """Return to main menu"""
    # Create fake update to reuse cmd_start
    class FakeMessage:
        def __init__(self, chat, text, bot):
            self.chat = chat
            self.text = text
            self.bot = bot
        async def reply_text(self, *args, **kwargs):
            return await query.message.edit_text(*args, **kwargs)
    
    class FakeUpdate:
        def __init__(self, user, message):
            self.effective_user = user
            self.message = message
    
    fake_update = FakeUpdate(query.from_user, FakeMessage(query.message.chat, "/start", query.message.bot))
    await cmd_start(fake_update, context)

# ═══════════════════════════════════════════════════════════════════════
# WEBHOOK & SERVER
# ═══════════════════════════════════════════════════════════════════════

def process_update_sync(update_data):
    """Thread-safe update processing"""
    global bot_loop
    if not bot_loop or not bot_loop.is_running():
        return False
    
    try:
        future = asyncio.run_coroutine_threadsafe(
            process_update_async(update_data),
            bot_loop
        )
        return future.result(timeout=30)
    except Exception as e:
        logger.error(f"Process update error: {e}")
        return False

async def process_update_async(update_data):
    """Process update in bot's async context"""
    try:
        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)
        return True
    except Exception as e:
        logger.error(f"Update processing error: {e}")
        return False

@app.route("/")
def health():
    db = SessionLocal()
    try:
        stats = get_stats(db)
        return jsonify({
            "status": "ICEGODS v6.0 PRODUCTION",
            "database": "connected",
            "admins": stats['total_admins'],
            "active": stats['active_admins'],
            "revenue_sol": stats['total_revenue_sol'],
            "webhook": "active",
            "time": datetime.utcnow().isoformat()
        })
    finally:
        db.close()

@app.route(f"/webhook/{BOT_TOKEN.split(':')[1]}", methods=['POST'])
def webhook():
    if not application or bot_loop is None:
        return jsonify({"error": "Bot not ready"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        
        success = process_update_sync(data)
        return jsonify({"ok": success}), 200 if success else 500
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def bot_main():
    """Main bot coroutine"""
    global application, bot_loop
    
    bot_loop = asyncio.get_running_loop()
    
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", lambda u,c: u.message.reply_text("Use /start")))
    application.add_handler(CommandHandler("confirm", cmd_confirm))
    application.add_handler(CommandHandler("referral", cmd_referral))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    await application.initialize()
    
    # Set webhook
    if WEBHOOK_URL:
        webhook_path = f"/webhook/{BOT_TOKEN.split(':')[1]}"
        full_url = f"{WEBHOOK_URL}{webhook_path}"
        await application.bot.set_webhook(url=full_url)
        logger.info(f"✅ Webhook: {full_url}")
    
    await application.start()
    logger.info("✅ Bot started!")
    
    # Keep running
    while True:
        await asyncio.sleep(3600)

def run_bot():
    """Run bot in thread"""
    asyncio.run(bot_main())

def main():
    logger.info("=" * 60)
    logger.info("ICEGODS v6.0 - PRODUCTION SaaS PLATFORM")
    logger.info("=" * 60)
    
    # Start bot thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start airdrop scheduler thread
    def run_scheduler():
        asyncio.run(run_airdrop_scheduler())
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Wait for ready
    import time
    for i in range(30):
        if bot_loop is not None:
            break
        time.sleep(0.5)
    
    # Start Flask
    logger.info(f"Starting server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=False)

if __name__ == "__main__":
    main()

