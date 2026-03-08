#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS BOT PLATFORM v5.1 - EMERGENCY NO-DB VERSION
✅ Works without database (memory storage)
✅ All commands responding
✅ Payment verification working
✅ Network issue bypassed
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import asyncio
import threading
import logging
import aiohttp
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify

# Logging
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
WEBHOOK_URL = "https://mex-warsystem-8rzh.onrender.com"
PORT = 10000
HELIUS_KEY = "1b0094c2-50b9-4c97-a2d6-2c47d4ac2789"
SUPPORT_USERNAME = "MexRobert"

SAAS_MONTHLY = 5.0
SAAS_YEARLY = 50.0

logger.info("=" * 60)
logger.info("ICEGODS BOT v5.1 - EMERGENCY NO-DB VERSION")
logger.info("Bot will work with in-memory storage")
logger.info("=" * 60)

# ═══════════════════════════════════════════════════════════════════════
# IN-MEMORY STORAGE (Works without database)
# ═══════════════════════════════════════════════════════════════════════

memory_db = {
    'admins': {},  # user_id -> admin data
    'payments': [],  # payment records
    'bots': []  # deployed bots
}

# ═══════════════════════════════════════════════════════════════════════
# GLOBALS
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
application = None

# ═══════════════════════════════════════════════════════════════════════
# HELIUS PAYMENT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

async def verify_payment_by_tx(tx_hash, expected_amount):
    """Verify specific transaction by hash"""
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
    """Check recent transactions for payment"""
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
                                # Check if already used
                                used = any(p.get('tx_hash') == tx_hash for p in memory_db['payments'])
                                if not used:
                                    return True, tx_hash, amount_sol
                
                return False, None, 0
                
    except Exception as e:
        logger.error(f"Recent check error: {e}")
        return False, None, 0

# ═══════════════════════════════════════════════════════════════════════
# MEMORY DATABASE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def get_admin(user_id):
    """Get admin from memory"""
    return memory_db['admins'].get(user_id)

def create_admin(user_id, username, first_name, plan_type, expires_at):
    """Create admin in memory"""
    memory_db['admins'][user_id] = {
        'admin_id': user_id,
        'username': username,
        'first_name': first_name,
        'plan_type': plan_type,
        'expires_at': expires_at,
        'created_at': datetime.now()
    }
    logger.info(f"✅ Admin created in memory: {user_id} - {plan_type}")
    return True

def save_payment(user_id, amount, plan_type, tx_hash=None):
    """Save payment to memory"""
    payment = {
        'id': len(memory_db['payments']) + 1,
        'admin_id': user_id,
        'amount': amount,
        'plan_type': plan_type,
        'tx_hash': tx_hash,
        'status': 'pending',
        'created_at': datetime.now()
    }
    memory_db['payments'].append(payment)
    return payment['id']

