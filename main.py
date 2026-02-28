#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
MEX-WARSYSTEM V2.6 - EMERGENCY FIX (Safe Markdown)
═══════════════════════════════════════════════════════════════════════
"""

import os
import asyncio
import threading
import aiohttp
import logging
import asyncpg
import re
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

# SAFE MARKDOWN ESCAPE
def escape_md(text):
    """Escape markdown special characters"""
    if not text:
        return ""
    # Remove or escape problematic chars
    text = str(text)
    text = text.replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
    return text

async def init_db():
    global db_pool
    if not DATABASE_URL:
        return False
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5, command_timeout=30, statement_cache_size=0)
        async with db_pool.acquire() as conn:
            await conn.execute("CREATE TABLE IF NOT EXISTS users (telegram_id BIGINT PRIMARY KEY, plan_type TEXT DEFAULT 'free', referrals_count INT DEFAULT 0, total_paid DECIMAL(10,4) DEFAULT 0)")
            await conn.execute("CREATE TABLE IF NOT EXISTS payments (id SERIAL PRIMARY KEY, telegram_id BIGINT, amount_sol DECIMAL(10,4), plan_type TEXT, status TEXT DEFAULT 'pending')")
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
            return dict(row) if row else None
    except:
        return None

async def analyze_token(token_address, chain="solana"):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if not data.get('pairs'):
                    return None
                
                pair = data['pairs'][0]
                return {
                    'symbol': escape_md(pair['baseToken']['symbol']),
                    'name': escape_md(pair['baseToken']['name']),
                    'price': float(pair['priceUsd']),
                    'liquidity': pair.get('liquidity', {}).get('usd', 0),
                    'volume_24h': pair.get('volume', {}).get('h24', 0),
                    'change_24h': pair.get('priceChange', {}).get('h24', 0),
                    'url': pair['url'],
                    'chain': chain
                }
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return None

async def post_signals():
    """Post with SAFE formatting (no markdown)"""
    try:
        # Simple scan
        async with aiohttp.ClientSession() as session:
            url = "https://api.dexscreener.com/token-profiles/latest/v1"
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return
                
                data = await resp.json()
                if not data:
                    return
                
                # Get first token
                profile = data[0]
                token_addr = profile.get('tokenAddress')
                if not token_addr:
                    return
                
                # Get details
                detail_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_addr}"
                async with session.get(detail_url, timeout=5) as dresp:
                    if dresp.status != 200:
                        return
                    
                    details = await dresp.json()
                    if not details.get('pairs'):
                        return
                    
                    pair = details['pairs'][0]
                    symbol = escape_md(pair['baseToken']['symbol'])
                    name = escape_md(pair['baseToken']['name'])
                    price = float(pair['priceUsd'])
                    liquidity = pair.get('liquidity', {}).get('usd', 0)
                    
                    # PLAIN TEXT message (no markdown)
                    msg = f"""🚀 NEW LAUNCH DETECTED

💎 {name} (${symbol})
💵 Price: ${price:.8f}
💧 Liquidity: ${liquidity:,.0f}

📊 Chart: {pair['url']}

💎 Get early alerts: @ICEMEXWarSystem_Bot"""
                    
                    # Send without markdown
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
        await asyncio.sleep(600)  # 10 minutes

# Handlers
async def start(update, context):
    user = update.effective_user
    db_user = await get_user(user.id)
    refs = db_user.get('referrals_count', 0) if db_user else 0
    ref_link = f"https://t.me/{context.bot.username}?start=ref_{user.id}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Buy VIP (0.5 SOL)", callback_data="buy_vip")],
        [InlineKeyboardButton("🚀 Promote Token", callback_data="promote")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ])
    
    # SAFE text - no markdown
    text = f"""👁️ MEX-WARSYSTEM V2.6

Welcome, {user.first_name}!

🎯 What We Do:
• Track whale wallets
• Detect new launches early
• Token promotion (legal)
• Risk analysis

🎁 FREE ACCESS:
Invite 3 friends = 2 days VIP
Progress: {refs}/3

💰 PAID TIERS:
• VIP: 0.5 SOL/month
• Whale Tracker: 1 SOL
• Premium: 3 SOL

🔗 Your Link:
{ref_link}

⚡ Share & earn!"""
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def button(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "stats":
        user = await get_user(user_id)
        refs = user.get('referrals_count', 0) if user else 0
        await query.message.reply_text(f"📊 Stats\n\nReferrals: {refs}/3\nPlan: {user.get('plan_type', 'FREE').upper() if user else 'FREE'}")
        return
    
    if query.data == "promote":
        await query.message.reply_text(f"""🚀 TOKEN PROMOTION

