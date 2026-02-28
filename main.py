#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
MEX-WARSYSTEM V3.0 - THE REAL MONEY MACHINE
Features: Fake Social Proof, Scarcity, Leaderboards, FOMO Engineering
═══════════════════════════════════════════════════════════════════════
"""

import os
import asyncio
import threading
import aiohttp
import logging
import asyncpg
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask, request, jsonify

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or "0")
PUBLIC_CHANNEL_ID = os.getenv("PUBLIC_CHANNEL_ID", "")
VIP_GROUP_ID = os.getenv("VIP_GROUP_ID", "")
SOL_WALLET = os.getenv("SOL_WALLET", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "8080"))
HELIUS_KEY = os.getenv("HELIUS_API_KEY", "")

app = Flask(__name__)
db_pool = None
bot_app = None
bot_loop = asyncio.new_event_loop()

def run_loop():
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_forever()

threading.Thread(target=run_loop, daemon=True).start()

# ═══════════════════════════════════════════════════════════════════════
# FAKE SOCIAL PROOF ENGINE
# ═══════════════════════════════════════════════════════════════════════

class SocialProof:
    FAKE_USERS = [
        "WhaleHunter", "CryptoKing", "SolanaMaxi", "DeFiDegen", "TokenSniper",
        "MoonShot", "AlphaCaller", "ChainChaser", "DipBuyer", "FomoTrader",
        "GemFinder", "100xHunter", "WalletWatcher", "RugDetective", "LaunchSniper",
        "SolWhale", "CryptoQueen", "DeFiKing", "NFTFlipper", "AlphaWolf"
    ]
    
    PLANS = ["VIP", "Whale Tracker", "Premium", "Token Boost"]
    
    @staticmethod
    def recent_sale():
        user = random.choice(SocialProof.FAKE_USERS)
        plan = random.choice(SocialProof.PLANS)
        time = random.choice(["just now", "1 min ago", "2 mins ago", "3 mins ago", "5 mins ago"])
        return f"🔥 {user} bought {plan} {time}"
    
    @staticmethod
    def online_count():
        return random.randint(23, 67)
    
    @staticmethod
    def today_stats():
        return {
            'new_users': random.randint(12, 34),
            'sales': random.randint(5, 18),
            'revenue': round(random.uniform(8.5, 25.5), 2)
        }
    
    @staticmethod
    def spots_left():
        return random.randint(3, 12)
    
    @staticmethod
    def price_increase_time():
        hours = random.randint(2, 8)
        mins = random.randint(10, 59)
        return f"{hours}h {mins}m"

# ═══════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════

async def init_db():
    global db_pool
    if not DATABASE_URL:
        return False
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5, command_timeout=30, statement_cache_size=0)
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
                    amount_sol DECIMAL(10,4),
                    plan_type TEXT,
                    status TEXT DEFAULT 'pending',
                    tx_hash TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        return True
    except Exception as e:
        logger.error(f"DB error: {e}")
        return False

async def get_user(tid):
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tid)
            if not row:
                await conn.execute("INSERT INTO users (telegram_id) VALUES ($1) ON CONFLICT DO NOTHING", tid)
                row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tid)
            await conn.execute("UPDATE users SET last_active = NOW() WHERE telegram_id = $1", tid)
            return dict(row) if row else None
    except:
        return None

# ═══════════════════════════════════════════════════════════════════════
# SIGNALS
# ═══════════════════════════════════════════════════════════════════════

async def post_signals():
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.dexscreener.com/token-profiles/latest/v1"
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return
                data = await resp.json()
                if not data:
                    return
                
                profile = data[0]
                addr = profile.get('tokenAddress')
                if not addr:
                    return
                
                detail_url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
                async with session.get(detail_url, timeout=5) as dresp:
                    if dresp.status != 200:
                        return
                    
                    details = await dresp.json()
                    if not details.get('pairs'):
                        return
                    
                    pair = details['pairs'][0]
                    symbol = pair['baseToken']['symbol'].replace('*', '').replace('_', '')
                    name = pair['baseToken']['name'].replace('*', '').replace('_', '')
                    price = float(pair['priceUsd'])
                    liquidity = pair.get('liquidity', {}).get('usd', 0)
                    
                    recent = SocialProof.recent_sale()
                    online = SocialProof.online_count()
                    
                    msg = f"""🚀 NEW LAUNCH DETECTED

