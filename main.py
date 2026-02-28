#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
MEX-WARSYSTEM V2 - VIRAL GROWTH EDITION
Features: Fake Social Proof, Scarcity, Leaderboards, FOMO Notifications
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
# CONFIG
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
    
    VIP_PRICE_SOL: float = float(os.getenv("VIP_PRICE_SOL", "0.5"))
    WHALE_PRICE_SOL: float = float(os.getenv("WHALE_PRICE_SOL", "1.0"))
    PREMIUM_PRICE_SOL: float = float(os.getenv("PREMIUM_PRICE_SOL", "3.0"))
    
    # Fake scarcity settings
    MAX_VIP_SPOTS: int = 100
    SPOTS_REMAINING: int = random.randint(7, 23)  # Dynamic

config = Config()

# ═══════════════════════════════════════════════════════════════════════
# GLOBAL
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
db_pool: Optional[asyncpg.Pool] = None
bot_app: Optional[Application] = None
start_time = time.time()
bot_loop = asyncio.new_event_loop()

def run_loop():
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_forever()

threading.Thread(target=run_loop, daemon=True).start()

# Fake activity generator
class FakeActivity:
    """Generate believable fake social proof"""
    
    FAKE_USERS = [
        "WhaleHunter", "CryptoKing", "SolanaMaxi", "DeFiDegen", "TokenSniper",
        "MoonShot", "AlphaCaller", "ChainChaser", "DipBuyer", "FomoTrader",
        "GemFinder", "100xHunter", "WalletWatcher", "RugDetective", "LaunchSniper"
    ]
    
    @staticmethod
    def get_recent_sale():
        """Generate fake recent purchase"""
        user = random.choice(FakeActivity.FAKE_USERS)
        plan = random.choice(["VIP", "Whale Tracker", "Premium"])
        time_ago = random.choice(["just now", "1 min ago", "2 mins ago", "5 mins ago"])
        return f"🔥 {user} bought {plan} {time_ago}"
    
    @staticmethod
    def get_online_count():
        """Fake online users"""
        return random.randint(12, 47)
    
    @staticmethod
    def get_today_stats():
        """Fake daily stats"""
        return {
            'new_users': random.randint(8, 25),
            'vip_activations': random.randint(3, 12),
            'whale_alerts': random.randint(5, 15)
        }

# ═══════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════

async def init_db():
    global db_pool
    if not config.DATABASE_URL:
        return False
    
    try:
        db_pool = await asyncpg.create_pool(
            config.DATABASE_URL,
            min_size=1, max_size=5,
            command_timeout=30,
            statement_cache_size=0
        )
        
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    plan_type TEXT DEFAULT 'free',
                    plan_expires_at TIMESTAMP,
                    referrals_count INT DEFAULT 0,
                    referred_by BIGINT,
                    total_paid DECIMAL(10,4) DEFAULT 0,
                    streak_days INT DEFAULT 0,
                    last_checkin TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_active TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT,
                    tx_hash TEXT UNIQUE,
                    amount_sol DECIMAL(10,4),
                    plan_type TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Leaderboard tracking
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS leaderboard (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT,
                    month DATE,
                    referrals INT DEFAULT 0,
                    reward_claimed BOOLEAN DEFAULT FALSE
                )
            """)
        
        return True
    except Exception as e:
        logger.error(f"DB error: {e}")
        return False

async def get_user(telegram_id: int):
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            if not row:
                await conn.execute("INSERT INTO users (telegram_id) VALUES ($1) ON CONFLICT DO NOTHING", telegram_id)
                row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            await conn.execute("UPDATE users SET last_active = NOW() WHERE telegram_id = $1", telegram_id)
            return dict(row) if row else None
    except Exception as e:
        return None

# ═══════════════════════════════════════════════════════════════════════
# SIGNAL ENGINE
# ═══════════════════════════════════════════════════════════════════════

async def scan_launches():
    """Find new tokens"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.dexscreener.com/token-profiles/latest/v1"
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return []
                
                data = await resp.json()
                tokens = []
                
                for profile in data[:10]:
                    addr = profile.get('tokenAddress')
                    if not addr:
                        continue
                    
                    detail_url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
                    async with session.get(detail_url, timeout=5) as dresp:
                        if dresp.status != 200:
                            continue
                        
                        details = await dresp.json()
                        if not details.get('pairs'):
                            continue
                        
                        pair = details['pairs'][0]
                        liquidity = pair.get('liquidity', {}).get('usd', 0)
                        
                        if 5000 < liquidity < 50000:
                            tokens.append({
                                'symbol': pair['baseToken']['symbol'],
                                'name': pair['baseToken']['name'],
                                'price': float(pair['priceUsd']),
                                'liquidity': liquidity,
                                'volume': pair.get('volume', {}).get('h24', 0),
                                'change': pair.get('priceChange', {}).get('h24', 0),
                                'url': pair['url'],
                                'chain': profile.get('chainId', 'solana')
                            })
                
                return tokens[:2]
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return []

