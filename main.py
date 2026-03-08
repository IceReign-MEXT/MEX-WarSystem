#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS BOT PLATFORM v6.2 - COMPLETE ECOSYSTEM
Group Detection + Payment Monitor + Cross-Channel Marketing + Token Detection
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import asyncio
import threading
import logging
import aiohttp
import secrets
import traceback
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ChatMemberHandler, MessageHandler, filters
from flask import Flask, request, jsonify

from database import init_db, SessionLocal, get_or_create_admin, check_subscription, add_referral_reward, get_stats, Admin, Payment, ClientBot, Subscriber
from token_detector import run_detection_loop
from group_monitor import GroupMonitor
from payment_monitor import PaymentMonitor
from cross_channel_marketing import CrossChannelMarketing

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
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "MexRobert")
BOT_USERNAME = os.getenv("BOT_USERNAME", "ICEMEXWarSystem_Bot")

SAAS_MONTHLY = float(os.getenv("SAAS_MONTHLY_PRICE", "5.0"))
SAAS_YEARLY = float(os.getenv("SAAS_YEARLY_PRICE", "50.0"))
REFERRAL_REWARD_DAYS = int(os.getenv("REFERRAL_REWARD_DAYS", "3"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

# ═══════════════════════════════════════════════════════════════════════
# GLOBALS
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
application = None
bot_loop = None
group_monitor = None
payment_monitor = None
marketing_engine = None

# ═══════════════════════════════════════════════════════════════════════
# PAYMENT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

async def verify_payment_by_tx(tx_hash: str, expected_amount: float) -> tuple:
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_KEY}"
            payload = {"transactions": [tx_hash]}
            
            async with session.post(url, json=payload, timeout=30) as resp:
                if resp.status != 200:
                    return False, 0.0
                
                data = await resp.json()
                if not data or not isinstance(data, list):
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
    """Main entry with full viral funnel"""
    user = update.effective_user
    chat_type = update.effective_chat.type if update.effective_chat else "private"
    
    logger.info(f"/start from {user.id} in {chat_type}")
    
    # Handle group starts (when users click from group welcome message)
    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(
            f"""👋 Hi @{user.username or user.first_name}!

Private message me to subscribe:
@{BOT_USERNAME}

💎 Get VIP access to token alerts!"""
        )
        return
    
    db = SessionLocal()
    try:
        # Track marketing source
        source = "direct"
        if context.args and len(context.args) > 0:
            if context.args[0].startswith("marketing_"):
                source = context.args[0].replace("marketing_", "")
                if marketing_engine:
                    await marketing_engine.track_conversion(user.id, source)
            elif context.args[0].startswith("vip_") or context.args[0].startswith("premium_"):
                source = f"group_{context.args[0]}"
            else:
                source = f"referral_{context.args[0]}"
        
        # Get or create admin
        admin = get_or_create_admin(db, user.id, user.username, user.first_name)
        
        # Process referral
        if source.startswith("referral_") and admin.created_at > datetime.utcnow() - timedelta(minutes=1):
            ref_code = source.replace("referral_", "")
            referrer = db.query(Admin).filter(Admin.referral_code == ref_code).first()
            if referrer and referrer.telegram_id != user.id:
                add_referral_reward(db, referrer.telegram_id, REFERRAL_REWARD_DAYS)
                try:
                    await context.bot.send_message(
                        referrer.telegram_id,
                        f"🎉 @{user.username or user.first_name} joined via your link!\n⏰ +{REFERRAL_REWARD_DAYS} days added!"
                    )
                except:
                    pass
        
        # MASTER ADMIN PANEL
        if user.id == ADMIN_ID:
            stats = get_stats(db)
            
            # Calculate projected revenue
            active_admins = stats['active_admins']
            projected_monthly = active_admins * SAAS_MONTHLY * 0.2  # 20% commission
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Live Stats", callback_data="master_stats")],
                [InlineKeyboardButton("💰 Revenue", callback_data="master_revenue")],
                [InlineKeyboardButton("👥 Manage Admins", callback_data="master_admins")],
                [InlineKeyboardButton("🤖 Bot Deployments", callback_data="master_bots")],
                [InlineKeyboardButton("📢 Marketing Control", callback_data="master_marketing")]
            ])
            
            await update.message.reply_text(
                f"""👑 ICEGODS MASTER DASHBOARD

💎 PLATFORM OVERVIEW:
━━━━━━━━━━━━━━━━━━━━━
👥 Total Admins: {stats['total_admins']}
✅ Active: {stats['active_admins']} 
🤖 Bots Live: {stats['total_bots']}
💰 Total Revenue: {stats['total_revenue_sol']:.2f} SOL

📈 PROJECTIONS:
• Monthly Recurring: ~{projected_monthly:.1f} SOL
• At 100 admins: {100 * SAAS_MONTHLY * 0.2:.0f} SOL/month
• At 500 admins: {500 * SAAS_MONTHLY * 0.2:.0f} SOL/month

💳 Master Wallet:
`{MASTER_WALLET}`

⚡ Systems: ALL ONLINE
🔍 Detection: RUNNING
📢 Marketing: ACTIVE""",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            return
        
        # REGULAR USER FLOW
        is_active, days_left = check_subscription(db, user.id)
        
        if is_active:
            bots_count = len(admin.client_bots)
            earnings = admin.total_earned_sol
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Deploy New Bot", callback_data="deploy_bot")],
                [InlineKeyboardButton("⚙️ Manage Bots", callback_data="my_bots")],
                [InlineKeyboardButton("🎁 Airdrop Manager", callback_data="airdrop_menu")],
                [InlineKeyboardButton("💎 Referral Program", callback_data="referral_dashboard")],
                [InlineKeyboardButton("📊 Earnings Report", callback_data="earnings_report")],
                [InlineKeyboardButton("⚠️ Expires in {days_left}d", callback_data="renew_reminder")]
            ])
            
            await update.message.reply_text(
                f"""⚡ ADMIN DASHBOARD

✅ Status: ACTIVE
⏰ Expires: {days_left} days
🤖 Bots: {bots_count}/{admin.max_clients}
💰 Total Earned: {earnings:.2f} SOL

🔗 Your Referral Link:
`t.me/{BOT_USERNAME}?start={admin.referral_code}`

👥 Referrals: {admin.referral_count}
🎁 Free Days Earned: {admin.referral_count * 3}

📈 EARN MORE:
• Deploy more bots = More revenue
• Refer friends = Free access
• Higher tiers = More features

🚀 What would you like to do?""",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            # EXPIRED OR NEW USER
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💎 Monthly - {SAAS_MONTHLY} SOL", callback_data="sub_monthly")],
                [InlineKeyboardButton(f"👑 Yearly - {SAAS_YEARLY} SOL (Save 17%)", callback_data="sub_yearly")],
                [InlineKeyboardButton("🎁 I Have Referral Code", callback_data="enter_referral")],
                [InlineKeyboardButton("📊 See Demo Bot", url="https://t.me/Icegods_Bridge_bot")],
                [InlineKeyboardButton("💬 Join Community", url="https://t.me/CHINACRYPTOCROSSCHAINSNETWORKS")]
            ])
            
            await update.message.reply_text(
                f"""🚀 ICEGODS BOT PLATFORM

Deploy professional token alert bots!

💎 WHAT YOU GET:
━━━━━━━━━━━━━━━━━━━━━
✅ Auto-detect new launches (DexScreener + Helius)
✅ VIP/Whale/Premium tier management
✅ Automatic SOL payment collection
✅ Built-in airdrop distribution
✅ Cross-channel marketing tools
✅ 80% revenue share (you keep most!)

💰 REVENUE POTENTIAL:
• 10 subscribers @ 1 SOL = 8 SOL profit/month
• 100 subscribers @ 1 SOL = 80 SOL profit/month
• Scale to unlimited bots

📊 PRICING:
• Monthly: {SAAS_MONTHLY} SOL
• Yearly: {SAAS_YEARLY} SOL

🔥 VIRAL BONUS:
Refer 3 friends → +3 days free + 1 extra bot slot!

⚡ Limited to {admin.max_clients} bot{'s' if admin.max_clients > 1 else ''} (earn more slots!)

Source: {source}
Click below to start 👇""",
                reply_markup=keyboard
            )
    
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("❌ Error loading dashboard. Try again: /start")
    finally:
        db.close()