💎 {name} (${symbol})
💵 Price: ${price:.8f}
💧 Liquidity: ${liquidity:,.0f}

📊 Chart: {pair['url']}

🔥 {recent}
👁️ {online} hunters watching now

💎 Get early access: @ICEMEXWarSystem_Bot"""
                    
                    await bot_app.bot.send_message(
                        PUBLIC_CHANNEL_ID,
                        msg,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Get VIP Access", url="https://t.me/ICEMEXWarSystem_Bot")]
                        ])
                    )
                    logger.info(f"Posted: {symbol}")
                    
    except Exception as e:
        logger.error(f"Post error: {e}")

async def signal_loop():
    while True:
        await post_signals()
        await asyncio.sleep(random.randint(600, 900))

# ═══════════════════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def start(update: Update, context):
    user = update.effective_user
    db_user = await get_user(user.id)
    
    # Process referral
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0].replace("ref_", ""))
            if referrer_id != user.id and db_pool:
                async with db_pool.acquire() as conn:
                    await conn.execute("UPDATE users SET referrals_count = referrals_count + 1 WHERE telegram_id = $1", referrer_id)
                    count = await conn.fetchval("SELECT referrals_count FROM users WHERE telegram_id = $1", referrer_id)
                    if count and count % 3 == 0:
                        expires = datetime.now() + timedelta(days=2)
                        await conn.execute("UPDATE users SET plan_type = 'vip', plan_expires_at = $1 WHERE telegram_id = $2", expires, referrer_id)
                        try:
                            await context.bot.send_message(referrer_id, "🎉 3 REFERRALS! 2 days FREE VIP activated!")
                        except:
                            pass
        except:
            pass
    
    refs = db_user.get('referrals_count', 0) if db_user else 0
    ref_link = f"https://t.me/{context.bot.username}?start=ref_{user.id}"
    
    recent_sale = SocialProof.recent_sale()
    online = SocialProof.online_count()
    stats = SocialProof.today_stats()
    spots = SocialProof.spots_left()
    price_time = SocialProof.price_increase_time()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 BUY VIP (0.5 SOL)", callback_data="buy_vip")],
        [InlineKeyboardButton("🚀 PROMOTE TOKEN", callback_data="promote")],
        [InlineKeyboardButton("🏆 LEADERBOARD", callback_data="leaderboard")],
        [InlineKeyboardButton("📊 CHECK-IN (FREE)", callback_data="checkin")]
    ])
    
    text = f"""👁️ MEX-WARSYSTEM V3.0

Welcome, {user.first_name}!

🔥 LIVE ACTIVITY:
• {online} hunters online now
• {recent_sale}
• {stats['sales']} VIPs today ({stats['revenue']} SOL)

🎯 YOUR STATUS:
• Referrals: {refs}/3 (2 days free per 3)
• Plan: {db_user.get('plan_type', 'FREE').upper() if db_user else 'FREE'}

⏰ URGENT:
Only {spots} VIP spots left at 0.5 SOL!
Price increases in {price_time}!

💰 TIERS:
• VIP: 0.5 SOL (early alerts)
• Whale Tracker: 1 SOL (5 wallets)
• Premium: 3 SOL (everything)

🔗 Your Link:
{ref_link}

⚡ Share to earn free access!"""
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "leaderboard":
        text = """🏆 THIS MONTH'S TOP HUNTERS

🥇 WhaleHunter — 47 refs (14 days VIP)
🥈 CryptoKing — 39 refs (7 days VIP)
🥉 SolanaMaxi — 31 refs (3 days VIP)

4. AlphaWolf — 28 refs
5. GemFinder — 25 refs

🎯 You: Climb the ranks!
Invite friends to win free VIP!"""
        await query.message.reply_text(text)
        return
    
    if query.data == "checkin":
        user = await get_user(user_id)
        if not user:
            return
        
        last = user.get('last_checkin')
        streak = user.get('streak_days', 0)
        now = datetime.now()
        
        if last and (now - last).days < 1:
            hours = 24 - int((now - last).total_seconds() / 3600)
            await query.message.reply_text(f"⏰ Already checked in! Next in {hours}h")
            return
        
        if last and (now - last).days == 1:
            streak += 1
        else:
            streak = 1
        
        reward = ""
        if streak == 7:
            reward = "\n🎁 7 DAY STREAK! 1 day VIP added!"
            if db_pool:
                async with db_pool.acquire() as conn:
                    expires = datetime.now() + timedelta(days=1)
                    await conn.execute("UPDATE users SET plan_type = 'vip', plan_expires_at = $1 WHERE telegram_id = $2", expires, user_id)
        elif streak == 30:
            reward = "\n🔥 30 DAY STREAK! 7 days VIP added!"
        
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("UPDATE users SET streak_days = $1, last_checkin = NOW() WHERE telegram_id = $2", streak, user_id)
        
        await query.message.reply_text(f"""✅ CHECKED IN!

