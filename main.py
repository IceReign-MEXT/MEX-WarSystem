#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS BOT PLATFORM - SaaS Revenue System
Master Bot: Manages client subscriptions, white-label deployments, revenue sharing
═══════════════════════════════════════════════════════════════════════════
"""

import os
import asyncio
import logging
import aiohttp
import random
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify, render_template_string
import asyncpg
from functools import wraps

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

class Config:
    """Centralized configuration"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    BOT_USERNAME = os.getenv("BOT_USERNAME", "ICEMEXWarSystem_Bot")
    PLATFORM_NAME = os.getenv("PLATFORM_NAME", "ICEGODS Platform")
    PLATFORM_URL = os.getenv("PLATFORM_URL", "")
    SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@MexRobert")
    MASTER_WALLET = os.getenv("MASTER_WALLET", "")
    DATABASE_URL = os.getenv("DATABASE_URL")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", "8080"))
    HELIUS_KEY = os.getenv("HELIUS_API_KEY")
    
    # SaaS Pricing
    SAAS_MONTHLY = float(os.getenv("SAAS_MONTHLY_PRICE", "5.0"))
    SAAS_YEARLY = float(os.getenv("SAAS_YEARLY_PRICE", "50.0"))
    COMMISSION_PERCENT = float(os.getenv("SAAS_COMMISSION_PERCENT", "20"))
    
    # Client Pricing Defaults
    DEFAULT_VIP = float(os.getenv("DEFAULT_VIP_PRICE", "0.5"))
    DEFAULT_WHALE = float(os.getenv("DEFAULT_WHALE_PRICE", "1.0"))
    DEFAULT_PREMIUM = float(os.getenv("DEFAULT_PREMIUM_PRICE", "2.5"))
    
    # Features
    SIGNAL_INTERVAL = int(os.getenv("SIGNAL_INTERVAL_MINUTES", "10"))
    REFERRAL_REWARD_DAYS = int(os.getenv("REFERRAL_REWARD_DAYS", "3"))
    REFERRALS_NEEDED = int(os.getenv("REFERRALS_NEEDED", "3"))

app = Flask(__name__)
db_pool = None
application = None

# ═══════════════════════════════════════════════════════════════════════
# DATABASE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

class DatabaseManager:
    """Handle all database operations"""
    
    @staticmethod
    async def init():
        global db_pool
        try:
            db_pool = await asyncpg.create_pool(
                Config.DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            
            async with db_pool.acquire() as conn:
                # Master admin table
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
                
                # End users (across all client bots)
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
                
                # Payments (platform fees from admins)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS platform_payments (
                        id SERIAL PRIMARY KEY,
                        admin_id BIGINT,
                        amount_sol DECIMAL(10,4),
                        payment_type TEXT, -- 'monthly', 'yearly', 'commission'
                        status TEXT DEFAULT 'pending',
                        tx_hash TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        confirmed_at TIMESTAMP
                    )
                """)
                
                # Client bot payments (end user payments)
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
                
                # Revenue calculations
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
                
                # Airdrops for end users
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS airdrops (
                        id SERIAL PRIMARY KEY,
                        client_bot_id INT,
                        user_telegram_id BIGINT,
                        amount DECIMAL(20,8),
                        tx_hash TEXT,
                        plan_type TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT NOW(),
                        sent_at TIMESTAMP
                    )
                """)
                
                # Token signals/alerts
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
                
            logger.info("✅ Database initialized with SaaS schema")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    @staticmethod
    async def get_admin(admin_id: int) -> Optional[Dict]:
        if not db_pool:
            return None
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM platform_admins WHERE admin_id = $1", admin_id
            )
            return dict(row) if row else None
    
    @staticmethod
    async def create_admin(admin_id: int, username: str, sub_type: str, expires: datetime):
        if not db_pool:
            return False
        async with db_pool.acquire() as conn:
            api_key = f"ice_{admin_id}_{int(datetime.now().timestamp())}"
            await conn.execute("""
                INSERT INTO platform_admins (admin_id, username, subscription_type, subscription_expires, api_key)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (admin_id) DO UPDATE SET
                    subscription_type = $3,
                    subscription_expires = $4,
                    status = 'active'
            """, admin_id, username, sub_type, expires, api_key)
            return True

# ═══════════════════════════════════════════════════════════════════════
# REVENUE CALCULATOR
# ═══════════════════════════════════════════════════════════════════════