async def post_signals():
    """Post to channel"""
    try:
        tokens = await scan_launches()
        
        for token in tokens:
            risk = random.randint(30, 70)
            emoji = "🟢" if risk < 40 else "🟡" if risk < 60 else "🔴"
            
            msg = f"""🚀 **NEW LAUNCH DETECTED**

💎 {token['name']} (${token['symbol']})
🔗 {token['chain'].upper()}

💵 Price: ${token['price']:.8f}
💧 Liquidity: ${token['liquidity']:,.0f}
📈 24h: {token['change']:+.1f}%

⚠️ Risk: {emoji} {risk}/100

📊 {token['url']}

🔥 {FakeActivity.get_recent_sale()}

💎 Get early alerts: @ICEMEXWarSystem_Bot"""
            
            await bot_app.bot.send_message(config.PUBLIC_CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)
            
    except Exception as e:
        logger.error(f"Post error: {e}")

async def signal_loop():
    while True:
        await post_signals()
        await asyncio.sleep(random.randint(600, 1200))

# ═══════════════════════════════════════════════════════════════════════
# LEADERBOARD SYSTEM
# ═══════════════════════════════════════════════════════════════════════

async def get_leaderboard():
    """Get top referrers this month"""
    if not db_pool:
        return []
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT u.telegram_id, u.username, u.first_name, l.referrals
                FROM leaderboard l
                JOIN users u ON l.telegram_id = u.telegram_id
                WHERE l.month = DATE_TRUNC('month', NOW())
                ORDER BY l.referrals DESC
                LIMIT 10
            """)
            return [dict(row) for row in rows]
    except:
        return []

async def update_leaderboard(user_id: int):
    """Update user's referral count"""
    if not db_pool:
        return
    
    try:
        async with db_pool.acquire() as conn:
            # Get current month
            current_month = datetime.now().replace(day=1).date()
            
            # Insert or update
            await conn.execute("""
                INSERT INTO leaderboard (telegram_id, month, referrals)
                VALUES ($1, $2, 1)
                ON CONFLICT (telegram_id, month) 
                DO UPDATE SET referrals = leaderboard.referrals + 1
            """, user_id, current_month)
    except:
        pass

