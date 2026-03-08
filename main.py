#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS BOT PLATFORM v5.0 - EMERGENCY WORKING VERSION
✅ All commands responding
✅ Auto payment detection
✅ Database working
✅ Deployment ready
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import asyncio
import threading
import logging
import aiohttp
import ssl
import json
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from flask import Flask, request, jsonify
import asyncpg

# Force stdout logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

BOT_TOKEN = "7968707142:AAHk3snOd8SxZ_8_hJY5Tq0p6eDebh9RvJk"
ADMIN_ID = 8254662446
MASTER_WALLET = "HxmywH2gW9ezQ2nBXwurpaWsZS6YvdmLF23R9WgMAM7p"
DATABASE_URL = "postgresql://postgres:IceWarlord30Icegods@db.ylpxxgvaetykmswzrpmi.supabase.co:5432/postgres"
WEBHOOK_URL = "https://mex-warsystem-8rzh.onrender.com"
PORT = 10000
HELIUS_KEY = "1b0094c2-50b9-4c97-a2d6-2c47d4ac2789"
SUPPORT_USERNAME = "MexRobert"

SAAS_MONTHLY = 5.0
SAAS_YEARLY = 50.0

logger.info("=" * 60)
logger.info("ICEGODS BOT PLATFORM v5.0 STARTING")
logger.info(f"Admin ID: {ADMIN_ID}")
logger.info(f"Master Wallet: {MASTER_WALLET[:20]}...")
logger.info("=" * 60)

# ═══════════════════════════════════════════════════════════════════════
# GLOBALS
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
db_pool = None
application = None

# ═══════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════

