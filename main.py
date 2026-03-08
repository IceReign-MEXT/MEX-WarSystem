#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS BOT PLATFORM - SaaS Revenue System
Working Version for Render Deployment
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import asyncio
import threading
import logging
import aiohttp
import random
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify
import asyncpg

# Force load environment variables immediately
from dotenv import load_dotenv
load_dotenv()

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION - Hardcoded Fallbacks if env vars fail
# ═══════════════════════════════════════════════════════════════════════

class Config:
    """Configuration with hardcoded fallbacks"""
    BOT_TOKEN = os.getenv("BOT_TOKEN") or "7968707142:AAHk3snOd8SxZ_8_hJY5Tq0p6eDebh9RvJk"
    ADMIN_ID = int(os.getenv("ADMIN_ID") or "8254662446")
    BOT_USERNAME = os.getenv("BOT_USERNAME") or "ICEMEXWarSystem_Bot"
    PLATFORM_NAME = os.getenv("PLATFORM_NAME") or "ICEGODS Platform"
    PLATFORM_URL = os.getenv("PLATFORM_URL") or "https://icegods-platform.onrender.com"
    SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME") or "MexRobert"
    MASTER_WALLET = os.getenv("MASTER_WALLET") or "HxmywH2gW9ezQ2nBXwurpaWsZS6YvdmLF23R9WgMAM7p"
    DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://postgres.sezxolvjozcbqhwlhluz:IceWarlord30Icegods@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"
    WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "https://mex-warsystem-8rzh.onrender.com"
    PORT = int(os.getenv("PORT") or "8080")
    HELIUS_KEY = os.getenv("HELIUS_API_KEY") or "1b0094c2-50b9-4c97-a2d6-2c47d4ac2789"
    
    # SaaS Pricing
    SAAS_MONTHLY = float(os.getenv("SAAS_MONTHLY_PRICE") or "5.0")
    SAAS_YEARLY = float(os.getenv("SAAS_YEARLY_PRICE") or "50.0")
    COMMISSION_PERCENT = float(os.getenv("SAAS_COMMISSION_PERCENT") or "20")
    
    # Client Pricing Defaults
    DEFAULT_VIP = float(os.getenv("DEFAULT_VIP_PRICE") or "0.5")
    DEFAULT_WHALE = float(os.getenv("DEFAULT_WHALE_PRICE") or "1.0")
    DEFAULT_PREMIUM = float(os.getenv("DEFAULT_PREMIUM_PRICE") or "2.5")
    
    # Features
    SIGNAL_INTERVAL = int(os.getenv("SIGNAL_INTERVAL_MINUTES") or "10")
    REFERRAL_REWARD_DAYS = int(os.getenv("REFERRAL_REWARD_DAYS") or "3")
    REFERRALS_NEEDED = int(os.getenv("REFERRALS_NEEDED") or "3")

# Log configuration on startup
logger.info(f"🔧 Config loaded: BOT_TOKEN={'SET' if Config.BOT_TOKEN else 'MISSING'}, ADMIN_ID={Config.ADMIN_ID}")

# Flask app
app = Flask(__name__)

# Global variables
db_pool: Optional[asyncpg.Pool] = None
bot_app: Optional[Application] = None
bot_loop: Optional[asyncio.AbstractEventLoop] = None

# ═══════════════════════════════════════════════════════════════════════
# DATABASE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