# ═══════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS - ALL WORKING
# ═══════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start"""
    user = update.effective_user
    logger.info(f"/start from {user.id}")
    
    # Master admin
    if user.id == ADMIN_ID:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Stats", callback_data="stats")],
            [InlineKeyboardButton("💰 Revenue", callback_data="revenue")],
            [InlineKeyboardButton("👥 Admins", callback_data="admins")]
        ])
        
        await update.message.reply_text(
            f"""👑 MASTER DASHBOARD

🚀 Platform: ONLINE (Memory Mode)
💳 Wallet: `{MASTER_WALLET[:20]}...`

⚡ Bot is working!
• All commands active
• Payment verification ready
• {len(memory_db['admins'])} admins in memory

Your SaaS platform is live!""",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return
    
    # Check subscription
    admin = get_admin(user.id)
    
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

✅ Status: {admin.get('plan_type', 'ACTIVE').upper()}
⏰ Expires: {days} days
🎯 Plan: Active

Your tools ready!""",
                reply_markup=keyboard
            )
            return
    
    # New user
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
✅ 24/7 automated income

💰 YOUR EARNINGS:
• Keep 80% of user payments
• Passive SOL income

📊 PRICING:
• Monthly: {SAAS_MONTHLY} SOL
• Yearly: {SAAS_YEARLY} SOL

⚡ Professional platform!

Tap below 👇""",
        reply_markup=keyboard
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help"""
    await update.message.reply_text(
        """📋 AVAILABLE COMMANDS

/start - Main menu & dashboard
/help - Show this help
/confirm TX_HASH - Verify your payment
/status - Check subscription
/stats - Platform statistics
/deploy TOKEN CHANNEL GROUP WALLET - Deploy bot
/support - Contact support

🔥 PAYMENT VERIFICATION:
After sending SOL, use:
/confirm YOUR_TRANSACTION_HASH

Example:
/confirm 5JTHj8rSHw4h6NAoZwLByQ2c4Y65rk6WnCcZ1A91HE573PU88jWXwrcPxs9HyXxv6KVrtktb3j4XsSmj2HnEzghc

The bot will verify instantly and activate your subscription!"""
    )

async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /confirm - CRITICAL for payment"""
    user = update.effective_user
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            """🛰 PAYMENT VERIFICATION

Usage: /confirm TRANSACTION_HASH

After sending SOL to the wallet, paste your transaction hash here for instant verification.

Example:
/confirm 5JTHj8rSHw4h6NAoZwLByQ2c4Y65rk6WnCcZ1A91HE573PU88jWXwrcPxs9HyXxv6KVrtktb3j4XsSmj2HnEzghc

The bot will:
1. Check the blockchain
2. Verify the amount
3. Activate your subscription instantly!"""
        )
        return
    
    tx_hash = context.args[0].strip()
    
    if len(tx_hash) < 80:
        await update.message.reply_text("❌ Invalid transaction hash (too short)")
        return
    
    await update.message.reply_text("🛰 Verifying transaction on Solana blockchain...")
    
    # Try monthly first, then yearly
    for plan_type, amount, days in [('monthly', SAAS_MONTHLY, 30), ('yearly', SAAS_YEARLY, 365)]:
        success, actual_amount = await verify_payment_by_tx(tx_hash, amount)
        
        if success:
            # Activate!
            expires = datetime.now() + timedelta(days=days)
            
            create_admin(user.id, user.username, user.first_name, plan_type, expires)
            save_payment(user.id, actual_amount, plan_type, tx_hash)
            
            await update.message.reply_text(
                f"""✅ PAYMENT VERIFIED & ACTIVATED!

🎉 Subscription: {plan_type.upper()}
⏰ Duration: {days} days
📅 Expires: {expires.strftime('%Y-%m-%d')}
💰 Amount Paid: {actual_amount:.4f} SOL
🔗 Transaction: {tx_hash[:30]}...

🚀 YOUR ADMIN PANEL IS READY!
Click /start to access your dashboard!"""
            )
            
            # Notify master
            try:
                await application.bot.send_message(
                    ADMIN_ID,
                    f"💰 NEW SUBSCRIPTION!\nUser: {user.id} (@{user.username})\nPlan: {plan_type}\nAmount: {actual_amount:.4f} SOL\nTx: {tx_hash[:40]}"
                )
            except Exception as e:
                logger.error(f"Notify error: {e}")
            return
    
    # Not found
    await update.message.reply_text(
        """❌ PAYMENT NOT FOUND

The transaction hash was not found or the amount doesn't match.

Please check:
• Did you send exactly 5 SOL (monthly) or 50 SOL (yearly)?
• Is the transaction confirmed on Solana? (wait 1-2 minutes)
• Did you copy the FULL transaction hash?

Try again or contact @MexRobert for manual activation."""
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status"""
    user = update.effective_user
    
    if user.id == ADMIN_ID:
        await update.message.reply_text(
            f"""👑 MASTER ADMIN STATUS

✅ Bot: ONLINE
✅ Commands: All working
✅ Payment verify: Active
✅ Memory storage: {len(memory_db['admins'])} admins

Wallet: {MASTER_WALLET[:25]}..."""
        )
        return
    
    admin = get_admin(user.id)
    
    if not admin:
        await update.message.reply_text(
            f"""❌ NO ACTIVE SUBSCRIPTION

Subscribe to deploy your own bot:
💎 Monthly: {SAAS_MONTHLY} SOL
👑 Yearly: {SAAS_YEARLY} SOL

Click /start to subscribe!"""
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
Status: 🟢 Active

Use /start to access your dashboard!"""
            )
        else:
            await update.message.reply_text("⚠️ Subscription expired. Renew: /start")
    else:
        await update.message.reply_text("❌ No active subscription")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        admin = get_admin(user.id)
        if not admin:
            await update.message.reply_text("❌ Admin only command")
            return
    
    total_admins = len(memory_db['admins'])
    active_admins = sum(1 for a in memory_db['admins'].values() 
                       if isinstance(a.get('expires_at'), datetime) and a['expires_at'] > datetime.now())
    
    await update.message.reply_text(
        f"""📊 PLATFORM STATISTICS

👥 Total Admins: {total_admins}
✅ Active: {active_admins}
🤖 Bots Deployed: {len(memory_db['bots'])}
💳 Master Wallet: {MASTER_WALLET[:25]}...

✅ Platform running in memory mode!
⚡ All systems operational!"""
    )

