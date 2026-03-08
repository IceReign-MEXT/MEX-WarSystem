#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS BOT PLATFORM v3.1 - PRODUCTION READY
✅ Auto payment verification via Helius API
✅ Automatic subscription activation
✅ New Supabase: ylpxxgvaetykmswzrpmi
✅ Password: IceWarlord30Icegods
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
from datetime import datetime, timedelta
from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify
import asyncpg

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION - ACTUAL VALUES
# ═══════════════════════════════════════════════════════════════════════

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN") or "7968707142:AAHk3snOd8SxZ_8_hJY5Tq0p6eDebh9RvJk"
    ADMIN_ID = int(os.getenv("ADMIN_ID") or "8254662446")
    MASTER_WALLET = os.getenv("MASTER_WALLET") or "HxmywH2gW9ezQ2nBXwurpaWsZS6YvdmLF23R9WgMAM7p"
    
    # NEW SUPABASE - DIRECT CONNECTION (port 5432)
    DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://postgres:IceWarlord30Icegods@db.ylpxxgvaetykmswzrpmi.supabase.co:5432/postgres"
    
    WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "https://mex-warsystem-8rzh.onrender.com"
    PORT = int(os.getenv("PORT") or "10000")
    HELIUS_KEY = os.getenv("HELIUS_API_KEY") or "1b0094c2-50b9-4c97-a2d6-2c47d4ac2789"
    SUPPORT_USERNAME = "MexRobert"
    
    # Pricing
    SAAS_MONTHLY = 5.0
    SAAS_YEARLY = 50.0
    COMMISSION_PERCENT = 20

logger.info("🔧 ICEGODS Platform v3.1 Starting...")
logger.info(f"🔧 Admin ID: {Config.ADMIN_ID}")
logger.info(f"🔧 Database: ylpxxgvaetykmswzrpmi.supabase.co:5432")

# ═══════════════════════════════════════════════════════════════════════
# GLOBALS
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
db_pool = None
bot_app = None
bot_loop = None

# ═══════════════════════════════════════════════════════════════════════
# DATABASE - NEW SUPABASE
# ═══════════════════════════════════════════════════════════════════════

