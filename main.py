#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS BOT PLATFORM v6.1 - PRODUCTION READY
Fixed Database Schema + Token Detection + Airdrop System
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
import traceback
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify

# Import our modules
from database import init_db, SessionLocal, get_or_create_admin, check_subscription, add_referral_reward, get_stats, Admin, Payment, ClientBot
from token_detector import run_detection_loop

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
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
HELIUS_KEY = os.getenv("HELIUS_API_KEY")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@MexRobert")

SAAS_MONTHLY = float(os.getenv("SAAS_MONTHLY_PRICE", "5.0"))
SAAS_YEARLY = float(os.getenv("SAAS_YEARLY_PRICE", "50.0"))
REFERRAL_REWARD_DAYS = int(os.getenv("REFERRAL_REWARD_DAYS", "3"))

# Validation
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")
if not MASTER_WALLET:
    raise ValueError("MASTER_WALLET not set!")
if ADMIN_ID == 0:
    raise ValueError("ADMIN_ID not set!")

logger.info(f"Config loaded: Admin={ADMIN_ID}, Master Wallet={MASTER_WALLET[:15]}...")

# ═══════════════════════════════════════════════════════════════════════
# GLOBALS
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
application = None
bot_loop = None

# ═══════════════════════════════════════════════════════════════════════
# PAYMENT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

async def verify_payment_by_tx(tx_hash: str, expected_amount: float) -> tuple:
    """Verify Solana transaction via Helius"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_KEY}"
            payload = {"transactions": [tx_hash]}
            
            async with session.post(url, json=payload, timeout=30) as resp:
                if resp.status != 200:
                    logger.error(f"Helius API error: {resp.status}")
                    return False, 0.0
                
                data = await resp.json()
                if not data or not isinstance(data, list) or len(data) == 0:
                    return False, 0.0
                
                tx = data[0]
                transfers = tx.get('nativeTransfers', [])
                
                for transfer in transfers:
                    if transfer.get('toUserAccount') == MASTER_WALLET:
                        amount_sol = transfer.get('amount', 0) / 1_000_000_000
                        if abs(amount_sol - expected_amount) < 0.01:
                            return True, amount_sol
                
                return False, 0.0
                
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        return False, 0.0

# ═══════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main entry point"""
    user = update.effective_user
    logger.info(f"/start from {user.id} (@{user.username})")
    
    db = SessionLocal()
    try:
        # Check for referral code
        referral_code = None
        if context.args and len(context.args) > 0:
            referral_code = context.args[0]
            logger.info(f"Referral code detected: {referral_code}")
        
        # Get or create admin
        admin = get_or_create_admin(db, user.id, user.username, user.first_name)
        
        # Process referral
        if referral_code and admin.created_at > datetime.utcnow() - timedelta(minutes=1):
            referrer = db.query(Admin).filter(Admin.referral_code == referral_code).first()
            if referrer and referrer.telegram_id != user.id:
                success = add_referral_reward(db, referrer.telegram_id, REFERRAL_REWARD_DAYS)
                if success:
                    try:
                        await context.bot.send_message(
                            referrer.telegram_id,
                            f"🎉 New referral! @{user.username or user.id} joined!\n"
                            f"⏰ +{REFERRAL_REWARD_DAYS} days added!"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify referrer: {e}")
        
        # MASTER ADMIN PANEL
        if user.id == ADMIN_ID:
            stats = get_stats(db)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Stats", callback_data="master_stats")],
                [InlineKeyboardButton("💰 Revenue", callback_data="master_revenue")],
                [InlineKeyboardButton("👥 Admins", callback_data="master_admins")],
                [InlineKeyboardButton("🤖 Bots", callback_data="master_bots")]
            ])
            
            await update.message.reply_text(
                f"""👑 ICEGODS MASTER DASHBOARD

💎 Platform Stats:
• Total Admins: {stats['total_admins']}
• Active Subs: {stats['active_admins']}
• Bots Deployed: {stats['total_bots']}
• Revenue: {stats['total_revenue_sol']:.2f} SOL

💳 Wallet: `{MASTER_WALLET[:20]}...`

⚡ Status: ONLINE
🔍 Detection: ACTIVE""",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            return
        
        # REGULAR USER
        is_active, days_left = check_subscription(db, user.id)
        
        if is_active:
            bots_count = len(admin.client_bots)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Deploy Bot", callback_data="deploy_bot")],
                [InlineKeyboardButton("⚙️ My Bots", callback_data="my_bots")],
                [InlineKeyboardButton("🎁 Airdrops", callback_data="airdrops")],
                [InlineKeyboardButton("💎 Referrals", callback_data="referral")]
            ])
            
            await update.message.reply_text(
                f"""⚡ ADMIN PANEL

✅ Status: ACTIVE
⏰ Expires: {days_left} days
🤖 Bots: {bots_count}/{admin.max_clients}
💰 Earned: {admin.total_earned_sol:.2f} SOL

🔗 Code: `{admin.referral_code}`
👥 Referrals: {admin.referral_count}

🚀 Deploy your bot and start earning!""",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            # NO SUBSCRIPTION
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💎 Monthly ({SAAS_MONTHLY} SOL)", callback_data="sub_monthly")],
                [InlineKeyboardButton(f"👑 Yearly ({SAAS_YEARLY} SOL)", callback_data="sub_yearly")],
                [InlineKeyboardButton("🎁 Have Code?", callback_data="enter_referral")]
            ])
            
            await update.message.reply_text(
                f"""🚀 ICEGODS Bot Platform

Deploy white-label token alert bots!

💎 WHAT YOU GET:
✅ Auto-detect new token launches
✅ VIP/Whale/Premium tiers
✅ Automatic airdrop distribution
✅ You keep 80% of revenue

📊 PRICING:
• Monthly: {SAAS_MONTHLY} SOL
• Yearly: {SAAS_YEARLY} SOL

🔥 BONUS: Refer 3 = +3 days + 1 bot slot!

Tap below 👇""",
                reply_markup=keyboard
            )
    
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("❌ Error loading dashboard. Please try /start again.")
    finally:
        db.close()