class RevenueCalculator:
    """Calculate and project revenues"""
    
    @staticmethod
    async def get_admin_revenue_projection(admin_id: int) -> Dict:
        """Project revenue for an admin based on their setup"""
        if not db_pool:
            return {}
        
        async with db_pool.acquire() as conn:
            # Get client bots
            bots = await conn.fetch(
                "SELECT * FROM client_bots WHERE admin_id = $1 AND status = 'active'",
                admin_id
            )
            
            total_projected = 0
            bot_projections = []
            
            for bot in bots:
                # Calculate based on pricing and typical conversion rates
                vip_price = bot['vip_price']
                whale_price = bot['whale_price']
                premium_price = bot['premium_price']
                
                # Conservative estimates: 100 users, 5% conversion
                est_users = 100
                conversion_rate = 0.05
                
                monthly_vip = est_users * conversion_rate * 0.7 * vip_price
                monthly_whale = est_users * conversion_rate * 0.2 * whale_price
                monthly_premium = est_users * conversion_rate * 0.1 * premium_price
                
                bot_monthly = monthly_vip + monthly_whale + monthly_premium
                bot_yearly = bot_monthly * 12
                
                total_projected += bot_monthly
                
                bot_projections.append({
                    'bot_id': bot['bot_id'],
                    'username': bot['bot_username'],
                    'monthly_projection': round(bot_monthly, 2),
                    'yearly_projection': round(bot_yearly, 2),
                    'pricing': {
                        'vip': vip_price,
                        'whale': whale_price,
                        'premium': premium_price
                    }
                })
            
            platform_fee_percent = Config.COMMISSION_PERCENT
            net_monthly = total_projected * (1 - platform_fee_percent / 100)
            
            return {
                'admin_id': admin_id,
                'total_bots': len(bots),
                'gross_monthly': round(total_projected, 2),
                'platform_fee_percent': platform_fee_percent,
                'platform_fee_monthly': round(total_projected * platform_fee_percent / 100, 2),
                'net_monthly': round(net_monthly, 2),
                'net_yearly': round(net_monthly * 12, 2),
                'bot_details': bot_projections
            }

# ═══════════════════════════════════════════════════════════════════════
# TELEGRAM HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main entry point - detects if admin or end user"""
    user = update.effective_user
    
    # Check if this is the master admin
    if user.id == Config.ADMIN_ID:
        await show_master_dashboard(update, context)
        return
    
    # Check if registered admin
    admin = await DatabaseManager.get_admin(user.id)
    
    if admin and admin.get('subscription_expires') and admin['subscription_expires'] > datetime.now():
        await show_admin_dashboard(update, context, admin)
    else:
        await show_subscription_offer(update, context)

async def show_master_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show master admin (you) the platform overview"""
    
    if not db_pool:
        await update.message.reply_text("❌ Database error")
        return
    
    async with db_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_admins,
                COUNT(*) FILTER (WHERE subscription_expires > NOW()) as active_admins,
                COALESCE(SUM(total_paid_to_platform), 0) as total_revenue,
                COUNT(*) FILTER (WHERE DATE(created_at) = CURRENT_DATE) as new_today
            FROM platform_admins
        """)
        
        client_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_bots,
                COALESCE(SUM(monthly_revenue), 0) as client_revenue
            FROM client_bots
            WHERE status = 'active'
        """)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Revenue Report", callback_data="master_revenue")],
        [InlineKeyboardButton("👥 Manage Admins", callback_data="master_admins")],
        [InlineKeyboardButton("🤖 Client Bots", callback_data="master_bots")],
        [InlineKeyboardButton("💰 Withdraw Earnings", callback_data="master_withdraw")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="master_broadcast")]
    ])
    
    text = f"""👑 MASTER DASHBOARD - {Config.PLATFORM_NAME}

📊 PLATFORM STATS:
• Total Admins: {stats['total_admins']}
• Active Subs: {stats['active_admins']}
• Client Bots: {client_stats['total_bots']}
• New Today: {stats['new_today']}

💰 REVENUE:
• Your Total: {stats['total_revenue']:.2f} SOL
• Client Volume: {client_stats['client_revenue']:.2f} SOL
• Platform Fees: {stats['total_revenue'] * Config.COMMISSION_PERCENT / 100:.2f} SOL