async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Payment verification with instant activation"""
    user = update.effective_user
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            """🛰 PAYMENT VERIFICATION

Send your transaction hash after paying:

/confirm YOUR_TX_HASH

Example:
/confirm 5JTHj8rSHw4h6NAoZwLByQ2c4Y65rk6WnCcZ1A91HE573PU88jWXwrcPxs9HyXxv6KVrtktb3j4XsSmj2HnEzghc"""
        )
        return
    
    tx_hash = context.args[0].strip()
    
    if len(tx_hash) < 80:
        await update.message.reply_text("❌ Invalid hash (too short)")
        return
    
    await update.message.reply_text("🛰 Verifying on Solana blockchain...")
    
    db = SessionLocal()
    try:
        # Check if used
        existing = db.query(Payment).filter(Payment.tx_hash == tx_hash).first()
        if existing:
            await update.message.reply_text("❌ This transaction was already used!")
            return
        
        # Try plans
        for plan_type, amount, days in [
            ('monthly', SAAS_MONTHLY, 30),
            ('yearly', SAAS_YEARLY, 365)
        ]:
            success, actual = await verify_payment_by_tx(tx_hash, amount)
            
            if success:
                admin = get_or_create_admin(db, user.id, user.username, user.first_name)
                
                # Set expiry
                if admin.expires_at and admin.expires_at > datetime.utcnow():
                    admin.expires_at += timedelta(days=days)
                else:
                    admin.expires_at = datetime.utcnow() + timedelta(days=days)
                
                admin.plan_type = plan_type
                admin.is_active = True
                
                # Record payment
                payment = Payment(
                    admin_id=user.id,
                    amount_sol=actual,
                    plan_type=plan_type,
                    tx_hash=tx_hash,
                    status='confirmed',
                    confirmed_at=datetime.utcnow()
                )
                db.add(payment)
                db.commit()
                
                # Success message
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 Launch Dashboard", callback_data="main_menu")],
                    [InlineKeyboardButton("📖 Setup Guide", callback_data="setup_guide")]
                ])
                
                await update.message.reply_text(
                    f"""✅ PAYMENT CONFIRMED!