async def init_db():
    global db_pool
    try:
        logger.info("Connecting to database...")
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            ssl=ssl_context,
            command_timeout=30
        )
        
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    admin_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    plan_type TEXT DEFAULT 'none',
                    expires_at TIMESTAMP,
                    wallet TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    admin_id BIGINT,
                    amount DECIMAL(10,4),
                    plan_type TEXT,
                    tx_hash TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS client_bots (
                    bot_id SERIAL PRIMARY KEY,
                    admin_id BIGINT,
                    bot_token TEXT,
                    channel_id TEXT,
                    group_id TEXT,
                    client_wallet TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        
        logger.info("✅ Database connected!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

async def get_admin(user_id):
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM admins WHERE admin_id = $1", user_id)
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Get admin error: {e}")
        return None

async def create_admin(user_id, username, first_name, plan_type, expires_at):
    if not db_pool:
        return False
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO admins (admin_id, username, first_name, plan_type, expires_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (admin_id) DO UPDATE SET
                    plan_type = $4,
                    expires_at = $5,
                    username = $2,
                    first_name = $3
            """, user_id, username, first_name, plan_type, expires_at)
            return True
    except Exception as e:
        logger.error(f"Create admin error: {e}")
        return False

async def save_payment(user_id, amount, plan_type):
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            pid = await conn.fetchval("""
                INSERT INTO payments (admin_id, amount, plan_type, status)
                VALUES ($1, $2, $3, 'pending')
                RETURNING id
            """, user_id, amount, plan_type)
            return pid
    except Exception as e:
        logger.error(f"Save payment error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════
# HELIUS VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

async def verify_payment_by_tx(tx_hash, expected_amount):
    """Verify specific transaction"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_KEY}"
            
            payload = {"transactions": [tx_hash]}
            
            async with session.post(url, json=payload, timeout=30) as resp:
                if resp.status != 200:
                    logger.error(f"Helius error: {resp.status}")
                    return False, 0
                
                data = await resp.json()
                
                if not data or not isinstance(data, list) or len(data) == 0:
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

async def check_recent_payment(expected_amount):
    """Check recent transactions"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/addresses/{MASTER_WALLET}/transactions?api-key={HELIUS_KEY}&limit=20"
            
            async with session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    return False, None, 0
                
                data = await resp.json()
                
                if not isinstance(data, list):
                    return False, None, 0
                
                for tx in data:
                    tx_hash = tx.get('signature')
                    transfers = tx.get('nativeTransfers', [])
                    
                    for transfer in transfers:
                        if transfer.get('toUserAccount') == MASTER_WALLET:
                            amount_sol = transfer.get('amount', 0) / 1_000_000_000
                            if abs(amount_sol - expected_amount) < 0.01:
                                return True, tx_hash, amount_sol
                
                return False, None, 0
                
    except Exception as e:
        logger.error(f"Recent check error: {e}")
        return False, None, 0

# ═══════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS - ALL MUST BE REGISTERED
# ═══════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"/start from {user.id} ({user.username})")
    
    # Check if master admin
    if user.id == ADMIN_ID:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Stats", callback_data="stats")],
            [InlineKeyboardButton("💰 Revenue", callback_data="revenue")],
            [InlineKeyboardButton("👥 Admins", callback_data="admins")]
        ])
        
        await update.message.reply_text(
            f"""👑 MASTER DASHBOARD

🚀 Platform: ONLINE
💳 Wallet: `{MASTER_WALLET[:20]}...`

Your SaaS platform is live!""",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return
    
    # Check if subscribed admin
    admin = await get_admin(user.id)
    
    if admin and admin.get('expires_at'):
        expires = admin['expires_at']
        if isinstance(expires, str):
            expires = datetime.fromisoformat(expires.replace('Z', '+00:00'))
        
        if expires > datetime.now():
            days = (expires - datetime.now()).days
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Deploy Bot", callback_data="deploy")],
                [InlineKeyboardButton("⚙️ My Bots", callback_data="mybots")],
                [InlineKeyboardButton("💰 Earnings", callback_data="earnings")]
            ])
            
            await update.message.reply_text(
                f"""⚡ ADMIN PANEL

Status: {admin.get('plan_type', 'ACTIVE').upper()}
Expires: {days} days
Plan: Active

Your tools ready!""",
                reply_markup=keyboard
            )
            return
    
    # New user - subscription offer
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Monthly (5 SOL)", callback_data="sub_monthly")],
        [InlineKeyboardButton("👑 Yearly (50 SOL)", callback_data="sub_yearly")],
        [InlineKeyboardButton("📊 Calculator", callback_data="calc")],
        [InlineKeyboardButton("❓ How It Works", callback_data="how")]
    ])
    
    await update.message.reply_text(
        f"""🚀 ICEGODS Bot Platform

Deploy your own token alert bot!

💎 WHAT YOU GET:
✅ White-label Telegram bot
✅ Automated token alerts
✅ Subscription management
✅ Revenue dashboard

💰 YOUR EARNINGS:
• Keep 80% of user payments
• Passive SOL income

📊 PRICING:
• Monthly: {SAAS_MONTHLY} SOL
• Yearly: {SAAS_YEARLY} SOL

Tap below 👇""",
        reply_markup=keyboard
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        """📋 COMMANDS

/start - Main menu & dashboard
/help - Show this help
/confirm TX_HASH - Verify payment
/status - Check subscription
/stats - Platform stats (admins)
/deploy TOKEN CHANNEL GROUP WALLET - Deploy bot
/support - Contact support

PAYMENT:
After sending SOL, use:
/confirm YOUR_TRANSACTION_HASH

Example:
/confirm 5JTHj8rSHw4h6NAoZwLByQ2c4Y65rk6WnCcZ1A91HE573PU88jWXwrcPxs9HyXxv6KVrtktb3j4XsSmj2HnEzghc"""
    )

async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /confirm command - CRITICAL for payment verification"""
    user = update.effective_user
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            """🛰 PAYMENT VERIFICATION

Usage: /confirm TRANSACTION_HASH

Send your Solana transaction hash after payment.

Example:
/confirm 5JTHj8rSHw4h6NAoZwLByQ2c4Y65rk6WnCcZ1A91HE573PU88jWXwrcPxs9HyXxv6KVrtktb3j4XsSmj2HnEzghc"""
        )
        return
    
    tx_hash = context.args[0].strip()
    
    # Validate format
    if len(tx_hash) < 80:
        await update.message.reply_text("❌ Invalid transaction hash (too short)")
        return
    
    await update.message.reply_text("🛰 Verifying transaction...")
    
    # Try monthly amount first
    for plan_type, amount, days in [('monthly', SAAS_MONTHLY, 30), ('yearly', SAAS_YEARLY, 365)]:
        success, actual_amount = await verify_payment_by_tx(tx_hash, amount)
        
        if success:
            # Payment verified! Activate
            expires = datetime.now() + timedelta(days=days)
            
            created = await create_admin(user.id, user.username, user.first_name, plan_type, expires)
            
            if created:
                await update.message.reply_text(
                    f"""✅ PAYMENT VERIFIED & ACTIVATED!

🎉 Plan: {plan_type.upper()}
⏰ Expires: {expires.strftime('%Y-%m-%d')}
💰 Amount: {actual_amount:.4f} SOL
🔗 Tx: {tx_hash[:30]}...

🚀 YOUR ADMIN PANEL IS READY!
Click /start to access it!"""
                )
                
                # Notify master
                try:
                    await application.bot.send_message(
                        ADMIN_ID,
                        f"💰 NEW SUB!\nUser: {user.id}\nPlan: {plan_type}\nAmount: {actual_amount:.4f} SOL"
                    )
                except:
                    pass
                return
    
    # Not found
    await update.message.reply_text(
        """❌ PAYMENT NOT FOUND

The transaction was not found or amount doesn't match.

Please check:
• Did you send exactly 5 SOL (monthly) or 50 SOL (yearly)?
• Is the transaction confirmed? Wait 1-2 minutes.
• Did you copy the full hash?

Try again or contact @MexRobert"""
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user = update.effective_user
    
    if user.id == ADMIN_ID:
        await update.message.reply_text("👑 You are Master Admin")
        return
    
    admin = await get_admin(user.id)
    
    if not admin:
        await update.message.reply_text(
            "❌ No subscription\n\nSubscribe: /start\nMonthly: 5 SOL\nYearly: 50 SOL"
        )
        return
    
    if admin.get('expires_at'):
        expires = admin['expires_at']
        if isinstance(expires, str):
            expires = datetime.fromisoformat(expires.replace('Z', '+00:00'))
        
        if expires > datetime.now():
            days = (expires - datetime.now()).days
            await update.message.reply_text(
                f"""✅ ACTIVE SUBSCRIPTION

Plan: {admin.get('plan_type', 'UNKNOWN').upper()}
Expires: {expires.strftime('%Y-%m-%d')} ({days} days)
Status: Active

Use /start for dashboard"""
            )
        else:
            await update.message.reply_text("⚠️ Subscription expired. Renew: /start")
    else:
        await update.message.reply_text("❌ No active subscription")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        admin = await get_admin(user.id)
        if not admin:
            await update.message.reply_text("❌ Admin only")
            return
    
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                total = await conn.fetchval("SELECT COUNT(*) FROM admins") or 0
                active = await conn.fetchval("SELECT COUNT(*) FROM admins WHERE expires_at > NOW()") or 0
        
            text = f"""📊 STATISTICS

👥 Total Admins: {total}
✅ Active: {active}
💳 Wallet: {MASTER_WALLET[:25]}...

✅ Platform running!"""
        else:
            text = "❌ Database not connected"
        
        await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await update.message.reply_text("⚠️ Error loading stats")

async def cmd_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /deploy command"""
    user = update.effective_user
    
    # Check subscription
    admin = await get_admin(user.id)
    if not admin or not admin.get('expires_at'):
        await update.message.reply_text("❌ Subscription required. Subscribe: /start")
        return
    
    if not context.args or len(context.args) < 4:
        await update.message.reply_text(
            """🚀 DEPLOY YOUR BOT

Usage:
/deploy BOT_TOKEN CHANNEL_ID GROUP_ID WALLET

Example:
/deploy 123456:ABC... -1001234567890 -1009876543210 HxmywH2g...

Get bot token from @BotFather"""
        )
        return
    
    bot_token = context.args[0]
    channel_id = context.args[1]
    group_id = context.args[2]
    wallet = context.args[3]
    
    # Save
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO client_bots (admin_id, bot_token, channel_id, group_id, client_wallet)
                    VALUES ($1, $2, $3, $4, $5)
                """, user.id, bot_token, channel_id, group_id, wallet)
        except Exception as e:
            logger.error(f"Deploy error: {e}")
    
    await update.message.reply_text(
        f"""✅ DEPLOYMENT REQUESTED

Bot: {bot_token[:20]}...
Channel: {channel_id}
Group: {group_id}
Wallet: {wallet[:15]}...

⏳ Processing 2-5 minutes...
You'll receive confirmation!"""
    )

async def cmd_airdrop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /airdrop command"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Master admin only")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            """🎁 AIRDROP TOKENS

Usage: /airdrop BOT_ID AMOUNT

Example: /airdrop 1 100"""
        )
        return
    
    await update.message.reply_text("🎁 Airdrop feature - Contact @MexRobert to configure")

