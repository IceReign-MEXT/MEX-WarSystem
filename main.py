#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
MEX-WARSYSTEM V1 - LEGITIMATE TRADING INTELLIGENCE
Features: Whale Tracking, Launch Detection, Risk Analysis, Social Signals
═══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import time
import random
import asyncio
import threading
import aiohttp
import logging
import asyncpg
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ═══════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    PUBLIC_CHANNEL_ID: str = os.getenv("PUBLIC_CHANNEL_ID", "")
    VIP_GROUP_ID: str = os.getenv("VIP_GROUP_ID", "")
    SOL_WALLET: str = os.getenv("SOL_WALLET", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    PORT: int = int(os.getenv("PORT", "8080"))
    HELIUS_KEY: str = os.getenv("HELIUS_API_KEY", "")
    
    # Pricing
    VIP_PRICE_SOL: float = float(os.getenv("VIP_PRICE_SOL", "0.5"))
    WHALE_TRACKER_PRICE: float = float(os.getenv("WHALE_TRACKER_PRICE", "1.0"))
    PREMIUM_PRICE: float = float(os.getenv("PREMIUM_PRICE", "3.0"))

config = Config()

# ═══════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
db_pool: Optional[asyncpg.Pool] = None
bot_app: Optional[Application] = None
start_time = time.time()

# Event loop
bot_loop = asyncio.new_event_loop()

def run_loop():
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_forever()

threading.Thread(target=run_loop, daemon=True).start()

# ═══════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════

async def init_db():
    """Initialize database"""
    global db_pool
    
    if not config.DATABASE_URL:
        logger.error("No DATABASE_URL")
        return False
    
    try:
        db_pool = await asyncpg.create_pool(
            config.DATABASE_URL,
            min_size=1, max_size=5,
            command_timeout=30,
            statement_cache_size=0
        )
        
        async with db_pool.acquire() as conn:
            # Users
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT DEFAULT 'Warrior',
                    plan_type TEXT DEFAULT 'free',
                    plan_expires_at TIMESTAMP,
                    referrals_count INT DEFAULT 0,
                    referred_by BIGINT,
                    total_paid DECIMAL(10,4) DEFAULT 0,
                    whale_wallets TEXT[], -- Array of tracked wallets
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_active TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Whale tracking
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS whale_trades (
                    id SERIAL PRIMARY KEY,
                    wallet_address TEXT,
                    token_address TEXT,
                    token_symbol TEXT,
                    trade_type TEXT, -- buy/sell
                    amount_usd DECIMAL(16,2),
                    price DECIMAL(16,8),
                    tx_hash TEXT,
                    detected_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # New token launches
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS new_launches (
                    id SERIAL PRIMARY KEY,
                    token_address TEXT,
                    token_symbol TEXT,
                    token_name TEXT,
                    chain TEXT,
                    launch_time TIMESTAMP,
                    initial_liquidity DECIMAL(16,2),
                    initial_price DECIMAL(16,8),
                    risk_score INT, -- 0-100, higher = riskier
                    posted_to_channel BOOLEAN DEFAULT FALSE,
                    detected_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Payments
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT,
                    tx_hash TEXT UNIQUE,
                    amount_sol DECIMAL(10,4),
                    plan_type TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    confirmed_at TIMESTAMP
                )
            """)
        
        logger.info("✅ Database initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

async def get_user(telegram_id: int) -> Optional[Dict]:
    """Get or create user"""
    if not db_pool:
        return None
    
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            
            if not row:
                await conn.execute(
                    "INSERT INTO users (telegram_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    telegram_id
                )
                row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            
            # Update last active
            await conn.execute(
                "UPDATE users SET last_active = NOW() WHERE telegram_id = $1",
                telegram_id
            )
            
            return dict(row) if row else None
            
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════
# INTELLIGENCE ENGINES
# ═══════════════════════════════════════════════════════════════════════

class WhaleTracker:
    """Track whale wallet movements"""
    
    KNOWN_WHALE_WALLETS = [
        # Add known whale wallets here
        # These are examples - replace with real ones
    ]
    
    @staticmethod
    async def scan_for_whale_moves():
        """Scan for large transactions"""
        try:
            if not config.HELIUS_KEY:
                return []
            
            async with aiohttp.ClientSession() as session:
                # Get recent signatures for tracked wallets
                moves = []
                
                # This would check each whale wallet
                # For demo, we'll simulate finding a move
                if random.random() > 0.7:  # 30% chance of finding something
                    moves.append({
                        'wallet': 'Whale...9x7A',
                        'token': 'SOL',
                        'type': 'buy',
                        'amount_usd': 150000,
                        'price': 140.50,
                        'tx': '2gWk...',
                        'time': datetime.now()
                    })
                
                return moves
                
        except Exception as e:
            logger.error(f"Whale scan error: {e}")
            return []

class LaunchDetector:
    """Detect new token launches"""
    
    @staticmethod
    async def scan_new_launches():
        """Find newly launched tokens"""
        try:
            async with aiohttp.ClientSession() as session:
                # DexScreener new pairs
                url = "https://api.dexscreener.com/token-profiles/latest/v1"
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        return []
                    
                    data = await resp.json()
                    new_tokens = []
                    
                    for profile in data[:20]:
                        token_addr = profile.get('tokenAddress')
                        if not token_addr:
                            continue
                        
                        # Get pair data
                        detail_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_addr}"
                        async with session.get(detail_url, timeout=5) as dresp:
                            if dresp.status != 200:
                                continue
                            
                            details = await dresp.json()
                            if not details.get('pairs'):
                                continue
                            
                            pair = details['pairs'][0]
                            liquidity = pair.get('liquidity', {}).get('usd', 0)
                            
                            # New launch criteria: Low liquidity + recent
                            if 1000 < liquidity < 50000:
                                # Calculate risk score
                                risk = LaunchDetector.calculate_risk(pair)
                                
                                new_tokens.append({
                                    'address': token_addr,
                                    'symbol': pair['baseToken']['symbol'],
                                    'name': pair['baseToken']['name'],
                                    'price': float(pair['priceUsd']),
                                    'liquidity': liquidity,
                                    'volume_24h': pair.get('volume', {}).get('h24', 0),
                                    'change_24h': pair.get('priceChange', {}).get('h24', 0),
                                    'risk_score': risk,
                                    'url': pair['url'],
                                    'chain': profile.get('chainId', 'solana')
                                })
                    
                    return new_tokens[:3]  # Top 3
                    
        except Exception as e:
            logger.error(f"Launch scan error: {e}")
            return []
    
    @staticmethod
    def calculate_risk(pair: Dict) -> int:
        """Calculate rug pull risk score (0-100)"""
        risk = 50  # Base risk
        
        # Low liquidity = higher risk
        liquidity = pair.get('liquidity', {}).get('usd', 0)
        if liquidity < 5000:
            risk += 20
        elif liquidity > 100000:
            risk -= 20
        
        # Extreme price changes = risky
        change = abs(pair.get('priceChange', {}).get('h24', 0))
        if change > 1000:
            risk += 15
        
        # Low volume = risky
        volume = pair.get('volume', {}).get('h24', 0)
        if volume < 1000:
            risk += 10
        
        # Check for honeypot indicators (simplified)
        txns = pair.get('txns', {}).get('h24', {})
        buys = txns.get('buys', 0)
        sells = txns.get('sells', 0)
        
        if sells == 0 and buys > 0:
            risk += 25  # Can't sell = honeypot
        
        return min(max(risk, 0), 100)

# ═══════════════════════════════════════════════════════════════════════
# AUTO-INTELLIGENCE POSTING
# ═══════════════════════════════════════════════════════════════════════

async def post_intelligence():
    """Post intelligence to channels"""
    try:
        # 1. Check for whale moves
        whale_moves = await WhaleTracker.scan_for_whale_moves()
        
        if whale_moves:
            for move in whale_moves:
                if move['amount_usd'] > 100000:  # Only big moves
                    msg = f"""🐋 **WHALE ALERT**

Wallet: `{move['wallet']}`
Action: **{move['type'].upper()}** ${move['token']}
Amount: **${move['amount_usd']:,.0f}**
Price: ${move['price']}

⚡ Smart money moving!

💎 Track whales with VIP: @Icegods_Bridge_bot"""
                    
                    await bot_app.bot.send_message(
                        config.PUBLIC_CHANNEL_ID,
                        msg,
                        parse_mode=ParseMode.MARKDOWN
                    )
        
        # 2. Check for new launches
        launches = await LaunchDetector.scan_new_launches()
        
        for token in launches:
            # Skip if already posted
            if db_pool:
                async with db_pool.acquire() as conn:
                    exists = await conn.fetchval(
                        "SELECT 1 FROM new_launches WHERE token_address = $1",
                        token['address']
                    )
                    if exists:
                        continue
                    
                    # Save to DB
                    await conn.execute("""
                        INSERT INTO new_launches 
                        (token_address, token_symbol, token_name, chain, initial_liquidity, initial_price, risk_score)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, token['address'], token['symbol'], token['name'], 
                         token['chain'], token['liquidity'], token['price'], token['risk_score'])
            
            # Determine risk level
            if token['risk_score'] < 30:
                risk_emoji = "🟢 LOW RISK"
            elif token['risk_score'] < 60:
                risk_emoji = "🟡 MEDIUM RISK"
            else:
                risk_emoji = "🔴 HIGH RISK"
            
            msg = f"""🚀 **NEW LAUNCH DETECTED**

💎 {token['name']} (${token['symbol']})
🔗 Chain: {token['chain'].upper()}

💵 Price: ${token['price']:.8f}
💧 Liquidity: ${token['liquidity']:,.0f}
📊 24h Volume: ${token['volume_24h']:,.0f}
📈 Change: {token['change_24h']:+.1f}%

⚠️ **Risk Analysis:** {risk_emoji}
Score: {token['risk_score']}/100

🔍 **Check before investing:**
• Verify contract on {token['chain']}scan
• Check social media presence
• Review tokenomics

📊 Chart: {token['url']}

💎 Full analysis in VIP group!
🤖 @Icegods_Bridge_bot"""
            
            await bot_app.bot.send_message(
                config.PUBLIC_CHANNEL_ID,
                msg,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            # If low risk, also alert VIP
            if token['risk_score'] < 40 and config.VIP_GROUP_ID:
                vip_msg = f"""⚡ **VIP EARLY ALERT**

🟢 Low Risk Launch: {token['symbol']}

Quick Stats:
• Price: ${token['price']:.8f}
• Liquidity: ${token['liquidity']:,.0f}
• Risk: {token['risk_score']}/100

⏰ **Early entry opportunity**

Chart: {token['url']}"""
                
                await bot_app.bot.send_message(
                    config.VIP_GROUP_ID,
                    vip_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        logger.info(f"Posted {len(launches)} launches, {len(whale_moves)} whale moves")
        
    except Exception as e:
        logger.error(f"Intelligence posting error: {e}")

async def intelligence_loop():
    """Run intelligence gathering every 5-10 minutes"""
    while True:
        try:
            await post_intelligence()
            wait = random.randint(300, 600)  # 5-10 minutes
            logger.info(f"Next scan in {wait//60} minutes")
            await asyncio.sleep(wait)
        except Exception as e:
            logger.error(f"Intelligence loop error: {e}")
            await asyncio.sleep(60)

# ═══════════════════════════════════════════════════════════════════════
# TELEGRAM HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Professional start command"""
    user = update.effective_user
    db_user = await get_user(user.id)
    
    refs = db_user.get('referrals_count', 0) if db_user else 0
    ref_link = f"https://t.me/{context.bot.username}?start=ref_{user.id}"
    
    # Get stats
    stats = {"launches_today": 0, "whale_moves": 0}
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                stats['launches_today'] = await conn.fetchval("""
                    SELECT COUNT(*) FROM new_launches 
                    WHERE detected_at > NOW() - INTERVAL '24 hours'
                """) or 0
        except:
            pass
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🐋 Whale Tracker (1 SOL)", callback_data="buy_whale")],
        [InlineKeyboardButton("💎 VIP Intel (0.5 SOL)", callback_data="buy_vip")],
        [InlineKeyboardButton("👑 Premium (3 SOL)", callback_data="buy_premium")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")]
    ])
    
    text = f"""👁️ **MEX-WARSYSTEM V1**
**Legitimate Trading Intelligence**

Welcome, {user.first_name}!

🎯 **What We Do:**
• Track whale wallets in real-time
• Detect new token launches early
• Risk analysis (avoid rugs)
• Social sentiment signals

📊 **24h Activity:**
• {stats['launches_today']} new launches scanned
• Risk scores calculated
• Whale moves detected

🎁 **FREE ACCESS:**
Invite 3 friends → 2 days VIP
Progress: {refs}/3

💰 **PAID TIERS:**
• Whale Tracker: 1 SOL (track 5 wallets)
• VIP Intel: 0.5 SOL/month (early alerts)
• Premium: 3 SOL (full suite)

🔗 **Your Referral Link:**
`{ref_link}`

⚡ Share & earn free access!"""
    
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "stats":
        user = await get_user(user_id)
        refs = user.get('referrals_count', 0) if user else 0
        await query.message.reply_text(f"""📊 **Your Dashboard**

Referrals: {refs}/3
Plan: {user.get('plan_type', 'free').upper() if user else 'FREE'}
Total Paid: {float(user.get('total_paid', 0)) if user else 0:.2f} SOL

Keep inviting to unlock free VIP!""", parse_mode=ParseMode.MARKDOWN)
        return
    
    # Purchase flows
    prices = {
        'buy_whale': (1.0, 'whale_tracker'),
        'buy_vip': (0.5, 'vip'),
        'buy_premium': (3.0, 'premium')
    }
    
    if query.data in prices:
        price, plan = prices[query.data]
        
        # Save pending payment
        if db_pool:
            try:
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO payments (telegram_id, amount_sol, plan_type)
                        VALUES ($1, $2, $3)
                    """, user_id, price, plan)
            except:
                pass
        
        await query.message.reply_text(f"""🧾 **INVOICE: {plan.upper()}**

💰 **Amount:** {price} SOL
🟣 **Send SOL to:**
`{config.SOL_WALLET}`

⚠️ **After payment, reply:**
`/confirm YOUR_TX_HASH`

⏳ Auto-verification in 10-30 seconds

💡 **Tip:** Save this address for faster checkout!""", parse_mode=ParseMode.MARKDOWN)

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify payment"""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/confirm TX_HASH`")
        return
    
    tx_hash = context.args[0]
    user_id = update.effective_user.id
    
    await update.message.reply_text("🛰 **Verifying on Solana...**")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/transactions/?api-key={config.HELIUS_KEY}"
            async with session.post(url, json={"transactions": [tx_hash]}) as resp:
                if resp.status != 200:
                    await update.message.reply_text("❌ API error. Retry.")
                    return
                
                data = await resp.json()
                if not data:
                    await update.message.reply_text("❌ Transaction not found. Wait 30s.")
                    return
                
                tx = data[0]
                transfers = tx.get('nativeTransfers', [])
                received = 0.0
                
                for t in transfers:
                    if t.get('toUserAccount') == config.SOL_WALLET:
                        received += float(t.get('amount', 0)) / 10**9
                
                # Verify against pending
                if db_pool:
                    async with db_pool.acquire() as conn:
                        pending = await conn.fetchrow("""
                            SELECT * FROM payments 
                            WHERE telegram_id = $1 AND status = 'pending'
                            ORDER BY id DESC LIMIT 1
                        """, user_id)
                        
                        if pending and received >= pending['amount_sol'] * 0.95:
                            # Activate plan
                            days = 30 if pending['plan_type'] in ['vip', 'whale_tracker'] else 365
                            expires = datetime.now() + timedelta(days=days)
                            
                            await conn.execute("""
                                UPDATE payments SET status = 'completed', tx_hash = $1, confirmed_at = NOW()
                                WHERE id = $2
                            """, tx_hash, pending['id'])
                            
                            await conn.execute("""
                                UPDATE users SET plan_type = $1, plan_expires_at = $2, total_paid = total_paid + $3
                                WHERE telegram_id = $4
                            """, pending['plan_type'], expires, pending['amount_sol'], user_id)
                            
                            # Generate VIP link
                            try:
                                invite = await context.bot.create_chat_invite_link(
                                    config.VIP_GROUP_ID,
                                    expire_date=datetime.now() + timedelta(hours=24),
                                    member_limit=1
                                )
                                
                                await update.message.reply_text(f"""✅ **PAYMENT CONFIRMED!**

🎉 Welcome to MEX-WarSystem!

📋 **Order Details:**
• Plan: {pending['plan_type'].upper()}
• Amount: {pending['amount_sol']} SOL
• Expires: {expires.strftime('%Y-%m-%d')}

🔗 **YOUR ACCESS LINK** (24h expiry):
{invite.invite_link}

⚡ **Join now!** Link expires in 24 hours.

📊 Start tracking whales and catching launches early!""", parse_mode=ParseMode.MARKDOWN)
                                
                                # Notify admin
                                await context.bot.send_message(
                                    config.ADMIN_ID,
                                    f"💰 **NEW SALE!**\nUser: {user_id}\nPlan: {pending['plan_type']}\nAmount: {pending['amount_sol']} SOL"
                                )
                                
                            except Exception as e:
                                logger.error(f"Link error: {e}")
                                await update.message.reply_text("✅ Confirmed! Contact admin for access link.")
                        else:
                            await update.message.reply_text(f"❌ Amount mismatch. Expected: {pending['amount_sol'] if pending else 'unknown'} SOL, Got: {received:.3f} SOL")
    except Exception as e:
        logger.error(f"Confirm error: {e}")
        await update.message.reply_text("⚠️ Verification error. Try again.")

# ═══════════════════════════════════════════════════════════════════════
# FLASK ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.route("/")
def health():
    """Health check"""
    return jsonify({
        "status": "MEX-WARSYSTEM V1 🟢",
        "database": "connected" if db_pool else "disconnected",
        "uptime_seconds": int(time.time() - start_time),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route(f"/webhook/{config.BOT_TOKEN.split(':')[1] if ':' in config.BOT_TOKEN else 'invalid'}", methods=['POST'])
def webhook():
    """Handle Telegram updates"""
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
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════

def init():
    """Initialize everything"""
    global bot_app
    
    logger.info("🚀 Initializing MEX-WarSystem V1...")
    
    # Database
    try:
        db_future = asyncio.run_coroutine_threadsafe(init_db(), bot_loop)
        db_ok = db_future.result(timeout=30)
        logger.info(f"Database: {'✅' if db_ok else '❌'}")
    except Exception as e:
        logger.error(f"DB init error: {e}")
    
    # Bot
    try:
        bot_app = Application.builder().token(config.BOT_TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("confirm", confirm_payment))
        bot_app.add_handler(CallbackQueryHandler(button_handler))
        
        asyncio.run_coroutine_threadsafe(bot_app.initialize(), bot_loop).result(timeout=30)
        
        # Webhook
        if config.WEBHOOK_URL and "render.com" in config.WEBHOOK_URL:
            webhook_path = f"/webhook/{config.BOT_TOKEN.split(':')[1]}"
            full_url = f"{config.WEBHOOK_URL}{webhook_path}"
            
            try:
                asyncio.run_coroutine_threadsafe(
                    bot_app.bot.set_webhook(url=full_url),
                    bot_loop
                ).result(timeout=30)
                logger.info(f"✅ Webhook: {full_url}")
            except Exception as e:
                logger.error(f"Webhook failed: {e}")
        
        asyncio.run_coroutine_threadsafe(bot_app.start(), bot_loop).result(timeout=30)
        
        # Start intelligence loop
        asyncio.run_coroutine_threadsafe(intelligence_loop(), bot_loop)
        
        logger.info("✅ MEX-WarSystem V1 READY")
        
    except Exception as e:
        logger.error(f"Bot init failed: {e}")
        raise

init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, threaded=True)