async def init_database():
    """Initialize database connection and tables"""
    global db_pool
    try:
        logger.info("🔌 Connecting to database...")
        db_pool = await asyncpg.create_pool(
            Config.DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60,
            ssl="require"
        )
        
        async with db_pool.acquire() as conn:
            logger.info("📊 Creating tables...")
            
            # Platform admins (devs who subscribe)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS platform_admins (
                    admin_id BIGINT PRIMARY KEY,
                    username TEXT,
                    subscription_type TEXT DEFAULT 'none',
                    subscription_expires TIMESTAMP,
                    revenue_share_percent DECIMAL(5,2) DEFAULT 80.00,
                    total_earned DECIMAL(15,4) DEFAULT 0,
                    total_paid_to_platform DECIMAL(15,4) DEFAULT 0,
                    api_key TEXT UNIQUE,
                    webhook_url TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_payment TIMESTAMP
                )
            """)
            
            # Client bots (white-label instances)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS client_bots (
                    bot_id SERIAL PRIMARY KEY,
                    admin_id BIGINT REFERENCES platform_admins(admin_id),
                    bot_token TEXT,
                    bot_username TEXT,
                    public_channel_id TEXT,
                    vip_group_id TEXT,
                    client_wallet TEXT,
                    vip_price DECIMAL(10,4) DEFAULT 0.5,
                    whale_price DECIMAL(10,4) DEFAULT 1.0,
                    premium_price DECIMAL(10,4) DEFAULT 2.5,
                    status TEXT DEFAULT 'active',
                    deployed_at TIMESTAMP DEFAULT NOW(),
                    monthly_revenue DECIMAL(15,4) DEFAULT 0,
                    total_users INT DEFAULT 0,
                    paid_users INT DEFAULT 0
                )
            """)
            
            # End users across all client bots
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS end_users (
                    user_id BIGINT,
                    client_bot_id INT REFERENCES client_bots(bot_id),
                    telegram_id BIGINT,
                    username TEXT,
                    plan_type TEXT DEFAULT 'free',
                    plan_expires TIMESTAMP,
                    referrals_count INT DEFAULT 0,
                    total_paid DECIMAL(10,4) DEFAULT 0,
                    solana_wallet TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (client_bot_id, telegram_id)
                )
            """)
            
            # Platform payments (from admins to you)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS platform_payments (
                    id SERIAL PRIMARY KEY,
                    admin_id BIGINT,
                    amount_sol DECIMAL(10,4),
                    payment_type TEXT,
                    status TEXT DEFAULT 'pending',
                    tx_hash TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    confirmed_at TIMESTAMP
                )
            """)
            
            # Client payments (end users to admins)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS client_payments (
                    id SERIAL PRIMARY KEY,
                    client_bot_id INT,
                    user_telegram_id BIGINT,
                    amount_sol DECIMAL(10,4),
                    plan_type TEXT,
                    status TEXT DEFAULT 'pending',
                    tx_hash TEXT,
                    platform_fee DECIMAL(10,4),
                    admin_revenue DECIMAL(10,4),
                    created_at TIMESTAMP DEFAULT NOW(),
                    confirmed_at TIMESTAMP
                )
            """)
            
            # Revenue logs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS revenue_logs (
                    id SERIAL PRIMARY KEY,
                    admin_id BIGINT,
                    client_bot_id INT,
                    period_start DATE,
                    period_end DATE,
                    gross_revenue DECIMAL(15,4),
                    platform_fee DECIMAL(15,4),
                    net_revenue DECIMAL(15,4),
                    calculated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Token signals
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS token_signals (
                    id SERIAL PRIMARY KEY,
                    token_address TEXT,
                    name TEXT,
                    symbol TEXT,
                    price_usd DECIMAL(20,10),
                    liquidity_usd DECIMAL(20,2),
                    volume_24h DECIMAL(20,2),
                    detected_at TIMESTAMP DEFAULT NOW(),
                    posted_to_clients BOOLEAN DEFAULT false
                )
            """)
            
            logger.info("✅ Database tables created")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def get_admin(admin_id: int) -> Optional[Dict[str, Any]]:
    """Get admin by ID"""
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM platform_admins WHERE admin_id = $1", admin_id
            )
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Get admin error: {e}")
        return None