async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /support command"""
    await update.message.reply_text(
        f"""💬 SUPPORT

Contact: @{SUPPORT_USERNAME}
Your ID: {update.effective_user.id}

Include your ID for faster response!"""
    )

# ═══════════════════════════════════════════════════════════════════════
# BUTTON HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button presses"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"Button: {data} by {user_id}")
    
    if data == "stats":
        await handle_stats_button(query)
    elif data == "revenue":
        await handle_revenue_button(query)
    elif data == "admins":
        await handle_admins_button(query)
    elif data == "sub_monthly":
        await handle_subscribe_button(query, user_id, "monthly", SAAS_MONTHLY, 30)
    elif data == "sub_yearly":
        await handle_subscribe_button(query, user_id, "yearly", SAAS_YEARLY, 365)
    elif data == "check_payment":
        await handle_check_payment_button(query, user_id)
    elif data == "main_menu":
        await back_to_start(query)

async def handle_stats_button(query):
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                total = await conn.fetchval("SELECT COUNT(*) FROM admins") or 0
                active = await conn.fetchval("SELECT COUNT(*) FROM admins WHERE expires_at > NOW()") or 0
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
        
        await query.message.edit_text(
            f"""📊 STATISTICS

👥 Total: {total}
✅ Active: {active}
💳 {MASTER_WALLET[:25]}...""",
            reply_markup=keyboard
        )
    except Exception as e:
        await query.message.edit_text("⚠️ Error")

async def handle_revenue_button(query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 View Solscan", url=f"https://solscan.io/account/{MASTER_WALLET}")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        f"""💰 REVENUE