async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify payment"""
    user = update.effective_user
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: /confirm TRANSACTION_HASH")
        return
    
    tx_hash = context.args[0].strip()
    
    if len(tx_hash) < 80:
        await update.message.reply_text("❌ Invalid transaction hash")
        return
    
    await update.message.reply_text("🛰 Verifying on Solana...")
    
    db = SessionLocal()
    try:
        # Check if tx already used
        existing = db.query(Payment).filter(Payment.tx_hash == tx_hash).first()
        if existing:
            await update.message.reply_text("❌ Transaction already used!")
            db.close()
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
                    f"""✅ ACTIVATED!

🎉 Plan: {plan_type.upper()}
⏰ Duration: {days} days
📅 Expires: {admin.expires_at.strftime('%Y-%m-%d')}
💰 Paid: {actual_amount:.4f} SOL

🚀 Click /start!"""
                )
                
                # Notify master
                try:
                    await context.bot.send_message(
                        ADMIN_ID,
                        f"💰 NEW: {user.id} | {plan_type} | {actual_amount:.4f} SOL"
                    )
                except:
                    pass
                return
        
        await update.message.reply_text(
            f"""❌ NOT FOUND

Check:
• Sent exactly {SAAS_MONTHLY} or {SAAS_YEARLY} SOL?
• Transaction confirmed?
• Correct wallet: {MASTER_WALLET[:15]}...