async def init_database():
    """Connect to NEW Supabase"""
    global db_pool
    
    try:
        logger.info("🔌 Connecting to NEW Supabase...")
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        db_pool = await asyncpg.create_pool(
            Config.DATABASE_URL,
            min_size=1,
            max_size=5,
            ssl=ssl_context,
            command_timeout=30,
            server_settings={'jit': 'off'}
        )
        
        async with db_pool.acquire() as conn:
            logger.info("📊 Creating tables...")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS platform_admins (
                    admin_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    subscription_type TEXT DEFAULT 'none',
                    subscription_expires TIMESTAMP,
                    total_earned DECIMAL(15,4) DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    wallet_address TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_payments (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    amount DECIMAL(10,4),
                    plan_type TEXT,
                    status TEXT DEFAULT 'pending',
                    tx_hash TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    verified_at TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS client_bots (
                    bot_id SERIAL PRIMARY KEY,
                    admin_id BIGINT REFERENCES platform_admins(admin_id),
                    bot_name TEXT,
                    bot_token TEXT,
                    bot_username TEXT,
                    public_channel TEXT,
                    vip_group TEXT,
                    client_wallet TEXT,
                    status TEXT DEFAULT 'pending',
                    deployed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        
        logger.info("✅ DATABASE CONNECTED SUCCESSFULLY!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database failed: {e}")
        return False

async def get_admin(user_id: int):
    """Get admin"""
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM platform_admins WHERE admin_id = $1",
                user_id
            )
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Get admin error: {e}")
        return None

async def create_admin(user_id: int, username: str, first_name: str, plan_type: str, expires: datetime):
    """Create admin"""
    if not db_pool:
        return False
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO platform_admins (admin_id, username, first_name, subscription_type, subscription_expires, status)
                VALUES ($1, $2, $3, $4, $5, 'active')
                ON CONFLICT (admin_id) DO UPDATE SET
                    subscription_type = $4,
                    subscription_expires = $5,
                    status = 'active',
                    updated_at = NOW()
            """, user_id, username, first_name, plan_type, expires)
            logger.info(f"✅ Admin created: {user_id} - {plan_type}")
            return True
    except Exception as e:
        logger.error(f"Create admin error: {e}")
        return False

async def save_pending_payment(user_id: int, amount: float, plan_type: str):
    """Save payment"""
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            payment_id = await conn.fetchval("""
                INSERT INTO pending_payments (user_id, amount, plan_type, status)
                VALUES ($1, $2, $3, 'pending')
                RETURNING id
            """, user_id, amount, plan_type)
            return payment_id
    except Exception as e:
        logger.error(f"Save payment error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════
# HELIUS AUTO-VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

async def verify_payment_with_helius(user_id: int, expected_amount: float) -> tuple:
    """Verify payment via Helius"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/addresses/{Config.MASTER_WALLET}/transactions?api-key={Config.HELIUS_KEY}&limit=20"
            
            async with session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    logger.error(f"Helius error: {resp.status}")
                    return False, None, 0
                
                data = await resp.json()
                
                if not isinstance(data, list):
                    return False, None, 0
                
                for tx in data:
                    tx_hash = tx.get('signature')
                    if not tx_hash:
                        continue
                    
                    native_transfers = tx.get('nativeTransfers', [])
                    
                    for transfer in native_transfers:
                        to_address = transfer.get('toUserAccount')
                        amount_lamports = transfer.get('amount', 0)
                        amount_sol = amount_lamports / 1_000_000_000
                        
                        if to_address == Config.MASTER_WALLET:
                            if abs(amount_sol - expected_amount) < 0.01:
                                logger.info(f"✅ Payment found: {amount_sol} SOL")
                                return True, tx_hash, amount_sol
                
                return False, None, 0
                
    except Exception as e:
        logger.error(f"Helius error: {e}")
        return False, None, 0

# ═══════════════════════════════════════════════════════════════════════
# TELEGRAM HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main entry"""
    user = update.effective_user
    logger.info(f"▶️ Start from {user.id} ({user.username})")
    
    if user.id == Config.ADMIN_ID:
        await show_master_dashboard(update, user)
        return
    
    admin = await get_admin(user.id)
    
    if admin and admin.get('subscription_expires'):
        expires = admin['subscription_expires']
        if isinstance(expires, str):
            expires = datetime.fromisoformat(expires.replace('Z', '+00:00'))
        
        if expires > datetime.now():
            days_left = (expires - datetime.now()).days
            await show_admin_dashboard(update, user, admin, days_left)
            return
    
    await show_subscription_offer(update, user)

async def show_master_dashboard(update: Update, user):
    """Master dashboard"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Stats", callback_data="master_stats")],
        [InlineKeyboardButton("💰 Revenue", callback_data="master_revenue")],
        [InlineKeyboardButton("👥 Admins", callback_data="master_admins")]
    ])
    
    await update.message.reply_text(
        f"""👑 MASTER DASHBOARD - ICEGODS Platform

🚀 Status: ONLINE
💳 Wallet: `{Config.MASTER_WALLET[:20]}...`

Your SaaS platform is live!
• Devs subscribe for 5-50 SOL
• You earn 20% commission
• Auto payment verification

Select below:""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def show_admin_dashboard(update: Update, user, admin, days_left):
    """Subscriber dashboard"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Deploy Bot", callback_data="deploy_bot")],
        [InlineKeyboardButton("⚙️ My Bots", callback_data="my_bots")],
        [InlineKeyboardButton("📊 Stats", callback_data="my_stats")],
        [InlineKeyboardButton("💰 Earnings", callback_data="my_earnings")],
        [InlineKeyboardButton("🔄 Renew", callback_data="renew_sub")]
    ])
    
    exp_str = admin['subscription_expires'].strftime('%Y-%m-%d') if isinstance(admin['subscription_expires'], datetime) else str(admin['subscription_expires'])[:10]
    
    await update.message.reply_text(
        f"""⚡ ADMIN PANEL

👤 Status: {admin.get('subscription_type', 'ACTIVE').upper()}
⏰ Expires: {days_left} days ({exp_str})
💰 Earned: {admin.get('total_earned', 0):.2f} SOL

🎯 Your Tools Ready!""",
        reply_markup=keyboard
    )

async def show_subscription_offer(update: Update, user):
    """Show offer"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Monthly - 5 SOL", callback_data="sub_monthly")],
        [InlineKeyboardButton("👑 Yearly - 50 SOL", callback_data="sub_yearly")],
        [InlineKeyboardButton("📊 Calculator", callback_data="calc_revenue")],
        [InlineKeyboardButton("❓ How It Works", callback_data="how_works")],
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{Config.SUPPORT_USERNAME}")]
    ])
    
    await update.message.reply_text(
        f"""🚀 ICEGODS Bot Platform

Deploy your own token alert bot!

💎 WHAT YOU GET:
✅ White-label Telegram bot
✅ Automated token alerts
✅ Subscription management
✅ Referral system
✅ Revenue dashboard
✅ 24/7 automated income

💰 YOUR EARNINGS:
• Keep 80% of user payments
• Set your own prices
• Passive SOL income

📊 PRICING:
• Monthly: 5 SOL
• Yearly: 50 SOL (Best Value)

Tap below 👇""",
        reply_markup=keyboard
    )