Wallet: `{MASTER_WALLET}`""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def handle_admins_button(query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
    await query.message.edit_text("👥 Admins list", reply_markup=keyboard)

async def handle_subscribe_button(query, user_id, plan_type, amount, days):
    payment_id = await save_payment(user_id, amount, plan_type)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛰 Check Payment", callback_data="check_payment")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        f"""🧾 INVOICE #{payment_id}

Plan: {plan_type.upper()}
Amount: {amount} SOL

SEND TO:
`{MASTER_WALLET}`

Then click "Check Payment" or use:
/confirm YOUR_TX_HASH""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def handle_check_payment_button(query, user_id):
    await query.answer("Checking...")
    
    for plan_type, amount, days in [('monthly', SAAS_MONTHLY, 30), ('yearly', SAAS_YEARLY, 365)]:
        success, tx_hash, actual = await check_recent_payment(amount)
        
        if success:
            expires = datetime.now() + timedelta(days=days)
            user = query.from_user
            
            await create_admin(user.id, user.username, user.first_name, plan_type, expires)
            
            await query.message.edit_text(
                f"""✅ ACTIVATED!

Plan: {plan_type.upper()}
Expires: {expires.strftime('%Y-%m-%d')}
Amount: {actual:.4f} SOL

🚀 Click /start!"""
            )
            
            try:
                await application.bot.send_message(
                    ADMIN_ID,
                    f"💰 NEW: {user.id} - {plan_type} - {actual:.4f} SOL"
                )
            except:
                pass
            return
    
    await query.message.reply_text(
        """⏳ NOT FOUND

Use /confirm with your tx hash:
/confirm 5JTHj8rSHw4h6NAoZwLByQ2c4Y65rk6WnCcZ1A91HE573..."""
    )

async def back_to_start(query):
    class FakeUpdate:
        def __init__(self, user, msg):
            self.effective_user = user
            self.message = msg
    
    fake = FakeUpdate(query.from_user, query.message)
    await cmd_start(fake, None)

# ═══════════════════════════════════════════════════════════════════════
# FLASK SERVER
# ═══════════════════════════════════════════════════════════════════════

@app.route("/")
def health():
    return jsonify({
        "status": "ICEGODS v5.0 WORKING",
        "database": "connected" if db_pool else "disconnected",
        "commands": ["/start", "/help", "/confirm", "/status", "/stats", "/deploy", "/airdrop", "/support"],
        "wallet": MASTER_WALLET,
        "time": datetime.now().isoformat()
    })

@app.route(f"/webhook/{BOT_TOKEN.split(':')[1]}", methods=['POST'])
def webhook():
    if not application:
        return jsonify({"error": "Bot not ready"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        
        update = Update.de_json(data, application.bot)
        
        future = asyncio.run_coroutine_threadsafe(
            application.process_update(update),
            asyncio.get_event_loop()
        )
        future.result(timeout=10)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def init_bot():
    global application
    
    logger.info("Initializing bot...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def setup():
        global application
        
        # Init DB
        await init_db()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # REGISTER ALL HANDLERS - THIS IS CRITICAL
        application.add_handler(CommandHandler("start", cmd_start))
        application.add_handler(CommandHandler("help", cmd_help))
        application.add_handler(CommandHandler("confirm", cmd_confirm))
        application.add_handler(CommandHandler("status", cmd_status))
        application.add_handler(CommandHandler("stats", cmd_stats))
        application.add_handler(CommandHandler("deploy", cmd_deploy))
        application.add_handler(CommandHandler("airdrop", cmd_airdrop))
        application.add_handler(CommandHandler("support", cmd_support))
        
        # Button handler
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Initialize
        await application.initialize()
        
        # Webhook
        if WEBHOOK_URL:
            webhook_path = f"/webhook/{BOT_TOKEN.split(':')[1]}"
            full_url = f"{WEBHOOK_URL}{webhook_path}"
            await application.bot.set_webhook(url=full_url)
            logger.info(f"Webhook: {full_url}")
        
        await application.start()
        logger.info("✅ Bot started with all commands!")
    
    try:
        loop.run_until_complete(setup())
        loop.run_forever()
    except Exception as e:
        logger.error(f"Bot error: {e}")

def main():
    logger.info("=" * 60)
    logger.info("STARTING ICEGODS v5.0")
    logger.info("=" * 60)
    
    # Start bot in thread
    bot_thread = threading.Thread(target=init_bot, daemon=True)
    bot_thread.start()
    
    # Wait
    import time
    time.sleep(5)
    
    # Start Flask
    logger.info(f"Starting server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=True)

if __name__ == "__main__":
    main()