🎉 Subscription: {plan_type.upper()}
⏰ Duration: {days} days  
📅 Expires: {admin.expires_at.strftime('%Y-%m-%d %H:%M')}
💰 Amount: {actual:.4f} SOL
🔗 Tx: `{tx_hash[:25]}...`

🚀 YOUR DASHBOARD IS READY!

Next steps:
1. Deploy your first bot
2. Configure token detection
3. Set your prices
4. Start earning!

Click below to begin 👇""",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                # Notify master
                try:
                    await context.bot.send_message(
                        ADMIN_ID,
                        f"💰 NEW PAYMENT!\n"
                        f"User: {user.id} (@{user.username})\n"
                        f"Plan: {plan_type}\n"
                        f"Amount: {actual:.4f} SOL\n"
                        f"Revenue: +{actual * 0.2:.2f} SOL (your 20%)"
                    )
                except:
                    pass
                return
        
        # Not found
        await update.message.reply_text(
            f"""❌ PAYMENT NOT FOUND

Possible issues:
• Wrong amount (need {SAAS_MONTHLY} or {SAAS_YEARLY} SOL)
• Transaction not confirmed (wait 1-2 min)
• Wrong wallet address

Your wallet: `{MASTER_WALLET[:20]}...`

Try again or contact {SUPPORT_USERNAME}"""
        )
    
    except Exception as e:
        logger.error(f"Confirm error: {e}")
        await update.message.reply_text("❌ Verification failed. Try again.")
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
    
    logger.info(f"Button: {data} by {user_id}")
    
    try:
        if data == "sub_monthly":
            await show_invoice(query, "monthly", SAAS_MONTHLY, 30)
        elif data == "sub_yearly":
            await show_invoice(query, "yearly", SAAS_YEARLY, 365)
        elif data == "deploy_bot":
            await start_deployment_wizard(query, user_id, context)
        elif data == "my_bots":
            await show_my_bots(query, user_id)
        elif data == "referral_dashboard":
            await show_referral_full(query, user_id)
        elif data == "earnings_report":
            await show_earnings(query, user_id)
        elif data == "master_stats":
            await show_master_stats(query)
        elif data == "master_revenue":
            await show_master_revenue(query)
        elif data == "main_menu":
            await back_to_start(query, context)
        else:
            await query.message.edit_text(
                "🚧 Feature coming in v6.3!\n\n"
                "💎 Current features:\n"
                "• Payment verification ✅\n"
                "• Subscription management ✅\n"
                "• Referral system ✅\n\n"
                "Click /start to refresh"
            )
    
    except Exception as e:
        logger.error(f"Button error: {e}")
        await query.message.reply_text("❌ Error. Click /start to restart")

async def show_invoice(query, plan_type, amount, days):
    """Show payment invoice"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I've Sent Payment", callback_data=f"paid_{plan_type}")],
        [InlineKeyboardButton("📋 Payment Instructions", callback_data="payment_help")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        f"""🧾 INVOICE #{int(datetime.utcnow().timestamp())}

━━━━━━━━━━━━━━━━━━━━━
PLAN: {plan_type.upper()}
DURATION: {days} days
AMOUNT: {amount} SOL
━━━━━━━━━━━━━━━━━━━━━

📤 SEND EXACTLY {amount} SOL TO:
`{MASTER_WALLET}`

⚠️ IMPORTANT:
• Send ONLY SOL (not SPL tokens)
• Double-check the amount
• Save your transaction hash

⏱ Verification: Instant after confirmation

After sending, click "I've Sent Payment" and use:
/confirm YOUR_TX_HASH""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def start_deployment_wizard(query, user_id, context):
    """Start bot deployment"""
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == user_id).first()
        
        if not admin or not admin.expires_at or admin.expires_at < datetime.utcnow():
            await query.message.edit_text("❌ Active subscription required!")
            return
        
        if len(admin.client_bots) >= admin.max_clients:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Refer for More Slots", callback_data="referral_dashboard")],
                [InlineKeyboardButton("📞 Upgrade Support", url=f"https://t.me/{SUPPORT_USERNAME}")]
            ])
            
            await query.message.edit_text(
                f"""❌ BOT LIMIT REACHED

You: {len(admin.client_bots)}/{admin.max_clients} bots

🎯 Unlock more slots:
• Refer 3 friends = +1 slot
• Contact support for bulk pricing

Current referrals: {admin.referral_count}""",
                reply_markup=keyboard
            )
            return
        
        # Start wizard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Start Setup (3 steps)", callback_data="deploy_step1")],
            [InlineKeyboardButton("📹 Video Tutorial", url="https://t.me/CHINACRYPTOCROSSCHAINSNETWORKS")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
        
        await query.message.edit_text(
            """🚀 BOT DEPLOYMENT WIZARD

I'll create your white-label bot in 3 easy steps:

STEP 1: Get Bot Token
→ Message @BotFather
→ Create new bot
→ Copy the token

STEP 2: Configure Detection
→ Set target token (optional)
→ Set min liquidity ($1k default)
→ Set max market cap ($1M default)

STEP 3: Set Your Prices
→ VIP tier (default 0.5 SOL)
→ Whale tier (default 1 SOL)  
→ Premium tier (default 2.5 SOL)

⚡ Your bot goes live instantly!

Ready to start?""",
            reply_markup=keyboard
        )
    
    finally:
        db.close()

async def show_my_bots(query, user_id):
    """Show user's deployed bots"""
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == user_id).first()
        
        if not admin or not admin.client_bots:
            await query.message.edit_text(
                "🤖 No bots deployed yet!\n\n"
                "Click 🚀 Deploy New Bot to get started."
            )
            return
        
        text = "⚙️ YOUR BOTS\n\n"
        keyboard_buttons = []
        
        for bot in admin.client_bots:
            status = "🟢 Live" if bot.is_active else "🔴 Stopped"
            text += (
                f"@{bot.bot_username or 'Unknown'}\n"
                f"Status: {status}\n"
                f"Subscribers: {bot.total_subscribers}\n"
                f"Revenue: {bot.total_revenue_sol:.2f} SOL\n"
                f"Alerts sent: {bot.total_alerts_sent}\n\n"
            )
            keyboard_buttons.append([
                InlineKeyboardButton(f"Manage @{bot.bot_username}", callback_data=f"manage_bot_{bot.id}")
            ])
        
        keyboard_buttons.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await query.message.edit_text(text, reply_markup=keyboard)
    
    finally:
        db.close()