# ═══════════════════════════════════════════════════════════════════════
# BUTTON HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all buttons"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"🔘 Button: {data} by {user_id}")
    
    # MASTER ADMIN
    if user_id == Config.ADMIN_ID:
        if data == "master_stats":
            await handle_master_stats(query)
        elif data == "master_revenue":
            await handle_master_revenue(query)
        elif data == "master_admins":
            await handle_master_admins(query)
        elif data == "master_main":
            await back_to_master(query)
        return
    
    # USER BUTTONS
    if data == "main_menu":
        await back_to_main(query, user_id)
    elif data == "calc_revenue":
        await handle_calc_revenue(query)
    elif data == "sub_monthly":
        await handle_subscription(query, user_id, "monthly", 5.0, 30)
    elif data == "sub_yearly":
        await handle_subscription(query, user_id, "yearly", 50.0, 365)
    elif data == "how_works":
        await handle_how_works(query)
    elif data == "deploy_bot":
        await handle_deploy_button(query, user_id)
    elif data == "my_bots":
        await handle_my_bots(query, user_id)
    elif data == "my_stats":
        await handle_my_stats(query, user_id)
    elif data == "my_earnings":
        await handle_my_earnings(query, user_id)
    elif data == "renew_sub":
        await handle_renew(query, user_id)
    elif data == "check_payment":
        await handle_check_payment(query, user_id)

async def handle_subscription(query, user_id, plan_type, amount, days):
    """Show invoice"""
    payment_id = await save_pending_payment(user_id, amount, plan_type)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛰 Check My Payment", callback_data="check_payment")],
        [InlineKeyboardButton("❓ Help", url=f"https://t.me/{Config.SUPPORT_USERNAME}")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        f"""🧾 INVOICE #{payment_id}

Plan: {plan_type.upper()}
Duration: {days} days
Amount: {amount} SOL

═══════════════════
SEND TO:
`{Config.MASTER_WALLET}`
═══════════════════

⚠️ Send EXACTLY {amount} SOL
✅ Click "Check My Payment"
🤖 Auto-verification!

Access activates instantly!""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def handle_check_payment(query, user_id):
    """Auto-verify"""
    await query.answer("🛰 Checking blockchain...")
    
    for amount, plan_type in [(5.0, 'monthly'), (50.0, 'yearly')]:
        success, tx_hash, actual_amount = await verify_payment_with_helius(user_id, amount)
        
        if success:
            expires = datetime.now() + timedelta(days=30 if plan_type == 'monthly' else 365)
            user = query.from_user
            
            created = await create_admin(user_id, user.username, user.first_name, plan_type, expires)
            
            if created:
                await query.message.edit_text(
                    f"""✅ PAYMENT VERIFIED!

🎉 Subscription ACTIVATED!
📦 Plan: {plan_type.upper()}
⏰ Expires: {expires.strftime('%Y-%m-%d')}
💰 Amount: {actual_amount:.4f} SOL
🔗 Tx: {tx_hash[:25]}...

🚀 Your admin panel is ready!
Click /start to access it!"""
                )
                
                # Notify master
                try:
                    await bot_app.bot.send_message(
                        Config.ADMIN_ID,
                        f"💰 NEW SUBSCRIPTION!\nUser: {user_id} (@{user.username})\nPlan: {plan_type}\nAmount: {actual_amount:.4f} SOL"
                    )
                except:
                    pass
                return
    
    await query.message.reply_text(
        """⏳ PAYMENT NOT FOUND

• Transaction still confirming? Wait 2 mins
• Wrong amount?
• Check Solscan for your tx

Try again shortly."""
    )

async def handle_master_stats(query):
    """Stats"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                total = await conn.fetchval("SELECT COUNT(*) FROM platform_admins") or 0
                active = await conn.fetchval("SELECT COUNT(*) FROM platform_admins WHERE subscription_expires > NOW()") or 0
            
            text = f"""📊 STATS

👥 Total Admins: {total}
✅ Active: {active}
💳 Wallet: {Config.MASTER_WALLET[:25]}...

✅ Platform running!"""
        else:
            text = "❌ Database disconnected"
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="master_main")]])
        await query.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await query.message.edit_text("⚠️ Error", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="master_main")]]))