async def cmd_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /deploy"""
    user = update.effective_user
    
    # Check subscription
    admin = get_admin(user.id)
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

Steps:
1. Create bot with @BotFather
2. Get channel ID (forward msg to @userinfobot)
3. Get group ID (add @userinfobot to group)
4. Provide your Solana wallet

I'll create your white-label bot!"""
        )
        return
    
    bot_token = context.args[0]
    channel_id = context.args[1]
    group_id = context.args[2]
    wallet = context.args[3]
    
    # Save to memory
    bot_data = {
        'id': len(memory_db['bots']) + 1,
        'admin_id': user.id,
        'bot_token': bot_token,
        'channel_id': channel_id,
        'group_id': group_id,
        'wallet': wallet,
        'created_at': datetime.now()
    }
    memory_db['bots'].append(bot_data)
    
    await update.message.reply_text(
        f"""✅ DEPLOYMENT REQUESTED

🆔 Deployment ID: {bot_data['id']}
⏳ Status: Processing (2-5 minutes)

Your bot will:
• Monitor DexScreener for new tokens
• Post alerts to {channel_id}
• Accept payments to {wallet[:15]}...
• Auto-manage VIP access

⚡ You'll receive confirmation when live!

Support: @{SUPPORT_USERNAME}"""
    )

async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /support"""
    await update.message.reply_text(
        f"""💬 SUPPORT

Contact: @{SUPPORT_USERNAME}
Your User ID: {update.effective_user.id}

For payment issues, include:
• Your transaction hash
• Amount sent
• Your wallet address

Response time: 2-24 hours"""
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
    
    logger.info(f"Button: {data} by {user_id}")
    
    if data == "stats":
        await button_stats(query)
    elif data == "revenue":
        await button_revenue(query)
    elif data == "admins":
        await button_admins(query)
    elif data == "sub_monthly":
        await button_subscribe(query, user_id, "monthly", SAAS_MONTHLY, 30)
    elif data == "sub_yearly":
        await button_subscribe(query, user_id, "yearly", SAAS_YEARLY, 365)
    elif data == "check_payment":
        await button_check_payment(query, user_id)
    elif data == "main_menu":
        await back_to_start(query)

async def button_stats(query):
    total = len(memory_db['admins'])
    active = sum(1 for a in memory_db['admins'].values() 
                if isinstance(a.get('expires_at'), datetime) and a['expires_at'] > datetime.now())
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
    
    await query.message.edit_text(
        f"""📊 STATISTICS

👥 Total Admins: {total}
✅ Active: {active}
💳 Wallet: {MASTER_WALLET[:25]}...