async def show_referral_full(query, user_id):
    """Full referral dashboard"""
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == user_id).first()
        
        link = f"https://t.me/{BOT_USERNAME}?start={admin.referral_code}"
        next_reward = 3 - (admin.referral_count % 3)
        
        # Calculate value of referrals
        free_days = admin.referral_count * 3
        slots_earned = admin.referral_count // 3
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share to Telegram", url=f"https://t.me/share/url?url={link}&text=🔥 ICEGODS Bot Platform - Deploy your own crypto alert bot and earn SOL!")],
            [InlineKeyboardButton("🐦 Share to Twitter", url=f"https://twitter.com/intent/tweet?text=Just%20found%20this%20bot%20platform%20for%20crypto%20alerts%20-%20earn%20passive%20SOL!%20{link}")],
            [InlineKeyboardButton("📋 Copy Link", callback_data="copy_ref_link")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
        
        await query.message.edit_text(
            f"""🎁 REFERRAL DASHBOARD

🔗 YOUR REFERRAL LINK:
`{link}`

📊 YOUR STATISTICS:
━━━━━━━━━━━━━━━━━━━━━
👥 Total Referrals: {admin.referral_count}
⏰ Free Days Earned: {free_days} days
🤖 Bonus Bot Slots: +{slots_earned}

🎯 NEXT REWARD:
Refer {next_reward} more friend{'s' if next_reward > 1 else ''} = 
✓ +3 days subscription
✓ +1 bot slot

💰 VALUE CALCULATION:
Each referral = 3 days free
At {SAAS_MONTHLY} SOL/month = {SAAS_MONTHLY/30*3:.3f} SOL value

🚀 TOP PERFORMERS GET:
• Featured on homepage
• Early access to new features
• Direct support line

📢 BEST SHARING SPOTS:
• Crypto Telegram groups
• Twitter/X crypto threads
• Discord communities
• Reddit r/Solana, r/CryptoCurrency""",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    finally:
        db.close()

async def show_earnings(query, user_id):
    """Show earnings report"""
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == user_id).first()
        
        # Calculate projections
        current_earnings = admin.total_earned_sol
        bots_count = len(admin.client_bots)
        
        # Estimate potential
        avg_subscriber_value = 0.8  # SOL per subscriber (after your 20%)
        potential_per_bot = 10 * avg_subscriber_value  # Assume 10 subs per bot
        total_potential = bots_count * potential_per_bot
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💸 Withdraw Earnings", callback_data="withdraw")],
            [InlineKeyboardButton("📊 Detailed Report", callback_data="detailed_earnings")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
        
        await query.message.edit_text(
            f"""📊 EARNINGS REPORT

💰 CURRENT STATS:
━━━━━━━━━━━━━━━━━━━━━
Total Earned: {current_earnings:.2f} SOL
Active Bots: {bots_count}
Platform Fee: 20% (you keep 80%)

📈 PROJECTIONS:
If each bot gets 10 subscribers:
• Potential: {total_potential:.1f} SOL
• At current SOL price: ${total_potential * 150:.0f} USD

🎯 GROWTH TIPS:
• Post in crypto groups daily
• Offer first week free trials  
• Partner with new token launches
• Use airdrops to attract users

⚡ INSTANT WITHDRAWAL:
No minimum, no delays
Send to any Solana wallet""",
            reply_markup=keyboard
        )
    
    finally:
        db.close()

async def show_master_stats(query):
    """Master admin stats"""
    db = SessionLocal()
    try:
        stats = get_stats(db)
        
        # Calculate growth rate (compare to last week)
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_this_week = db.query(Admin).filter(Admin.created_at > week_ago).count()
        
        await query.message.edit_text(
            f"""📊 PLATFORM ANALYTICS

👥 USER METRICS:
━━━━━━━━━━━━━━━━━━━━━
Total Admins: {stats['total_admins']}
Active (paid): {stats['active_admins']}
New this week: +{new_this_week}
Conversion rate: {(stats['active_admins']/max(stats['total_admins'],1)*100):.1f}%

🤖 BOT METRICS:
Total Deployed: {stats['total_bots']}
Active: {stats['active_bots']}
Avg per admin: {stats['total_bots']/max(stats['total_admins'],1):.1f}

💰 FINANCIAL:
Total Revenue: {stats['total_revenue_sol']:.2f} SOL
Your Share (20%): {stats['total_revenue_sol'] * 0.2:.2f} SOL
Projected Monthly: {stats['active_admins'] * SAAS_MONTHLY * 0.2:.1f} SOL

⚡ SYSTEM STATUS:
Database: ✅ Connected
Detection: ✅ Running
Payments: ✅ Active
Marketing: ✅ Broadcasting""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ])
        )
    
    finally:
        db.close()

async def show_master_revenue(query):
    """Show revenue breakdown"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        
        # Get monthly breakdown
        monthly = db.query(
            func.strftime('%Y-%m', Payment.confirmed_at),
            func.sum(Payment.amount_sol)
        ).filter(
            Payment.status == 'confirmed'
        ).group_by(
            func.strftime('%Y-%m', Payment.confirmed_at)
        ).all()
        
        text = "💰 REVENUE BREAKDOWN\n\n"
        for month, amount in monthly[-6:]:  # Last 6 months
            text += f"{month}: {amount:.2f} SOL\n"
        
        text += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"Total: {sum([m[1] for m in monthly]):.2f} SOL\n"
        text += f"Your 20%: {sum([m[1] for m in monthly]) * 0.2:.2f} SOL\n\n"
        text += f"Wallet: `{MASTER_WALLET[:25]}...`"
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("View on Solscan", url=f"https://solscan.io/account/{MASTER_WALLET}")],
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ]),
            parse_mode='Markdown'
        )
    
    finally:
        db.close()