📢 Spotlight - 2 SOL
• Featured post in channel
• Real chart analysis
• 1000+ traders see it

⚡ VIP Alert - 5 SOL
• Instant alert to VIP group
• Early buyers = organic volume

👑 Premium - 10 SOL
• Channel + VIP group
• 24-hour pinned post

To order:
Send SOL to {SOL_WALLET}
Then reply: /promo TOKEN_ADDRESS TIER

Example:
/promo EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v spotlight""")
        return
    
    if query.data == "buy_vip":
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("INSERT INTO payments (telegram_id, amount_sol, plan_type) VALUES ($1, $2, $3)", user_id, 0.5, 'vip')
        
        await query.message.reply_text(f"""🧾 VIP INVOICE

💰 0.5 SOL
🟣 {SOL_WALLET}

After payment:
/confirm TX_HASH

Auto-verification in 10-30s""")

async def promo_cmd(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /promo TOKEN_ADDRESS TIER\n\nTiers: spotlight (2 SOL), vip_alert (5 SOL), premium (10 SOL)")
        return
    
    token_address = context.args[0]
    tier = context.args[1].lower()
    
    prices = {'spotlight': 2.0, 'vip_alert': 5.0, 'premium': 10.0}
    if tier not in prices:
        await update.message.reply_text(f"Invalid tier. Choose: {', '.join(prices.keys())}")
        return
    
    price = prices[tier]
    user_id = update.effective_user.id
    
    # Check payment
    if not db_pool:
        await update.message.reply_text("❌ Database error")
        return
    
    async with db_pool.acquire() as conn:
        payment = await conn.fetchrow("SELECT * FROM payments WHERE telegram_id = $1 AND amount_sol = $2 AND status = 'pending' ORDER BY id DESC LIMIT 1", user_id, price)
        
        if not payment:
            await update.message.reply_text(f"❌ Payment not found! Send {price} SOL to {SOL_WALLET} first.")
            return
        
        # Get token data
        token_data = await analyze_token(token_address)
        if not token_data:
            await update.message.reply_text("❌ Could not fetch token data. Check address.")
            return
        
        # Mark paid
        await conn.execute("UPDATE payments SET status = 'completed' WHERE id = $1", payment['id'])
        
        # Post to channel (SAFE - no markdown)
        msg = f"""🚀 COMMUNITY SPOTLIGHT

💎 {token_data['name']} (${token_data['symbol']})
💵 Price: ${token_data['price']:.8f}
💧 Liquidity: ${token_data['liquidity']:,.0f}

📊 Chart: {token_data['url']}

DYOR - Community promotion, not financial advice.

💎 Promote your project: @ICEMEXWarSystem_Bot"""
        
        try:
            await context.bot.send_message(PUBLIC_CHANNEL_ID, msg)
            await update.message.reply_text(f"✅ {token_data['symbol']} posted to channel!")
        except Exception as e:
            logger.error(f"Post error: {e}")
            await update.message.reply_text("⚠️ Error posting. Contact admin.")
        
        # VIP alert if applicable
        if tier in ['vip_alert', 'premium'] and VIP_GROUP_ID:
            vip_msg = f"""⚡ VIP ALERT

New Spotlight: {token_data['symbol']}

Price: ${token_data['price']:.8f}
Chart: {token_data['url']}"""
            try:
                await context.bot.send_message(VIP_GROUP_ID, vip_msg)
                await update.message.reply_text("✅ VIP alert sent!")
            except:
                pass

async def confirm(update, context):
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
                            
                            try:
                                invite = await context.bot.create_chat_invite_link(VIP_GROUP_ID, expire_date=datetime.now() + timedelta(hours=24), member_limit=1)
                                await update.message.reply_text(f"""✅ CONFIRMED!

{pending['plan_type'].upper()} activated!
Expires: {expires.strftime('%Y-%m-%d')}

🔗 VIP LINK: {invite.invite_link}

⚡ Your edge starts NOW.""")
                            except:
                                await update.message.reply_text("✅ Confirmed! Contact admin for link.")
                        else:
                            await update.message.reply_text(f"❌ Amount mismatch")
    except Exception as e:
        logger.error(f"Confirm error: {e}")
        await update.message.reply_text("⚠️ Error. Try again.")

# Flask
@app.route("/")
def health():
    return jsonify({"status": "MEX-WARSYSTEM V2.6", "database": "connected" if db_pool else "disconnected"})

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

# Init
def init():
    global bot_app
    
    logger.info("🚀 Starting MEX-WarSystem V2.6...")
    
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
        
        logger.info("✅ V2.6 READY - SAFE MARKDOWN MODE")
        
    except Exception as e:
        logger.error(f"Init failed: {e}")
        raise

init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