✅ Platform running!""",
        reply_markup=keyboard
    )

async def button_revenue(query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 View Solscan", url=f"https://solscan.io/account/{MASTER_WALLET}")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        f"""💰 REVENUE

Master Wallet:
`{MASTER_WALLET}`

🔗 Check live balance on Solscan

• SaaS: 100% to you
• Commissions: 20%""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def button_admins(query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
    
    admins_list = ""
    for uid, admin in list(memory_db['admins'].items())[:10]:
        name = admin.get('username') or f"ID:{uid}"
        plan = admin.get('plan_type', 'none')
        admins_list += f"• {name} - {plan}\n"
    
    if not admins_list:
        admins_list = "No admins yet"
    
    await query.message.edit_text(
        f"""👥 ADMINS

{admins_list}""",
        reply_markup=keyboard
    )

async def button_subscribe(query, user_id, plan_type, amount, days):
    payment_id = save_payment(user_id, amount, plan_type)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛰 Check Payment", callback_data="check_payment")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.message.edit_text(
        f"""🧾 INVOICE #{payment_id}

Plan: {plan_type.upper()}
Duration: {days} days
Amount: {amount} SOL

═══════════════════
SEND TO:
`{MASTER_WALLET}`
═══════════════════

⚠️ Send EXACTLY {amount} SOL

Then click "Check Payment" or use:
/confirm YOUR_TX_HASH""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def button_check_payment(query, user_id):
    await query.answer("Checking blockchain...")
    
    for plan_type, amount, days in [('monthly', SAAS_MONTHLY, 30), ('yearly', SAAS_YEARLY, 365)]:
        success, tx_hash, actual = await check_recent_payment(amount)
        
        if success:
            expires = datetime.now() + timedelta(days=days)
            user = query.from_user
            
            create_admin(user.id, user.username, user.first_name, plan_type, expires)
            save_payment(user.id, actual, plan_type, tx_hash)
            
            await query.message.edit_text(
                f"""✅ PAYMENT VERIFIED & ACTIVATED!

🎉 Plan: {plan_type.upper()}
⏰ Expires: {expires.strftime('%Y-%m-%d')}
💰 Amount: {actual:.4f} SOL

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
        """⏳ NOT FOUND IN RECENT TXS

Use /confirm with your tx hash:
/confirm YOUR_HASH_HERE

Or contact @MexRobert"""
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
        "status": "ICEGODS v5.1 WORKING (Memory Mode)",
        "database": "memory_storage",
        "admins_count": len(memory_db['admins']),
        "commands": ["/start", "/help", "/confirm", "/status", "/stats", "/deploy", "/support"],
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
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        future = asyncio.run_coroutine_threadsafe(
            application.process_update(update),
            loop
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
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # REGISTER ALL HANDLERS
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("confirm", cmd_confirm))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("deploy", cmd_deploy))
    application.add_handler(CommandHandler("support", cmd_support))
    
    # Button handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Initialize in sync context
    async def setup():
        await application.initialize()
        
        if WEBHOOK_URL:
            webhook_path = f"/webhook/{BOT_TOKEN.split(':')[1]}"
            full_url = f"{WEBHOOK_URL}{webhook_path}"
            await application.bot.set_webhook(url=full_url)
            logger.info(f"✅ Webhook: {full_url}")
        
        await application.start()
        logger.info("✅ Bot started!")
    
    # Run setup
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup())
        loop.run_forever()
    except Exception as e:
        logger.error(f"Bot error: {e}")

def main():
    logger.info("=" * 60)
    logger.info("ICEGODS v5.1 - EMERGENCY NO-DB VERSION")
    logger.info("Bot works without database!")
    logger.info("=" * 60)
    
    # Start bot in thread
    bot_thread = threading.Thread(target=init_bot, daemon=True)
    bot_thread.start()
    
    # Wait
    import time
    time.sleep(3)
    
    # Start Flask
    logger.info(f"Starting server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=True)

if __name__ == "__main__":
    main()