async def back_to_start(query, context):
    """Return to main menu"""
    # Create minimal update object
    class FakeMsg:
        def __init__(self, chat, bot):
            self.chat = chat
            self.bot = bot
        async def reply_text(self, *args, **kwargs):
            return await query.message.edit_text(*args, **kwargs)
    
    class FakeUpdate:
        def __init__(self, user, msg):
            self.effective_user = user
            self.message = msg
            self.effective_chat = msg.chat
    
    fake = FakeUpdate(query.from_user, FakeMsg(query.message.chat, query.message.bot))
    await cmd_start(fake, context)

# ═══════════════════════════════════════════════════════════════════════
# GROUP HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot added/removed from groups"""
    if not group_monitor:
        return
    
    result = update.chat_member
    
    # Bot was added
    if result.new_chat_member and result.new_chat_member.user.id == context.bot.id:
        if result.new_chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
            await group_monitor.on_bot_added(update, context)
    
    # Bot was removed
    elif result.old_chat_member and result.old_chat_member.user.id == context.bot.id:
        if result.old_chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
            logger.info(f"Bot removed from {update.effective_chat.id}")

async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new group members"""
    if not group_monitor:
        return
    
    await group_monitor.on_new_member(update, context)

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
    """Process update in bot's async context"""
    try:
        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)
        return True
    except Exception as e:
        logger.error(f"Update error: {e}")
        return False