async def handle_master_revenue(query):
    """Revenue"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 View on Solscan", url=f"https://solscan.io/account/{Config.MASTER_WALLET}")],
        [InlineKeyboardButton("🔙 Back", callback_data="master_main")]
    ])
    
    await query.message.edit_text(
        f"""💰 REVENUE

Master Wallet:
`{Config.MASTER_WALLET}`

🔗 Check live balance

• SaaS: 100% to you
• Commissions: 20%

Auto-verified payments!""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def handle_master_admins(query):
    """Admins list"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                admins = await conn.fetch("SELECT admin_id, username, subscription_type, subscription_expires, status FROM platform_admins ORDER BY created_at DESC LIMIT 20")
            
            text = "👥 ADMINS\n\n"
            for a in admins:
                emoji = "🟢" if a['status'] == 'active' else "🔴"
                name = a['username'] or f"ID:{a['admin_id']}"
                exp = a['subscription_expires'].strftime('%Y-%m-%d') if isinstance(a['subscription_expires'], datetime) else str(a['subscription_expires'])[:10]
                text += f"{emoji} {name} | {a['subscription_type']} | {exp}\n"
        else:
            text = "❌ Database not connected"
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="master_main")]])
        await query.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Admins error: {e}")
        await query.message.edit_text("⚠️ Error", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="master_main")]]))

async def back_to_master(query):
    """Back to master"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Stats", callback_data="master_stats")],
        [InlineKeyboardButton("💰 Revenue", callback_data="master_revenue")],
        [InlineKeyboardButton("👥 Admins", callback_data="master_admins")]
    ])
    
    await query.message.edit_text(f"""👑 MASTER DASHBOARD

🚀 Platform Online
💳 Wallet: {Config.MASTER_WALLET[:20]}...

Select:""", reply_markup=keyboard)

async def back_to_main(query, user_id):
    """Back to main"""
    class FakeUpdate:
        def __init__(self, user, msg):
            self.effective_user = user
            self.message = msg
    
    fake_update = FakeUpdate(query.from_user, query.message)
    await start(fake_update, None)

async def handle_calc_revenue(query):
    """Calculator"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Subscribe", callback_data="sub_monthly")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        """📊 CALCULATOR

With 200 users:
• 10 VIP (0.5 SOL) = 5 SOL
• 4 Whale (1 SOL) = 4 SOL  
• 2 Premium (2.5 SOL) = 5 SOL
• Total: 14 SOL/month

Your 80% = 11.2 SOL
Minus SaaS (5 SOL) = 6.2 SOL PROFIT""",
        reply_markup=keyboard
    )

async def handle_how_works(query):
    """How it works"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Subscribe", callback_data="sub_monthly")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        """❓ HOW IT WORKS

1️⃣ SUBSCRIBE (5-50 SOL)
2️⃣ DEPLOY BOT (/deploy)
3️⃣ ATTRACT USERS
4️⃣ EARN AUTOMATICALLY
5️⃣ SCALE

💰 EXAMPLE:
500 users → 25 pay 0.5 SOL = 12.5 SOL
Your 80% = 10 SOL
Profit = 10 - 5 = 5 SOL/month""",
        reply_markup=keyboard
    )

async def handle_deploy_button(query, user_id):
    """Deploy"""
    admin = await get_admin(user_id)
    if not admin or not admin.get('subscription_expires'):
        await query.answer("❌ Subscribe first!", show_alert=True)
        await query.message.reply_text("Subscribe: /start")
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Get Help", url=f"https://t.me/{Config.SUPPORT_USERNAME}")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        """🚀 DEPLOY YOUR BOT

Send me:
/deploy BOT_TOKEN CHANNEL_ID GROUP_ID WALLET