🎯 QUICK ACTIONS:"""
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def show_subscription_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription offer to potential admins"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Monthly - 5 SOL/month", callback_data="sub_monthly")],
        [InlineKeyboardButton("👑 Yearly - 50 SOL/year (Save 10)", callback_data="sub_yearly")],
        [InlineKeyboardButton("📊 Revenue Calculator", callback_data="calc_revenue")],
        [InlineKeyboardButton("❓ How It Works", callback_data="how_it_works")],
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{Config.SUPPORT_USERNAME}")]
    ])
    
    text = f"""🚀 {Config.PLATFORM_NAME}

Deploy your own token alert bot & earn SOL!

💎 WHAT YOU GET:
• White-label Telegram bot
• Automated token alerts (DexScreener)
• Subscription management
• Referral system
• Airdrop distribution tools
• Revenue dashboard

💰 YOUR EARNINGS:
• Keep 80% of all user payments
• Set your own prices
• Monthly airdrops to your users
• 24/7 automated income

📊 PRICING:
• Monthly: {Config.SAAS_MONTHLY} SOL
• Yearly: {Config.SAAS_YEARLY} SOL (Best Value)

⚡ Limited spots available!

Tap below to start 👇"""
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def show_admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, admin: Dict):
    """Show registered admin their dashboard"""
    
    days_left = (admin['subscription_expires'] - datetime.now()).days
    
    # Get revenue projection
    projection = await RevenueCalculator.get_admin_revenue_projection(admin['admin_id'])
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Deploy New Bot", callback_data="deploy_bot")],
        [InlineKeyboardButton("📊 My Revenue", callback_data="my_revenue")],
        [InlineKeyboardButton("⚙️ Manage Bots", callback_data="my_bots")],
        [InlineKeyboardButton("🎁 Airdrop Tokens", callback_data="manage_airdrops")],
        [InlineKeyboardButton("💰 Withdraw", callback_data="withdraw_earnings")],
        [InlineKeyboardButton("🔄 Renew Subscription", callback_data="renew_sub")]
    ])
    
    text = f"""⚡ ADMIN DASHBOARD

👤 Status: {admin['subscription_type'].upper()}
⏰ Expires: {days_left} days
💰 Total Earned: {admin['total_earned']:.2f} SOL

📊 PROJECTIONS:
• Monthly Potential: {projection.get('gross_monthly', 0):.2f} SOL
• Your Share (80%): {projection.get('net_monthly', 0):.2f} SOL
• Active Bots: {projection.get('total_bots', 0)}

🎯 QUICK ACTIONS:"""
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Master admin buttons
    if user_id == Config.ADMIN_ID:
        if query.data == "master_revenue":
            await show_master_revenue(query)
        elif query.data == "master_admins":
            await show_all_admins(query)
        elif query.data == "calc_revenue":
            await show_revenue_calculator(query, user_id)
        return
    
    # Regular admin buttons
    if query.data == "calc_revenue":
        await show_revenue_calculator(query, user_id)
    elif query.data == "sub_monthly":
        await initiate_subscription(query, user_id, 'monthly')
    elif query.data == "sub_yearly":
        await initiate_subscription(query, user_id, 'yearly')
    elif query.data == "deploy_bot":
        await start_bot_deployment(query, user_id)
    elif query.data == "my_revenue":
        await show_my_revenue(query, user_id)
    elif query.data == "how_it_works":
        await show_how_it_works(query)

async def show_revenue_calculator(query, user_id):
    """Interactive revenue calculator"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Set Pricing & Calculate", callback_data="set_calc_pricing")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    # Default calculation
    users = 200
    conversion = 0.05  # 5%
    vip_price = Config.DEFAULT_VIP
    whale_price = Config.DEFAULT_WHALE
    premium_price = Config.DEFAULT_PREMIUM
    
    monthly = users * conversion * ((0.7 * vip_price) + (0.2 * whale_price) + (0.1 * premium_price))
    yearly = monthly * 12
    net_monthly = monthly * 0.8  # After 20% platform fee
    
    text = f"""📊 REVENUE CALCULATOR

Assumptions:
• {users} free users in your channel
• {int(conversion*100)}% buy subscription
• Pricing: VIP {vip_price} SOL, Whale {whale_price} SOL, Premium {premium_price} SOL

💰 PROJECTIONS:
• Monthly Gross: {monthly:.2f} SOL
• Platform Fee (20%): {monthly * 0.2:.2f} SOL
• YOUR EARNINGS: {net_monthly:.2f} SOL/month
• Yearly: {net_monthly * 12:.2f} SOL

🎯 With just 200 users, you earn {net_monthly:.2f} SOL monthly!

Customize your pricing below:"""
    
    await query.message.edit_text(text, reply_markup=keyboard)