Support: {SUPPORT_USERNAME}"""
        )
    
    except Exception as e:
        logger.error(f"Error in confirm: {e}")
        await update.message.reply_text("❌ Verification error. Try again.")
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════════════════
# BUTTON HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buttons"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"Button: {data} by {user_id}")
    
    try:
        if data == "sub_monthly":
            await show_invoice(query, "monthly", SAAS_MONTHLY, 30)
        elif data == "sub_yearly":
            await show_invoice(query, "yearly", SAAS_YEARLY, 365)
        elif data == "master_stats":
            await show_stats(query)
        elif data == "referral":
            await show_referral(query, user_id)
        elif data == "main_menu":
            await back_to_start(query, context)
        else:
            await query.message.edit_text("🚧 Feature coming soon!\n\nClick /start to refresh.")
    
    except Exception as e:
        logger.error(f"Button error: {e}")
        await query.message.reply_text("❌ Error. Click /start")

async def show_invoice(query, plan_type, amount, days):
    """Show payment invoice"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        f"""🧾 INVOICE

Plan: {plan_type.upper()}
Duration: {days} days
Amount: {amount} SOL

═══════════════════
SEND TO:
`{MASTER_WALLET}`
═══════════════════

⚠️ Send EXACTLY {amount} SOL

After sending:
/confirm YOUR_TX_HASH

Support: {SUPPORT_USERNAME}""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def show_stats(query):
    """Show platform stats"""
    db = SessionLocal()
    try:
        stats = get_stats(db)
        await query.message.edit_text(
            f"""📊 PLATFORM STATS

👥 Admins: {stats['total_admins']} (Active: {stats['active_admins']})
🤖 Bots: {stats['total_bots']}
💰 Revenue: {stats['total_revenue_sol']:.2f} SOL

⚡ System: ONLINE"""
        )
    finally:
        db.close()

async def show_referral(query, user_id):
    """Show referral info"""
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == user_id).first()
        bot_username = query.message.bot.username
        link = f"https://t.me/{bot_username}?start={admin.referral_code}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={link}&text=Join ICEGODS!")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
        
        await query.message.edit_text(
            f"""🎁 REFERRAL PROGRAM

🔗 Your Link:
`{link}`

📊 Stats:
• Referrals: {admin.referral_count}
• Earned: {admin.referral_count * 3} days

🎯 Next: Refer {3 - (admin.referral_count % 3)} more = +3 days!""",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    finally:
        db.close()

async def back_to_start(query, context):
    """Return to main menu"""
    # Trigger /start command
    await cmd_start(Update(update_id=0, message=query.message, callback_query=query), context)

# ═══════════════════════════════════════════════════════════════════════
# WEB SERVER
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
        logger.error(f"Process error: {e}")
        return False

async def process_update_async(update_data):
    """Process update"""
    try:
        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)
        return True
    except Exception as e:
        logger.error(f"Update error: {e}")
        return False

@app.route("/")
def health():
    """Health check with DB verification"""
    try:
        db = SessionLocal()
        stats = get_stats(db)
        db.close()
        
        return jsonify({
            "status": "ICEGODS v6.1 ONLINE",
            "database": "connected",
            "stats": stats,
            "time": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "ERROR",
            "error": str(e),
            "time": datetime.utcnow().isoformat()
        }), 500

@app.route(f"/webhook/{BOT_TOKEN.split(':')[1]}", methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
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
    """Main bot loop"""
    global application, bot_loop
    
    bot_loop = asyncio.get_running_loop()
    logger.info("Bot loop started")
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
        raise
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("confirm", cmd_confirm))
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
    
    # Keep alive
    while True:
        await asyncio.sleep(3600)

def run_bot():
    """Run bot in thread"""
    asyncio.run(bot_main())

def main():
    logger.info("=" * 60)
    logger.info("ICEGODS v6.1 STARTING")
    logger.info("=" * 60)
    
    # Start bot thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start detection loop in separate thread
    def run_detector():
        asyncio.run(run_detection_loop())
    
    detector_thread = threading.Thread(target=run_detector, daemon=True)
    detector_thread.start()
    
    # Wait for bot to be ready
    import time
    for i in range(60):
        if bot_loop is not None:
            logger.info("✅ Bot ready, starting server")
            break
        time.sleep(1)
    
    # Start Flask
    logger.info(f"Starting Flask on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=False)

if __name__ == "__main__":
    main()