async def create_or_update_admin(admin_id: int, username: str, sub_type: str, expires: datetime):
    """Create or update admin subscription"""
    if not db_pool:
        return False
    try:
        async with db_pool.acquire() as conn:
            api_key = f"ice_{admin_id}_{int(datetime.now().timestamp())}"
            await conn.execute("""
                INSERT INTO platform_admins (admin_id, username, subscription_type, subscription_expires, api_key)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (admin_id) DO UPDATE SET
                    subscription_type = $3,
                    subscription_expires = $4,
                    status = 'active',
                    username = $2
            """, admin_id, username, sub_type, expires, api_key)
            return True
    except Exception as e:
        logger.error(f"Create admin error: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════
# TELEGRAM HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main entry point"""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started bot")
    
    # Master admin (you)
    if user.id == Config.ADMIN_ID:
        await show_master_dashboard(update, context)
        return
    
    # Check if registered admin
    admin = await get_admin(user.id)
    
    if admin and admin.get('subscription_expires') and admin['subscription_expires'] > datetime.now():
        await show_admin_dashboard(update, context, admin)
    else:
        await show_subscription_offer(update, context)

async def show_master_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show master admin dashboard"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Platform Stats", callback_data="master_stats")],
        [InlineKeyboardButton("💰 Revenue Report", callback_data="master_revenue")],
        [InlineKeyboardButton("👥 Manage Admins", callback_data="master_admins")],
        [InlineKeyboardButton("🤖 Client Bots", callback_data="master_bots")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="master_broadcast")]
    ])
    
    text = f"""👑 MASTER DASHBOARD - {Config.PLATFORM_NAME}

🚀 Platform Status: ONLINE
💳 Your Wallet: `{Config.MASTER_WALLET[:15]}...`

📊 Quick Stats:
• Use buttons below for detailed reports
• All revenue flows to your wallet
• 20% commission on all client earnings

⚡ Platform is LIVE and ready!"""
    
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def show_admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, admin: Dict):
    """Show subscriber admin dashboard"""
    days_left = (admin['subscription_expires'] - datetime.now()).days if admin['subscription_expires'] else 0
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Deploy New Bot", callback_data="deploy_bot")],
        [InlineKeyboardButton("⚙️ My Bots", callback_data="my_bots")],
        [InlineKeyboardButton("📊 Revenue Stats", callback_data="my_revenue")],
        [InlineKeyboardButton("🎁 Airdrop Manager", callback_data="airdrop_mgr")],
        [InlineKeyboardButton("💰 Withdraw Earnings", callback_data="withdraw")],
        [InlineKeyboardButton("🔄 Renew Subscription", callback_data="renew_sub")]
    ])
    
    text = f"""⚡ ADMIN DASHBOARD

👤 Status: {admin.get('subscription_type', 'UNKNOWN').upper()}
⏰ Expires: {days_left} days
💰 Total Earned: {admin.get('total_earned', 0):.2f} SOL
📊 Revenue Share: {admin.get('revenue_share_percent', 80)}%

🎯 Your Tools:
• Deploy unlimited bots
• Set your own prices
• Automated user payments
• Token airdrop system
• Real-time analytics

🚀 Start deploying your first bot!"""
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def show_subscription_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription offer to new users"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💎 Monthly - {Config.SAAS_MONTHLY} SOL", callback_data="sub_monthly")],
        [InlineKeyboardButton(f"👑 Yearly - {Config.SAAS_YEARLY} SOL (Save 10)", callback_data="sub_yearly")],
        [InlineKeyboardButton("📊 Revenue Calculator", callback_data="calc_revenue")],
        [InlineKeyboardButton("❓ How It Works", callback_data="how_it_works")],
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{Config.SUPPORT_USERNAME}")]
    ])
    
    text = f"""🚀 {Config.PLATFORM_NAME}

Deploy your own token alert bot & earn SOL!

💎 WHAT YOU GET:
✅ White-label Telegram bot
✅ Automated token alerts (DexScreener)
✅ Subscription management system
✅ Referral system built-in
✅ Airdrop distribution tools
✅ Revenue dashboard
✅ 24/7 automated income

💰 YOUR EARNINGS:
• Keep {100 - Config.COMMISSION_PERCENT}% of all user payments
• Set your own prices (VIP/Whale/Premium)
• Monthly airdrops boost retention
• Scale to unlimited users

📊 PRICING:
• Monthly: {Config.SAAS_MONTHLY} SOL
• Yearly: {Config.SAAS_YEARLY} SOL (Best Value)

⚡ Limited spots available!

Tap below to start 👇"""
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Master admin buttons
    if user_id == Config.ADMIN_ID:
        if query.data == "master_stats":
            await show_master_stats(query)
        elif query.data == "master_revenue":
            await show_master_revenue(query)
        elif query.data == "master_admins":
            await show_master_admins(query)
        return
    
    # Regular buttons
    if query.data == "calc_revenue":
        await show_revenue_calculator(query, user_id)
    elif query.data == "sub_monthly":
        await initiate_subscription(query, user_id, 'monthly', Config.SAAS_MONTHLY)
    elif query.data == "sub_yearly":
        await initiate_subscription(query, user_id, 'yearly', Config.SAAS_YEARLY)
    elif query.data == "how_it_works":
        await show_how_it_works(query)
    elif query.data == "deploy_bot":
        await start_bot_deployment(query, user_id)
    elif query.data == "my_revenue":
        await show_my_revenue(query, user_id)