# ═══════════════════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = await get_user(user.id)
    
    # Process referral
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0].replace("ref_", ""))
            if referrer_id != user.id:
                await update_leaderboard(referrer_id)
                # Check for reward
                if db_pool:
                    async with db_pool.acquire() as conn:
                        count = await conn.fetchval("""
                            SELECT referrals FROM leaderboard 
                            WHERE telegram_id = $1 AND month = DATE_TRUNC('month', NOW())
                        """, referrer_id)
                        
                        if count and count % 3 == 0:  # Every 3 referrals
                            # Grant free VIP
                            expires = datetime.now() + timedelta(days=2)
                            await conn.execute("""
                                UPDATE users SET plan_type = 'vip', plan_expires_at = $1
                                WHERE telegram_id = $2
                            """, expires, referrer_id)
                            
                            try:
                                await context.bot.send_message(
                                    referrer_id,
                                    f"🎉 **3 REFERRALS!**\n\n2 days FREE VIP activated!\nKeep going! 🚀",
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            except:
                                pass
        except:
            pass
    
    refs = db_user.get('referrals_count', 0) if db_user else 0
    ref_link = f"https://t.me/{context.bot.username}?start=ref_{user.id}"
    
    # Fake activity
    online = FakeActivity.get_online_count()
    recent_sale = FakeActivity.get_recent_sale()
    today_stats = FakeActivity.get_today_stats()
    
    # Scarcity
    spots_left = max(0, config.MAX_VIP_SPOTS - random.randint(60, 85))
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 VIP (0.5 SOL)", callback_data="buy_vip")],
        [InlineKeyboardButton("🐋 Whale Tracker (1 SOL)", callback_data="buy_whale")],
        [InlineKeyboardButton("👑 Premium (3 SOL)", callback_data="buy_premium")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("📊 Check In (Free)", callback_data="checkin")]
    ])
    
    text = f"""👁️ **MEX-WARSYSTEM V2**

Welcome, {user.first_name}!

🔥 **LIVE ACTIVITY:**
• {online} users hunting right now
• {recent_sale}
• {today_stats['vip_activations']} VIPs today

🎯 **Your Status:**
• Referrals: {refs}/3 (2 days free per 3)
• Plan: {db_user.get('plan_type', 'FREE').upper() if db_user else 'FREE'}

⏰ **URGENT:**
Only {spots_left} VIP spots left at 0.5 SOL!
Price increases when sold out.

💰 **TIERS:**
• VIP: 0.5 SOL (early alerts)
• Whale Tracker: 1 SOL (5 wallets)
• Premium: 3 SOL (everything)

🔗 **Your Link:**
`{ref_link}`

⚡ Share to earn free access!"""
    
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "leaderboard":
        # Show fake + real leaderboard
        leaderboard = await get_leaderboard()
        
        text = "🏆 **THIS MONTH'S TOP HUNTERS**\n\n"
        
        # Add fake entries at top
        fake_leaders = [
            ("🥇 WhaleHunter", 47),
            ("🥈 CryptoKing", 39),
            ("🥉 SolanaMaxi", 31)
        ]
        
        for i, (name, refs) in enumerate(fake_leaders, 1):
            reward = "🎁 14 days VIP" if i == 1 else "🎁 7 days VIP" if i == 2 else "🎁 3 days VIP"
            text += f"{i}. {name} — {refs} refs {reward}\n"
        
        if leaderboard:
            text += "\n**Real Hunters:**\n"
            for i, user in enumerate(leaderboard[:5], 4):
                name = user.get('first_name') or user.get('username') or f"User{i}"
                text += f"{i}. {name} — {user['referrals']} refs\n"
        
        text += f"\n🎯 **You:** {user_id}\nInvite friends to climb the ranks!"
        
        await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return
    
    if query.data == "checkin":
        # Daily check-in for streak
        user = await get_user(user_id)
        if not user:
            return
        
        last_checkin = user.get('last_checkin')
        streak = user.get('streak_days', 0)
        
        now = datetime.now()
        
        # Check if already checked in today
        if last_checkin and (now - last_checkin).days < 1:
            hours_left = 24 - int((now - last_checkin).total_seconds() / 3600)
            await query.message.reply_text(f"⏰ Already checked in! Next in {hours_left}h")
            return
        
        # Update streak
        if last_checkin and (now - last_checkin).days == 1:
            streak += 1
        else:
            streak = 1
        
        # Reward for streaks
        reward_text = ""
        if streak == 7:
            reward_text = "\n🎁 **7 DAY STREAK!** 1 day VIP added!"
            if db_pool:
                async with db_pool.acquire() as conn:
                    expires = datetime.now() + timedelta(days=1)
                    await conn.execute("""
                        UPDATE users SET plan_type = 'vip', plan_expires_at = $1
                        WHERE telegram_id = $2 AND (plan_type = 'free' OR plan_expires_at < NOW())
                    """, expires, user_id)
        elif streak == 30:
            reward_text = "\n🔥 **30 DAY STREAK!** 7 days VIP added!"
        
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE users SET streak_days = $1, last_checkin = NOW()
                    WHERE telegram_id = $2
                """, streak, user_id)
        
        await query.message.reply_text(
            f"""✅ **CHECKED IN!**

🔥 Streak: {streak} days
{reward_text}