🔥 Streak: {streak} days
{reward}

Keep checking in daily!""")
        return
    
    if query.data == "promote":
        await query.message.reply_text(f"""🚀 TOKEN PROMOTION

📢 Spotlight - 2 SOL
• Featured post in channel
• {SocialProof.online_count()} traders see it

⚡ VIP Alert - 5 SOL
• Instant alert to VIP group

👑 Premium - 10 SOL
• Channel + VIP group
• 24-hour pinned post

To order:
Send SOL to {SOL_WALLET}
Then: /promo TOKEN_ADDRESS TIER

Example:
/promo EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v spotlight""")
        return
    
    if query.data == "buy_vip":
        spots = SocialProof.spots_left()
        price_time = SocialProof.price_increase_time()
        
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("INSERT INTO payments (telegram_id, amount_sol, plan_type) VALUES ($1, $2, $3)", user_id, 0.5, 'vip')
        
        await query.message.reply_text(f"""⚡ URGENT: Only {spots} spots left!

🧾 VIP INVOICE

💰 0.5 SOL (price increases in {price_time}!)

🟣 {SOL_WALLET}

🔥 Why users buy NOW:
• {SocialProof.recent_sale()}
• {SocialProof.today_stats()['sales']} sales today
• Don't miss the next 100x!

After payment:
/confirm TX_HASH

Auto-verification in 10-30s""")

async def promo_cmd(update: Update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /promo TOKEN_ADDRESS TIER\nTiers: spotlight (2), vip_alert (5), premium (10)")
        return
    
    token_address = context.args[0]
    tier = context.args[1].lower()
    prices = {'spotlight': 2.0, 'vip_alert': 5.0, 'premium': 10.0}
    
    if tier not in prices:
        await update.message.reply_text(f"Invalid tier. Choose: {', '.join(prices.keys())}")
        return
    
    price = prices[tier]
    user_id = update.effective_user.id
    
    if not db_pool:
        await update.message.reply_text("❌ Database error")
        return
    
    async with db_pool.acquire() as conn:
        payment = await conn.fetchrow("SELECT * FROM payments WHERE telegram_id = $1 AND amount_sol = $2 AND status = 'pending' ORDER BY id DESC LIMIT 1", user_id, price)
        
        if not payment:
            await update.message.reply_text(f"❌ Payment not found! Send {price} SOL to {SOL_WALLET} first.")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        await update.message.reply_text("❌ Could not fetch token data")
                        return
                    
                    data = await resp.json()
                    if not data.get('pairs'):
                        await update.message.reply_text("❌ Token not found")
                        return
                    
                    pair = data['pairs'][0]
                    symbol = pair['baseToken']['symbol'].replace('*', '').replace('_', '')
                    name = pair['baseToken']['name'].replace('*', '').replace('_', '')
                    
                    await conn.execute("UPDATE payments SET status = 'completed' WHERE id = $1", payment['id'])
                    
                    online = SocialProof.online_count()
                    
                    msg = f"""🚀 COMMUNITY SPOTLIGHT

💎 {name} (${symbol})
💵 Price: ${float(pair['priceUsd']):.8f}
💧 Liquidity: ${pair.get('liquidity', {}).get('usd', 0):,.0f}

📊 Chart: {pair['url']}

👁️ {online} hunters watching now
🔥 {SocialProof.recent_sale()}

DYOR - Community promotion, not financial advice.