async def initiate_subscription(query, user_id: int, sub_type: str):
    """Start subscription payment process"""
    
    amount = Config.SAAS_MONTHLY if sub_type == 'monthly' else Config.SAAS_YEARLY
    days = 30 if sub_type == 'monthly' else 365
    
    # Create payment record
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO platform_payments (admin_id, amount_sol, payment_type, status)
                VALUES ($1, $2, $3, 'pending')
            """, user_id, amount, sub_type)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I've Sent Payment", callback_data=f"confirm_sub_{sub_type}")],
        [InlineKeyboardButton("❓ Need Help?", url=f"https://t.me/{Config.SUPPORT_USERNAME}")]
    ])
    
    text = f"""🧾 SUBSCRIPTION INVOICE

📦 Plan: {sub_type.upper()}
⏰ Duration: {days} days
💰 Amount: {amount} SOL

═══════════════════
SEND TO: `{Config.MASTER_WALLET}`
═══════════════════

⚠️ Send EXACTLY {amount} SOL
✅ After sending, click button below
🛰 Auto-verification in 10-30s

Your access activates immediately after confirmation!"""
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def show_how_it_works(query):
    """Explain the SaaS business model"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Start Subscription", callback_data="sub_monthly")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    text = f"""❓ HOW {Config.PLATFORM_NAME} WORKS

1️⃣ SUBSCRIBE TO PLATFORM
   • Pay {Config.SAAS_MONTHLY} SOL/month or {Config.SAAS_YEARLY} SOL/year
   • Get access to bot deployment dashboard

2️⃣ DEPLOY YOUR BOT (5 minutes)
   • We create your white-label bot
   • Connect your Telegram channel/group
   • Set your custom pricing

3️⃣ ATTRACT USERS
   • Users join your channel
   • Bot posts free token alerts
   • Some upgrade to VIP for early access

4️⃣ EARN AUTOMATICALLY
   • Users pay YOUR wallet directly
   • You keep 80%, we take 20%
   • Monthly airdrops boost retention

5️⃣ SCALE & PROFIT
   • Deploy multiple bots
   • Build your brand
   • Passive SOL income 24/7

💰 REAL EXAMPLE:
• 500 users → 25 pay {Config.DEFAULT_VIP} SOL = 12.5 SOL
• Your share (80%) = 10 SOL/month
• Minus platform fee ({Config.SAAS_MONTHLY} SOL) = 9 SOL profit

Ready to start? 👇"""
    
    await query.message.edit_text(text, reply_markup=keyboard)

# ═══════════════════════════════════════════════════════════════════════
# TOKEN ALERT SYSTEM (For all client bots)
# ═══════════════════════════════════════════════════════════════════════