Keep checking in daily for free VIP!""",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Purchase flows
    prices = {
        'buy_vip': (0.5, 'vip'),
        'buy_whale': (1.0, 'whale'),
        'buy_premium': (3.0, 'premium')
    }
    
    if query.data in prices:
        price, plan = prices[query.data]
        
        # Save pending
        if db_pool:
            try:
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO payments (telegram_id, amount_sol, plan_type)
                        VALUES ($1, $2, $3)
                    """, user_id, price, plan)
            except:
                pass
        
        # Scarcity message
        spots = random.randint(3, 12)
        
        await query.message.reply_text(f"""⚡ **URGENT: Only {spots} spots left!**

🧾 **{plan.upper()} INVOICE**

💰 **{price} SOL** (price increases soon!)
🟣 `{config.SOL_WALLET}`

⏳ **After payment:**
Reply: `/confirm TX_HASH`

💡 **Why users buy:**
• {FakeActivity.get_recent_sale()}
• {random.randint(8, 25)} new users today
• Don't miss the next 100x!

🔥 **Act fast - spots filling up!**""", parse_mode=ParseMode.MARKDOWN)

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /confirm TX_HASH")
        return
    
    tx_hash = context.args[0]
    user_id = update.effective_user.id
    
    await update.message.reply_text("🛰 Verifying...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/transactions/?api-key={config.HELIUS_KEY}"
            async with session.post(url, json={"transactions": [tx_hash]}) as resp:
                if resp.status != 200:
                    await update.message.reply_text("❌ API error")
                    return
                
                data = await resp.json()
                if not data:
                    await update.message.reply_text("❌ TX not found")
                    return
                
                tx = data[0]
                transfers = tx.get('nativeTransfers', [])
                received = 0.0
                
                for t in transfers:
                    if t.get('toUserAccount') == config.SOL_WALLET:
                        received += float(t.get('amount', 0)) / 10**9
                
                if db_pool:
                    async with db_pool.acquire() as conn:
                        pending = await conn.fetchrow("""
                            SELECT * FROM payments 
                            WHERE telegram_id = $1 AND status = 'pending'
                            ORDER BY id DESC LIMIT 1
                        """, user_id)
                        
                        if pending and received >= pending['amount_sol'] * 0.95:
                            days = 30 if pending['plan_type'] in ['vip', 'whale'] else 365
                            expires = datetime.now() + timedelta(days=days)
                            
                            await conn.execute("""
                                UPDATE payments SET status = 'completed', tx_hash = $1
                                WHERE id = $2
                            """, tx_hash, pending['id'])
                            
                            await conn.execute("""
                                UPDATE users SET plan_type = $1, plan_expires_at = $2, total_paid = total_paid + $3
                                WHERE telegram_id = $4
                            """, pending['plan_type'], expires, pending['amount_sol'], user_id)
                            
                            # Success message with FOMO
                            await update.message.reply_text(f"""✅ **CONFIRMED! Welcome to the inner circle!**

🎉 **{pending['plan_type'].upper()}** activated!
⏰ Expires: {expires.strftime('%Y-%m-%d')}

🔥 **You're now part of {random.randint(50, 150)} elite hunters!**

📊 Next signal dropping in ~{random.randint(5, 15)} minutes!

⚡ **Your edge starts NOW.**""", parse_mode=ParseMode.MARKDOWN)
                            
                            # Notify admin
                            await context.bot.send_message(
                                config.ADMIN_ID,
                                f"💰 SALE: {pending['amount_sol']} SOL from {user_id}"
                            )
                        else:
                            await update.message.reply_text(f"❌ Amount mismatch")
    except Exception as e:
        logger.error(f"Confirm error: {e}")
        await update.message.reply_text("⚠️ Error. Try again.")

# ═══════════════════════════════════════════════════════════════════════
# FLASK
# ═══════════════════════════════════════════════════════════════════════

@app.route("/")
def health():
    return jsonify({
        "status": "MEX-WARSYSTEM V2 🟢",
        "database": "connected" if db_pool else "disconnected"
    })

@app.route(f"/webhook/{config.BOT_TOKEN.split(':')[1] if ':' in config.BOT_TOKEN else 'invalid'}", methods=['POST'])
def webhook():
    if not bot_app:
        return jsonify({"error": "Not ready"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        
        update = Update.de_json(data, bot_app.bot)
        future = asyncio.run_coroutine_threadsafe(bot_app.process_update(update), bot_loop)
        future.result(timeout=10)
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════
# INIT
# ═══════════════════════════════════════════════════════════════════════

def init():
    global bot_app
    
    logger.info("🚀 Starting MEX-WarSystem V2...")
    
    try:
        db_future = asyncio.run_coroutine_threadsafe(init_db(), bot_loop)
        db_ok = db_future.result(timeout=30)
        logger.info(f"DB: {'OK' if db_ok else 'FAIL'}")
    except Exception as e:
        logger.error(f"DB error: {e}")
    
    try:
        bot_app = Application.builder().token(config.BOT_TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("confirm", confirm))
        bot_app.add_handler(CallbackQueryHandler(button))
        
        asyncio.run_coroutine_threadsafe(bot_app.initialize(), bot_loop).result(timeout=30)
        
        if config.WEBHOOK_URL and "render.com" in config.WEBHOOK_URL:
            webhook_path = f"/webhook/{config.BOT_TOKEN.split(':')[1]}"
            full_url = f"{config.WEBHOOK_URL}{webhook_path}"
            asyncio.run_coroutine_threadsafe(bot_app.bot.set_webhook(url=full_url), bot_loop).result(timeout=30)
            logger.info(f"Webhook: {full_url}")
        
        asyncio.run_coroutine_threadsafe(bot_app.start(), bot_loop).result(timeout=30)
        asyncio.run_coroutine_threadsafe(signal_loop(), bot_loop)
        
        logger.info("✅ V2 READY")
        
    except Exception as e:
        logger.error(f"Init failed: {e}")
        raise

init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, threaded=True)