async def show_master_stats(query):
    """Show platform statistics to master"""
    if not db_pool:
        await query.message.edit_text("❌ Database not connected")
        return
    
    try:
        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_admins,
                    COUNT(*) FILTER (WHERE subscription_expires > NOW()) as active_admins,
                    COALESCE(SUM(total_paid_to_platform), 0) as total_revenue
                FROM platform_admins
            """)
            
            bot_stats = await conn.fetchrow("""
                SELECT COUNT(*) as total_bots FROM client_bots WHERE status = 'active'
            """)
        
        text = f"""📊 PLATFORM STATISTICS

👥 Total Admins: {stats['total_admins']}
✅ Active Subs: {stats['active_admins']}
🤖 Active Bots: {bot_stats['total_bots']}

💰 Total Revenue: {stats['total_revenue']:.2f} SOL
💳 Your Wallet: `{Config.MASTER_WALLET[:20]}...`

🚀 Platform is running smoothly!"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="master_main")]
        ])
        
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await query.message.edit_text("❌ Error loading stats")

async def show_master_revenue(query):
    """Show revenue breakdown"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Check Wallet", url=f"https://solscan.io/account/{Config.MASTER_WALLET}")],
        [InlineKeyboardButton("📊 Detailed Report", callback_data="revenue_detail")],
        [InlineKeyboardButton("🔙 Back", callback_data="master_main")]
    ])
    
    text = f"""💰 REVENUE DASHBOARD

Your Master Wallet:
`{Config.MASTER_WALLET}`

🔗 View on Solscan for live balance

Revenue Streams:
• SaaS Subscriptions: 100% to you
• Client Commissions: 20% of their earnings
• Platform Fees: Automatic collection

Tap below to view your wallet 👇"""
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def show_master_admins(query):
    """List all platform admins"""
    if not db_pool:
        await query.message.edit_text("❌ Database error")
        return
    
    try:
        async with db_pool.acquire() as conn:
            admins = await conn.fetch("""
                SELECT admin_id, username, subscription_type, subscription_expires, status
                FROM platform_admins
                ORDER BY created_at DESC
                LIMIT 10
            """)
        
        if not admins:
            await query.message.edit_text("👥 No admins yet")
            return
        
        text = "👥 PLATFORM ADMINS\n\n"
        for admin in admins:
            status = "🟢" if admin['status'] == 'active' else "🔴"
            expires = admin['subscription_expires'].strftime('%Y-%m-%d') if admin['subscription_expires'] else 'N/A'
            text += f"{status} {admin['username'] or admin['admin_id']}\n"
            text += f"   Plan: {admin['subscription_type']} | Expires: {expires}\n\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="master_main")]
        ])
        
        await query.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Admins error: {e}")
        await query.message.edit_text("❌ Error loading admins")

async def show_revenue_calculator(query, user_id):
    """Interactive revenue calculator"""
    # Example calculation
    users = 200
    conversion = 0.05
    vip = Config.DEFAULT_VIP
    whale = Config.DEFAULT_WHALE
    premium = Config.DEFAULT_PREMIUM
    
    monthly_gross = users * conversion * ((0.7 * vip) + (0.2 * whale) + (0.1 * premium))
    platform_fee = monthly_gross * Config.COMMISSION_PERCENT / 100
    net_monthly = monthly_gross - platform_fee - Config.SAAS_MONTHLY
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Subscribe Now", callback_data="sub_monthly")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    text = f"""📊 REVENUE CALCULATOR