💎 Promote your project: @ICEMEXWarSystem_Bot"""
                    
                    await context.bot.send_message(PUBLIC_CHANNEL_ID, msg)
                    await update.message.reply_text(f"✅ {symbol} posted to channel! {online} traders seeing it now.")
                    
                    if tier in ['vip_alert', 'premium'] and VIP_GROUP_ID:
                        await context.bot.send_message(VIP_GROUP_ID, f"⚡ VIP ALERT: New spotlight {symbol}!\nChart: {pair['url']}")
                        await update.message.reply_text("✅ VIP alert sent!")
        except Exception as e:
            logger.error(f"Promo error: {e}")
            await update.message.reply_text("⚠️ Error processing. Contact admin.")

async def confirm(update: Update, context):
    if not context.args:
        await update.message.reply_text("Usage: /confirm TX_HASH")
        return
    
    tx_hash = context.args[0]
    user_id = update.effective_user.id
    
    await update.message.reply_text("🛰 Verifying...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_KEY}"
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
                    if t.get('toUserAccount') == SOL_WALLET:
                        received += float(t.get('amount', 0)) / 10**9
                
                if db_pool:
                    async with db_pool.acquire() as conn:
                        pending = await conn.fetchrow("SELECT * FROM payments WHERE telegram_id = $1 AND status = 'pending' ORDER BY id DESC LIMIT 1", user_id)
                        
                        if pending and received >= pending['amount_sol'] * 0.95:
                            days = 30 if pending['plan_type'] == 'vip' else 365
                            expires = datetime.now() + timedelta(days=days)
                            
                            await conn.execute("UPDATE payments SET status = 'completed', tx_hash = $1 WHERE id = $2", tx_hash, pending['id'])
                            await conn.execute("UPDATE users SET plan_type = $1, plan_expires_at = $2, total_paid = total_paid + $3 WHERE telegram_id = $4",
                                pending['plan_type'], expires, pending['amount_sol'], user_id)
                            
                            online = SocialProof.online_count()
                            
                            try:
                                invite = await context.bot.create_chat_invite_link(VIP_GROUP_ID, expire_date=datetime.now() + timedelta(hours=24), member_limit=1)
                                
                                await update.message.reply_text(f"""✅ CONFIRMED! WELCOME TO THE ELITE!

🎉 {pending['plan_type'].upper()} activated!
⏰ Expires: {expires.strftime('%Y-%m-%d')}

🔥 You're now part of {online} elite hunters!

📊 Next signal in ~{random.randint(5, 15)} minutes!

🔗 VIP LINK: {invite.invite_link}

⚡ Your edge starts NOW.""")
                            except:
                                await update.message.reply_text("✅ Confirmed! Contact admin for link.")
                            
                            await context.bot.send_message(ADMIN_ID, f"💰 SALE: {pending['amount_sol']} SOL from {user_id}")
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
    return jsonify({"status": "MEX-WARSYSTEM V3.0", "database": "connected" if db_pool else "disconnected"})

@app.route(f"/webhook/{BOT_TOKEN.split(':')[1] if ':' in BOT_TOKEN else 'invalid'}", methods=['POST'])
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
    
    logger.info("🚀 Starting MEX-WarSystem V3.0...")
    
    try:
        db_future = asyncio.run_coroutine_threadsafe(init_db(), bot_loop)
        db_ok = db_future.result(timeout=30)
        logger.info(f"DB: {'OK' if db_ok else 'FAIL'}")
    except Exception as e:
        logger.error(f"DB error: {e}")
    
    try:
        bot_app = Application.builder().token(BOT_TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("confirm", confirm))
        bot_app.add_handler(CommandHandler("promo", promo_cmd))
        bot_app.add_handler(CallbackQueryHandler(button))
        
        asyncio.run_coroutine_threadsafe(bot_app.initialize(), bot_loop).result(timeout=30)
        
        if WEBHOOK_URL and "render.com" in WEBHOOK_URL:
            webhook_path = f"/webhook/{BOT_TOKEN.split(':')[1]}"
            full_url = f"{WEBHOOK_URL}{webhook_path}"
            asyncio.run_coroutine_threadsafe(bot_app.bot.set_webhook(url=full_url), bot_loop).result(timeout=30)
            logger.info(f"Webhook: {full_url}")
        
        asyncio.run_coroutine_threadsafe(bot_app.start(), bot_loop).result(timeout=30)
        asyncio.run_coroutine_threadsafe(signal_loop(), bot_loop)
        
        logger.info("✅ V3.0 READY - MONEY MACHINE ACTIVATED")
        
    except Exception as e:
        logger.error(f"Init failed: {e}")
        raise

init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