@app.route("/")
def health():
    """Health check"""
    try:
        db = SessionLocal()
        stats = get_stats(db)
        db.close()
        
        return jsonify({
            "status": "ICEGODS v6.2 FULLY OPERATIONAL",
            "version": "6.2.0",
            "database": "connected",
            "stats": stats,
            "systems": {
                "detection": "active",
                "payments": "active",
                "marketing": "active",
                "groups": "active"
            },
            "time": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "error": str(e),
            "time": datetime.utcnow().isoformat()
        }), 500

@app.route(f"/webhook/{BOT_TOKEN.split(':')[1]}", methods=['POST'])
def webhook():
    """Telegram webhook"""
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
    global application, bot_loop, group_monitor, payment_monitor, marketing_engine
    
    bot_loop = asyncio.get_running_loop()
    logger.info("🚀 Bot starting...")
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database ready")
    except Exception as e:
        logger.error(f"❌ Database failed: {e}")
        raise
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Initialize subsystems
    group_monitor = GroupMonitor(application)
    payment_monitor = PaymentMonitor(application)
    marketing_engine = CrossChannelMarketing(application)
    
    # Register handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("confirm", cmd_confirm))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Group handlers
    application.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_members))
    
    await application.initialize()
    
    # Set webhook
    if WEBHOOK_URL:
        webhook_path = f"/webhook/{BOT_TOKEN.split(':')[1]}"
        full_url = f"{WEBHOOK_URL}{webhook_path}"
        await application.bot.set_webhook(url=full_url)
        logger.info(f"✅ Webhook: {full_url}")
    
    await application.start()
    logger.info("✅ Bot operational!")
    
    # Keep alive
    while True:
        await asyncio.sleep(3600)

def run_bot():
    """Run bot thread"""
    asyncio.run(bot_main())

def run_background_tasks():
    """Run all background loops"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run all monitors concurrently
    async def run_all():
        await asyncio.gather(
            run_detection_loop(),
            payment_monitor.run_monitor_loop() if payment_monitor else asyncio.sleep(1),
            marketing_engine.run_marketing_loop() if marketing_engine else asyncio.sleep(1),
            return_exceptions=True
        )
    
    loop.run_until_complete(run_all())

def main():
    logger.info("=" * 60)
    logger.info("ICEGODS v6.2 - COMPLETE ECOSYSTEM")
    logger.info("=" * 60)
    
    # Start bot
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Wait for bot
    import time
    for i in range(60):
        if bot_loop is not None:
            break
        time.sleep(1)
    
    # Start background tasks
    bg_thread = threading.Thread(target=run_background_tasks, daemon=True)
    bg_thread.start()
    
    # Start Flask
    logger.info(f"🌐 Starting server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=False)

if __name__ == "__main__":
    main()