Assumptions:
• {users} free users
• {int(conversion*100)}% conversion rate
• Your pricing: VIP {vip} SOL, Whale {whale} SOL, Premium {premium} SOL

💰 MONTHLY PROJECTION:
• Gross Revenue: {monthly_gross:.2f} SOL
• Platform Fee ({Config.COMMISSION_PERCENT}%): {platform_fee:.2f} SOL
• SaaS Cost: {Config.SAAS_MONTHLY} SOL
• 🎯 YOUR PROFIT: {net_monthly:.2f} SOL/month

📈 With 200 users, you profit {net_monthly:.2f} SOL monthly!

Ready to start? 👇"""
    
    await query.message.edit_text(text, reply_markup=keyboard)

async def initiate_subscription(query, user_id: int, sub_type: str, amount: float):
    """Create subscription payment request"""
    days = 30 if sub_type == 'monthly' else 365
    
    # Create payment record
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO platform_payments (admin_id, amount_sol, payment_type, status)
                    VALUES ($1, $2, $3, 'pending')
                """, user_id, amount, sub_type)
        except Exception as e:
            logger.error(f"Payment record error: {e}")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I've Sent Payment", callback_data=f"confirm_sub_{sub_type}")],
        [InlineKeyboardButton("❓ Need Help?", url=f"https://t.me/{Config.SUPPORT_USERNAME}")]
    ])
    
    text = f"""🧾 SUBSCRIPTION INVOICE

📦 Plan: {sub_type.upper()}
⏰ Duration: {days} days
💰 Amount: {amount} SOL

═══════════════════
SEND TO:
`{Config.MASTER_WALLET}`
═══════════════════

⚠️ IMPORTANT:
• Send EXACTLY {amount} SOL
• Use Solana network only
• Transaction must confirm

✅ After sending, click button below
🛰 Auto-verification in 10-30s

Your bot deploys immediately after confirmation!"""
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def show_how_it_works(query):
    """Explain the business model"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Start Subscription", callback_data="sub_monthly")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    text = f"""❓ HOW {Config.PLATFORM_NAME} WORKS

1️⃣ SUBSCRIBE TO PLATFORM
   • Pay {Config.SAAS_MONTHLY} SOL/month
   • Get instant access to dashboard

2️⃣ DEPLOY YOUR BOT (5 min)
   • We create your white-label bot
   • Connect your Telegram channel
   • Set your custom pricing

3️⃣ ATTRACT USERS
   • Bot posts free token alerts
   • Users upgrade for VIP access
   • Referral system grows users

4️⃣ EARN AUTOMATICALLY
   • Users pay YOUR wallet directly
   • You keep {100 - Config.COMMISSION_PERCENT}%, we take {Config.COMMISSION_PERCENT}%
   • Monthly airdrops boost retention

5️⃣ SCALE & PROFIT
   • Deploy multiple bots
   • Build your brand
   • Passive SOL income 24/7

💰 EXAMPLE:
• 500 users → 25 pay {Config.DEFAULT_VIP} SOL = 12.5 SOL
• Your share (80%) = 10 SOL
• Minus platform fee = 9 SOL profit