class AlertDistributor:
    """Distribute token alerts to all active client bots"""
    
    @staticmethod
    async def fetch_and_distribute():
        """Fetch new tokens and send to all client channels"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.dexscreener.com/token-profiles/latest/v1"
                
                async with session.get(url, timeout=15) as resp:
                    if resp.status != 200:
                        return
                    
                    data = await resp.json()
                    if not data or not isinstance(data, list):
                        return
                    
                    # Get first new token
                    for profile in data[:3]:  # Top 3 new tokens
                        token_addr = profile.get('tokenAddress')
                        if not token_addr:
                            continue
                        
                        # Check if already posted
                        if db_pool:
                            async with db_pool.acquire() as conn:
                                existing = await conn.fetchval(
                                    "SELECT 1 FROM token_signals WHERE token_address = $1",
                                    token_addr
                                )
                                if existing:
                                    continue
                        
                        # Get detailed data
                        detail_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_addr}"
                        
                        async with session.get(detail_url, timeout=15) as dresp:
                            if dresp.status != 200:
                                continue
                            
                            details = await dresp.json()
                            if not details.get('pairs'):
                                continue
                            
                            pair = details['pairs'][0]
                            base = pair.get('baseToken', {})
                            
                            name = base.get('name', 'Unknown')[:30]
                            symbol = base.get('symbol', '???')[:10]
                            price = float(pair.get('priceUsd', 0))
                            liq = pair.get('liquidity', {}).get('usd', 0)
                            vol = pair.get('volume', {}).get('h24', 0)
                            
                            # Clean
                            name = name.replace('*', '').replace('_', '')
                            symbol = symbol.replace('*', '').replace('_', '')
                            
                            # Save to DB
                            if db_pool:
                                async with db_pool.acquire() as conn:
                                    await conn.execute("""
                                        INSERT INTO token_signals 
                                        (token_address, name, symbol, price_usd, liquidity_usd, volume_24h)
                                        VALUES ($1, $2, $3, $4, $5, $6)
                                    """, token_addr, name, symbol, price, liq, vol)
                            
                            # Distribute to all active client bots
                            await AlertDistributor.distribute_to_clients(
                                name, symbol, price, liq, vol, pair.get('url', ''), token_addr
                            )
                            
        except Exception as e:
            logger.error(f"Alert distribution error: {e}")
    
    @staticmethod
    async def distribute_to_clients(name, symbol, price, liq, vol, chart_url, token_addr):
        """Send alert to all client public channels"""
        if not db_pool:
            return
        
        async with db_pool.acquire() as conn:
            clients = await conn.fetch(
                "SELECT * FROM client_bots WHERE status = 'active'"
            )
        
        for client in clients:
            try:
                message = f"""🚀 NEW TOKEN ALERT

💎 {name} (${symbol})
💵 Price: ${price:.8f}
💧 Liquidity: ${liq:,.0f}
📊 24h Volume: ${vol:,.0f}

⏰ Just launched on Solana

⚠️ DYOR - Not financial advice

💎 Get EARLY access: @{client['bot_username']}"""
                
                # Send to client's public channel
                await application.bot.send_message(
                    client['public_channel_id'],
                    message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔥 Get VIP Alerts", url=f"https://t.me/{client['bot_username']}")]
                    ])
                )
                
                # Update stats
                async with db_pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE client_bots SET total_users = total_users + 1 WHERE bot_id = $1",
                        client['bot_id']
                    )
                
            except Exception as e:
                logger.error(f"Failed to send to client {client['bot_id']}: {e}")

async def alert_worker():
    """Background worker to distribute alerts"""
    while True:
        await AlertDistributor.fetch_and_distribute()
        await asyncio.sleep(Config.SIGNAL_INTERVAL * 60)

# ═══════════════════════════════════════════════════════════════════════
# FLASK WEB SERVER
# ═══════════════════════════════════════════════════════════════════════

@app.route("/")
def health_check():
    return jsonify({
        "status": "ICEGODS Platform Active",
        "platform": Config.PLATFORM_NAME,
        "master_wallet": Config.MASTER_WALLET,
        "saas_price_monthly": Config.SAAS_MONTHLY,
        "commission": Config.COMMISSION_PERCENT,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/stats")
def api_stats():
    """Public API for stats"""
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

@app.route(f"/webhook/{Config.BOT_TOKEN.split(':')[1] if Config.BOT_TOKEN else 'invalid'}", methods=['POST'])
def webhook():
    """Handle Telegram webhooks"""
    if not application:
        return jsonify({"error": "Bot not ready"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        
        update = Update.de_json(data, application.bot)
        asyncio.create_task(application.process_update(update))
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════
# MAIN INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════

def main():
    global application
    
    logger.info(f"🚀 Starting {Config.PLATFORM_NAME}...")
    
    # Initialize database
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    if not loop.run_until_complete(DatabaseManager.init()):
        logger.error("Database failed to initialize")
        return
    
    # Build application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start alert worker in background
    loop.create_task(alert_worker())
    
    # Initialize bot
    application.initialize()
    
    # Set webhook
    if Config.WEBHOOK_URL:
        webhook_path = f"/webhook/{Config.BOT_TOKEN.split(':')[1]}"
        full_url = f"{Config.WEBHOOK_URL}{webhook_path}"
        application.bot.set_webhook(url=full_url)
        logger.info(f"✅ Webhook set: {full_url}")
    
    application.start()
    logger.info("✅ Bot is running!")
    
    # Run Flask server
    app.run(host="0.0.0.0", port=Config.PORT, threaded=True)

if __name__ == "__main__":
    main()