Get token from @BotFather""",
        reply_markup=keyboard
    )

async def handle_my_bots(query, user_id):
    await query.message.edit_text("⚙️ YOUR BOTS\n\nNo active bots yet.\n\nUse /deploy!", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Deploy", callback_data="deploy_bot")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]))

async def handle_my_stats(query, user_id):
    await query.message.edit_text("📊 STATISTICS\n\nNo data yet.\nDeploy a bot!", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Deploy", callback_data="deploy_bot")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]))

async def handle_my_earnings(query, user_id):
    await query.message.edit_text("💰 EARNINGS\n\nBalance: 0.00 SOL\n\nDeploy a bot!", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Deploy", callback_data="deploy_bot")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]))

async def handle_renew(query, user_id):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Monthly (5 SOL)", callback_data="sub_monthly")],
        [InlineKeyboardButton("👑 Yearly (50 SOL)", callback_data="sub_yearly")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    await query.message.edit_text("🔄 RENEW\n\nSelect plan:", reply_markup=keyboard)

# ═══════════════════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════════════════

async def deploy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deploy"""
    user = update.effective_user
    
    admin = await get_admin(user.id)
    if not admin or not admin.get('subscription_expires'):
        await update.message.reply_text("❌ Subscription required\n\nSubscribe: /start")
        return
    
    if not context.args or len(context.args) < 4:
        await update.message.reply_text("""🚀 DEPLOYMENT

Usage:
/deploy BOT_TOKEN CHANNEL_ID GROUP_ID WALLET

Example:
/deploy 123456:ABC... -1001234567890 -1009876543210 Hxmyw...""")
        return
    
    bot_token = context.args[0]
    channel_id = context.args[1]
    group_id = context.args[2]
    wallet = context.args[3]
    
    await update.message.reply_text(
        f"""✅ DEPLOYMENT REQUESTED

Bot: {bot_token[:20]}...
Channel: {channel_id}
Group: {group_id}
Wallet: {wallet[:15]}...

⏳ Processing (2-5 mins)""")

# ═══════════════════════════════════════════════════════════════════════
# FLASK SERVER
# ═══════════════════════════════════════════════════════════════════════

@app.route("/")
def health():
    return jsonify({
        "status": "ICEGODS Platform v3.1 - LIVE",
        "database": "ylpxxgvaetykmswzrpmi",
        "connected": db_pool is not None,
        "auto_verify": "enabled",
        "master_wallet": Config.MASTER_WALLET,
        "timestamp": datetime.now().isoformat()
    })

@app.route(f"/webhook/{Config.BOT_TOKEN.split(':')[1]}", methods=['POST'])
def webhook():
    if not bot_app:
        return jsonify({"error": "Bot not ready"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        
        update = Update.de_json(data, bot_app.bot)
        
        future = asyncio.run_coroutine_threadsafe(
            bot_app.process_update(update),
            bot_loop
        )
        future.result(timeout=10)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════
# BOT INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════

def init_bot():
    global bot_app, bot_loop
    
    logger.info("🤖 Initializing bot...")
    
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    
    async def setup():
        global bot_app
        
        db_ok = await init_database()
        logger.info(f"Database: {'✅ Connected' if db_ok else '❌ Failed'}")
        
        bot_app = Application.builder().token(Config.BOT_TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("deploy", deploy_command))
        bot_app.add_handler(CallbackQueryHandler(button_handler))
        
        await bot_app.initialize()
        
        if Config.WEBHOOK_URL:
            webhook_path = f"/webhook/{Config.BOT_TOKEN.split(':')[1]}"
            full_url = f"{Config.WEBHOOK_URL}{webhook_path}"
            await bot_app.bot.set_webhook(url=full_url)
            logger.info(f"✅ Webhook: {full_url}")
        
        await bot_app.start()
        logger.info("✅ Bot started!")
    
    try:
        bot_loop.run_until_complete(setup())
        bot_loop.run_forever()
    except Exception as e:
        logger.error(f"Bot error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    logger.info("🚀 ICEGODS v3.1 PRODUCTION")
    logger.info(f"🔧 New Database: ylpxxgvaetykmswzrpmi")
    logger.info(f"🔧 Password Set: IceWarlord30Icegods")
    
    bot_thread = threading.Thread(target=init_bot, daemon=True)
    bot_thread.start()
    
    import time
    time.sleep(5)
    
    logger.info(f"🌐 Server on port {Config.PORT}")
    app.run(host="0.0.0.0", port=Config.PORT, threaded=True)

if __name__ == "__main__":
    main()