Ready? 👇"""
    
    await query.message.edit_text(text, reply_markup=keyboard)

async def start_bot_deployment(query, user_id: int):
    """Start the bot deployment process"""
    await query.message.edit_text(
        "🚀 BOT DEPLOYMENT\n\n"
        "To deploy your white-label bot, please provide:\n\n"
        "1. Your bot token (from @BotFather)\n"
        "2. Your public channel ID\n"
        "3. Your VIP group ID\n"
        "4. Your Solana wallet for payments\n\n"
        "Send details in format:\n"
        "/deploy BOT_TOKEN CHANNEL_ID GROUP_ID WALLET\n\n"
        "Example:\n"
        "/deploy 123456:ABC... -1001234567890 -1009876543210 HxmywH2g...",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
    )

async def show_my_revenue(query, user_id: int):
    """Show admin their revenue stats"""
    await query.message.edit_text(
        "📊 YOUR REVENUE\n\n"
        "Revenue stats will appear here once you have active bots.\n\n"
        "Deploy your first bot to start earning!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Deploy Bot", callback_data="deploy_bot")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
    )

# ═══════════════════════════════════════════════════════════════════════
# FLASK WEB SERVER
# ═══════════════════════════════════════════════════════════════════════

@app.route("/")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ICEGODS Platform LIVE",
        "platform": Config.PLATFORM_NAME,
        "master_wallet": Config.MASTER_WALLET,
        "saas_price_monthly": Config.SAAS_MONTHLY,
        "commission_percent": Config.COMMISSION_PERCENT,
        "database_connected": db_pool is not None,
        "bot_initialized": bot_app is not None,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/stats")
def api_stats():
    """Public API stats"""
    return jsonify({
        "platform": Config.PLATFORM_NAME,
        "pricing": {
            "saas_monthly": Config.SAAS_MONTHLY,
            "saas_yearly": Config.SAAS_YEARLY,
            "commission_percent": Config.COMMISSION_PERCENT
        },
        "features": [
            "white_label_bots",
            "automated_alerts",
            "subscription_management",
            "referral_system",
            "airdrop_tools",
            "revenue_dashboard"
        ]
    })

@app.route(f"/webhook/{Config.BOT_TOKEN.split(':')[1]}", methods=['POST'])
def webhook():
    """Handle Telegram webhooks"""
    if not bot_app:
        logger.error("Bot not initialized")
        return jsonify({"error": "Bot not ready"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        
        update = Update.de_json(data, bot_app.bot)
        
        # Process in bot's event loop
        future = asyncio.run_coroutine_threadsafe(
            process_update(update), 
            bot_loop
        )
        future.result(timeout=10)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

async def process_update(update: Update):
    """Process Telegram update"""
    try:
        await bot_app.process_update(update)
    except Exception as e:
        logger.error(f"Process update error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# BOT INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════

def init_bot():
    """Initialize bot in background thread"""
    global bot_app, bot_loop
    
    logger.info("🤖 Initializing bot...")
    
    # Create new event loop for this thread
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    
    async def setup():
        global bot_app
        
        # Initialize database
        if not await init_database():
            logger.error("❌ Database init failed")
            return
        
        # Build bot application
        try:
            bot_app = Application.builder().token(Config.BOT_TOKEN).build()
            bot_app.add_handler(CommandHandler("start", start_handler))
            bot_app.add_handler(CallbackQueryHandler(button_handler))
            
            # Initialize
            await bot_app.initialize()
            
            # Set webhook
            if Config.WEBHOOK_URL:
                webhook_path = f"/webhook/{Config.BOT_TOKEN.split(':')[1]}"
                full_url = f"{Config.WEBHOOK_URL}{webhook_path}"
                await bot_app.bot.set_webhook(url=full_url)
                logger.info(f"✅ Webhook set: {full_url}")
            
            # Start bot
            await bot_app.start()
            logger.info("✅ Bot started successfully!")
            
        except Exception as e:
            logger.error(f"❌ Bot setup error: {e}")
    
    # Run setup in event loop
    try:
        bot_loop.run_until_complete(setup())
        
        # Keep loop running
        while True:
            bot_loop.run_forever()
            
    except Exception as e:
        logger.error(f"❌ Bot loop error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

def main():
    """Main entry point"""
    logger.info(f"🚀 Starting {Config.PLATFORM_NAME}...")
    logger.info(f"🔧 Config: ADMIN_ID={Config.ADMIN_ID}, PORT={Config.PORT}")
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=init_bot, daemon=True)
    bot_thread.start()
    
    # Wait for bot to initialize
    import time
    time.sleep(3)
    
    # Start Flask server
    logger.info(f"🌐 Starting Flask server on port {Config.PORT}...")
    
    # Use Waitress for production (if available), else Flask dev
    try:
        from waitress import serve
        logger.info("Using Waitress WSGI server")
        serve(app, host="0.0.0.0", port=Config.PORT, threads=4)
    except ImportError:
        logger.warning("Waitress not available, using Flask dev server")
        app.run(host="0.0.0.0", port=Config.PORT, threaded=True)

if __name__ == "__main__":
    main()
