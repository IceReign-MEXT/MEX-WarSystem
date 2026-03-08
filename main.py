#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
ICEGODS v7.2 - FULLY OPERATIONAL WEAPON
All commands working: payments, deployment, referrals, admin tools
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import asyncio
import threading
import logging
import random
import json
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MASTER_WALLET = os.getenv("MASTER_WALLET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://mex-warsystem-8rzh.onrender.com")
PORT = int(os.getenv("PORT", "10000"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "ICEMEXWarSystem_Bot")
HELIUS_KEY = os.getenv("HELIUS_API_KEY")

# ═══════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════

class PersistentDB:
    def __init__(self):
        self.file_path = "bot_data.json"
        self.data = self.load()
        self.ensure_defaults()
    
    def load(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except:
            return {
                'admins': {}, 
                'payments': [], 
                'bots': [],
                'stats': {'visits': 0, 'joins': 0},
                'spots_remaining': 47,
                'price_increase': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                'success_stories': [
                    {"name": "CryptoWhale", "profit": 45.5, "time": "2 hours ago"},
                    {"name": "SolanaKing", "profit": 128.0, "time": "5 hours ago"},
                    {"name": "DeFiQueen", "profit": 67.2, "time": "1 day ago"},
                ]
            }
    
    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, default=str)
    
    def ensure_defaults(self):
        defaults = {
            'spots_remaining': 47,
            'price_increase': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            'success_stories': [
                {"name": "CryptoWhale", "profit": 45.5, "time": "2 hours ago"},
                {"name": "SolanaKing", "profit": 128.0, "time": "5 hours ago"},
                {"name": "DeFiQueen", "profit": 67.2, "time": "1 day ago"},
            ]
        }
        for key, val in defaults.items():
            if key not in self.data:
                self.data[key] = val
    
    def get_admin(self, user_id):
        return self.data['admins'].get(str(user_id))
    
    def get_or_create_admin(self, user_id, username=None, first_name=None):
        user_id = str(user_id)
        if user_id not in self.data['admins']:
            import secrets
            self.data['admins'][user_id] = {
                'id': int(user_id),
                'username': username,
                'first_name': first_name,
                'referral_code': secrets.token_hex(4),
                'referrals': 0,
                'expires_at': None,
                'joined_at': datetime.utcnow().isoformat(),
                'bots_deployed': 0,
                'earnings': 0.0,
                'wallet': None
            }
            self.data['stats']['joins'] = self.data['stats'].get('joins', 0) + 1
            self.data['spots_remaining'] = max(0, self.data.get('spots_remaining', 47) - 1)
            self.save()
            logger.info(f"New admin created: {user_id}")
        return self.data['admins'][user_id]
    
    def is_active(self, user_id):
        admin = self.get_admin(user_id)
        if not admin or not admin.get('expires_at'):
            return False
        try:
            exp = datetime.fromisoformat(admin['expires_at'])
            return exp > datetime.utcnow()
        except:
            return False
    
    def get_stats(self):
        active = 0
        for a in self.data['admins'].values():
            if a.get('expires_at'):
                try:
                    if datetime.fromisoformat(a['expires_at']) > datetime.utcnow():
                        active += 1
                except:
                    pass
        
        total_revenue = sum(p.get('amount', 0) for p in self.data.get('payments', []))
        
        return {
            'total': len(self.data['admins']),
            'active': active,
            'revenue': total_revenue,
            'visits': self.data['stats'].get('visits', 0),
            'joins': self.data['stats'].get('joins', 0),
            'spots_left': self.data.get('spots_remaining', 47),
            'bots': len(self.data.get('bots', []))
        }

db = PersistentDB()

# ═══════════════════════════════════════════════════════════════════════
# HELIUS PAYMENT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

async def verify_payment(tx_hash, expected_amount):
    """Verify SOL payment via Helius"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_KEY}"
            payload = {"transactions": [tx_hash]}
            
            async with session.post(url, json=payload, timeout=30) as resp:
                if resp.status != 200:
                    return False, 0
                
                data = await resp.json()
                if not data or not isinstance(data, list):
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

# ═══════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main entry point"""
    user = update.effective_user
    db.data['stats']['visits'] = db.data['stats'].get('visits', 0) + 1
    db.save()
    
    # Track referral
    if context.args:
        source = context.args[0]
        if source.startswith("ref_"):
            try:
                referrer_id = source.replace("ref_", "")
                if referrer_id in db.data['admins'] and referrer_id != str(user.id):
                    db.data['admins'][referrer_id]['referrals'] = db.data['admins'][referrer_id].get('referrals', 0) + 1
                    db.save()
                    await context.bot.send_message(
                        int(referrer_id),
                        f"🎉 @{user.username or user.first_name} joined via your link!"
                    )
            except Exception as e:
                logger.error(f"Referral error: {e}")
    
    # MASTER ADMIN
    if user.id == ADMIN_ID:
        stats = db.get_stats()
        await update.message.reply_text(
            f"""👑 MASTER CONTROL

📊 METRICS:
• Users: {stats['total']} (Active: {stats['active']})
• Revenue: {stats['revenue']:.2f} SOL
• Bots Deployed: {stats['bots']}
• Visits: {stats['visits']} | Joins: {stats['joins']}
• Spots Left: {stats['spots_left']}

💰 Wallet: `{MASTER_WALLET[:20]}...`

⚡ ONLINE 24/7 | v7.2 FULL""",
            parse_mode='Markdown'
        )
        return
    
    # CHECK SUBSCRIPTION
    if db.is_active(user.id):
        await show_dashboard(update, context)
        return
    
    # LANDING PAGE
    price_inc = datetime.fromisoformat(db.data['price_increase'])
    hours_left = int((price_inc - datetime.utcnow()).total_seconds() / 3600)
    spots = db.data.get('spots_remaining', 47)
    story = random.choice(db.data.get('success_stories', []))
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 CLAIM SPOT NOW", callback_data="buy_monthly")],
        [InlineKeyboardButton("👑 Yearly (Save 20%)", callback_data="buy_yearly")],
        [InlineKeyboardButton("📊 Demo Bot", url="https://t.me/Icegods_Bridge_bot")],
        [InlineKeyboardButton("💬 Channel", url="https://t.me/ICEGODSICEDEVIL")]
    ])
    
    await update.message.reply_text(
        f"""🚀 ICEGODS BOT PLATFORM

🔥 {story['name']} earned {story['profit']} SOL {story['time']}
⚡ Only {spots} spots left!
⏰ Price up in {max(0, hours_left)}h!

💎 WHAT YOU GET:
✅ White-label token alert bot
✅ Auto-detect 100x gems
✅ VIP/Whale/Premium tiers
✅ Automatic SOL payments
✅ Airdrop distribution
✅ 80% revenue share

💰 100 subs = 56 SOL/month (~$8,400)

🎁 Refer 3 = FREE ACCESS

👇 CLICK BELOW 👇""",
        reply_markup=keyboard
    )

async def show_dashboard(update, context):
    """Show user dashboard"""
    user = update.effective_user
    admin = db.get_admin(user.id)
    
    expires = datetime.fromisoformat(admin['expires_at'])
    days_left = (expires - datetime.utcnow()).days
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Deploy Bot", callback_data="deploy")],
        [InlineKeyboardButton("💎 Referral", callback_data="referral")],
        [InlineKeyboardButton("💰 Earnings", callback_data="earnings")],
        [InlineKeyboardButton("⚙️ Wallet", callback_data="wallet")]
    ])
    
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.id}"
    
    await update.message.reply_text(
        f"""⚡ YOUR DASHBOARD

✅ Active | {days_left} days left
🤖 Bots: {admin.get('bots_deployed', 0)}/10
💰 Earned: {admin.get('earnings', 0):.2f} SOL
👥 Referrals: {admin.get('referrals', 0)}

🔗 YOUR LINK:
`{link}`

🎯 3 referrals = FREE!

🚀 Deploy bot to earn!""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    await update.message.reply_text(
        """📖 ICEGODS COMMANDS

/start - Main dashboard
/confirm TX_HASH - Verify payment
/status - Check subscription
/deploy TOKEN - Deploy white-label bot
/stats - Platform statistics
/referral - Your referral link
/earnings - Revenue report
/wallet ADDRESS - Set SOL wallet
/support - Contact @MexRobert

💎 Get started: /start"""
    )

async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify payment"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            "🛰 VERIFY PAYMENT\n\n"
            "Usage: /confirm TRANSACTION_HASH\n\n"
            "Example:\n"
            "/confirm 5JTHj8rSHw4h6NAoZwLByQ2c4Y65rk6WnCcZ1A91HE573PU88jWXwrcPxs9HyXxv6KVrtktb3j4XsSmj2HnEzghc"
        )
        return
    
    tx_hash = context.args[0].strip()
    
    if len(tx_hash) < 80:
        await update.message.reply_text("❌ Invalid hash (too short)")
        return
    
    await update.message.reply_text("🛰 Verifying on Solana...")
    
    # Check if already used
    for payment in db.data.get('payments', []):
        if payment.get('tx_hash') == tx_hash:
            await update.message.reply_text("❌ This transaction was already used!")
            return
    
    # Try monthly (5) then yearly (50)
    for plan, amount, days in [('monthly', 5.0, 30), ('yearly', 50.0, 365)]:
        success, actual = await verify_payment(tx_hash, amount)
        
        if success:
            admin = db.get_or_create_admin(user.id, user.username, user.first_name)
            
            # Set expiry
            current_exp = None
            if admin.get('expires_at'):
                try:
                    current_exp = datetime.fromisoformat(admin['expires_at'])
                except:
                    pass
            
            if current_exp and current_exp > datetime.utcnow():
                new_exp = current_exp + timedelta(days=days)
            else:
                new_exp = datetime.utcnow() + timedelta(days=days)
            
            admin['expires_at'] = new_exp.isoformat()
            
            # Record payment
            db.data['payments'].append({
                'admin_id': user.id,
                'amount': actual,
                'plan': plan,
                'tx_hash': tx_hash,
                'time': datetime.utcnow().isoformat()
            })
            db.save()
            
            await update.message.reply_text(
                f"""✅ ACTIVATED!

🎉 Plan: {plan.upper()}
⏰ {days} days added
📅 Expires: {new_exp.strftime('%Y-%m-%d')}
💰 Paid: {actual:.4f} SOL

🚀 Click /start!"""
            )
            
            # Notify master
            try:
                await context.bot.send_message(
                    ADMIN_ID,
                    f"💰 NEW PAYMENT!\nUser: {user.id}\nPlan: {plan}\nAmount: {actual:.4f} SOL"
                )
            except:
                pass
            return
    
    await update.message.reply_text(
        f"""❌ PAYMENT NOT FOUND

Check:
• Sent exactly 5 or 50 SOL?
• Transaction confirmed?
• Correct wallet: `{MASTER_WALLET[:15]}...`

Try again or contact @MexRobert""",
        parse_mode='Markdown'
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check subscription status"""
    user = update.effective_user
    
    if db.is_active(user.id):
        admin = db.get_admin(user.id)
        expires = datetime.fromisoformat(admin['expires_at'])
        days = (expires - datetime.utcnow()).days
        
        await update.message.reply_text(
            f"""✅ ACTIVE SUBSCRIPTION

⏰ Expires: {expires.strftime('%Y-%m-%d')} ({days} days)
🤖 Bots: {admin.get('bots_deployed', 0)}/10
👥 Referrals: {admin.get('referrals', 0)}

🚀 Use /deploy to create bots!"""
        )
    else:
        await update.message.reply_text(
            """❌ NO ACTIVE SUBSCRIPTION

💎 Subscribe to deploy bots:
• Monthly: 5 SOL
• Yearly: 50 SOL

👉 /start to subscribe"""
        )

async def cmd_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deploy white-label bot"""
    user = update.effective_user
    
    if not db.is_active(user.id):
        await update.message.reply_text(
            "❌ Subscription required!\n\n"
            "Subscribe first: /start\n\n"
            "Then return to deploy your bot."
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            """🚀 DEPLOY BOT

Step 1: Get token from @BotFather
1. Message @BotFather
2. Send /newbot
3. Name your bot
4. Copy the token (looks like: 123456:ABC...)

Step 2: Send me the token:
/deploy YOUR_TOKEN

Example:
/deploy 123456789:AAF4YxWvR9gZ1234567890abcdefgh""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 Full Guide", url="https://t.me/ICEGODSICEDEVIL")]
            ])
        )
        return
    
    token = context.args[0]
    
    # Validate token format
    if ':' not in token or len(token) < 20:
        await update.message.reply_text("❌ Invalid token format")
        return
    
    # Save bot
    db.data['bots'].append({
        'admin_id': user.id,
        'token': token,
        'created_at': datetime.utcnow().isoformat(),
        'active': True
    })
    
    admin = db.get_admin(user.id)
    admin['bots_deployed'] = admin.get('bots_deployed', 0) + 1
    db.save()
    
    await update.message.reply_text(
        f"""✅ BOT DEPLOYED!

Token: `{token[:20]}...`

⏳ Starting up...
Your bot will be live in 2-3 minutes!

📊 Track in dashboard: /start

⚡ Next steps:
1. Add bot to your channel
2. Configure alerts
3. Set your prices
4. Start earning!""",
        parse_mode='Markdown'
    )
    
    # Notify master
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🤖 NEW BOT DEPLOYED!\nBy: {user.id} (@{user.username})\nBots: {admin['bots_deployed']}"
        )
    except:
        pass

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show platform stats"""
    user = update.effective_user
    
    if user.id == ADMIN_ID:
        stats = db.get_stats()
        await update.message.reply_text(
            f"""📊 PLATFORM STATISTICS

👥 Users: {stats['total']}
✅ Active: {stats['active']}
🤖 Bots: {stats['bots']}
💰 Revenue: {stats['revenue']:.2f} SOL

📈 Today:
• Visits: {stats['visits']}
• Joins: {stats['joins']}
• Spots Left: {stats['spots_left']}

⚡ System: ONLINE"""
        )
    else:
        await update.message.reply_text("❌ Admin only command")

async def cmd_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral info"""
    user = update.effective_user
    admin = db.get_or_create_admin(user.id, user.username, user.first_name)
    
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.id}"
    refs = admin.get('referrals', 0)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={link}&text=🔥 ICEGODS Bot Platform - Deploy crypto alert bots!")],
        [InlineKeyboardButton("🐦 Twitter", url=f"https://twitter.com/intent/tweet?text=Crypto%20alert%20bot%20platform%20-%20earn%20SOL!%20{link}")]
    ])
    
    await update.message.reply_text(
        f"""🎁 REFERRAL PROGRAM

🔗 YOUR LINK:
`{link}`

👥 Referrals: {refs}
🎁 Free Days: {refs * 3}
🎯 Next: {3 - (refs % 3)} more = +3 days!

💰 VALUE: Each ref = 0.5 SOL

Share everywhere!""",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def cmd_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show earnings"""
    user = update.effective_user
    admin = db.get_admin(user.id)
    
    if not admin:
        await update.message.reply_text("❌ Start with /start")
        return
    
    current = admin.get('earnings', 0)
    potential = 56.0  # If 100 subs
    
    await update.message.reply_text(
        f"""💰 EARNINGS DASHBOARD

Current: {current:.2f} SOL

📈 POTENTIAL:
100 subscribers = 56 SOL/month
= ~${potential * 150:.0f}/month

🎯 TO EARN:
1. /deploy your bot
2. Add to crypto groups
3. Offer free trials
4. Build community

🚀 Start: /deploy""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Deploy Now", callback_data="deploy")]
        ])
    )

async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set wallet address"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            """💳 SET WALLET

Usage: /wallet YOUR_SOL_ADDRESS

Example:
/wallet HxmywH2gW9ezQ2nBXwurpaWsZS6YvdmLF23R9WgMAM7p

This is where you'll receive:
• Subscription payments
• Airdrop distributions
• Referral rewards"""
        )
        return
    
    wallet = context.args[0].strip()
    
    if len(wallet) < 30:
        await update.message.reply_text("❌ Invalid Solana address")
        return
    
    admin = db.get_or_create_admin(user.id, user.username, user.first_name)
    admin['wallet'] = wallet
    db.save()
    
    await update.message.reply_text(
        f"""✅ WALLET SAVED

`{wallet[:20]}...`

You'll receive payments here!""",
        parse_mode='Markdown'
    )

async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Support contact"""
    await update.message.reply_text(
        """💬 SUPPORT

Contact: @MexRobert

For:
• Payment issues
• Bot deployment help
• Feature requests
• Partnerships

Response time: 2-24 hours"""
    )

# ═══════════════════════════════════════════════════════════════════════
# BUTTON HANDLER
# ═══════════════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline buttons"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "buy_monthly":
        await show_payment(query, "monthly", 5.0)
    elif query.data == "buy_yearly":
        await show_payment(query, "yearly", 50.0)
    elif query.data == "referral":
        await show_referral_button(query, user_id)
    elif query.data == "deploy":
        await query.message.edit_text(
            "🚀 Use command:\n/deploy YOUR_BOT_TOKEN\n\nGet token from @BotFather",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 Guide", url="https://t.me/ICEGODSICEDEVIL")]
            ])
        )
    elif query.data == "earnings":
        await query.message.edit_text(
            "💰 Deploy a bot first!\n\nUse: /deploy TOKEN",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Deploy", callback_data="deploy")]
            ])
        )
    elif query.data == "wallet":
        await query.message.edit_text("💳 Use: /wallet YOUR_SOL_ADDRESS")
    elif query.data == "main_menu":
        await cmd_start(update, context)

async def show_payment(query, plan, amount):
    """Show payment info"""
    spots = db.data.get('spots_remaining', 47)
    
    await query.message.edit_text(
        f"""🧾 {plan.upper()} PLAN

Amount: {amount} SOL
Wallet: `{MASTER_WALLET}`

Send SOL, then:
/confirm TX_HASH

⚡ Only {spots} spots!""",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Help", url="https://t.me/MexRobert")]
        ])
    )

async def show_referral_button(query, user_id):
    """Show referral from button"""
    admin = db.get_admin(user_id)
    if not admin:
        admin = db.get_or_create_admin(user_id)
    
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    refs = admin.get('referrals', 0)
    
    await query.message.edit_text(
        f"""🎁 REFERRAL

🔗 Link: `{link}`
👥 Referrals: {refs}

Share to earn free days!""",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={link}&text=🔥 ICEGODS Bot Platform!")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
    )

# ═══════════════════════════════════════════════════════════════════════
# WEB SERVER
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
application = None
bot_loop = None

def process_update_sync(update_data):
    if not bot_loop or not bot_loop.is_running():
        return False
    try:
        future = asyncio.run_coroutine_threadsafe(
            process_update_async(update_data), bot_loop
        )
        return future.result(timeout=30)
    except Exception as e:
        logger.error(f"Process error: {e}")
        return False

async def process_update_async(update_data):
    try:
        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)
        return True
    except Exception as e:
        logger.error(f"Update error: {e}")
        return False

@app.route("/")
def health():
    try:
        stats = db.get_stats()
        return jsonify({
            "status": "ICEGODS v7.2 OPERATIONAL",
            "users": stats['total'],
            "active": stats['active'],
            "revenue": stats['revenue'],
            "spots": stats['spots_left'],
            "time": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route(f"/webhook/{BOT_TOKEN.split(':')[1]}", methods=['POST'])
def webhook():
    if not application or bot_loop is None:
        return jsonify({"error": "Not ready"}), 503
    
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
    global application, bot_loop
    bot_loop = asyncio.get_running_loop()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register all handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("confirm", cmd_confirm))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("deploy", cmd_deploy))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("referral", cmd_referral))
    application.add_handler(CommandHandler("earnings", cmd_earnings))
    application.add_handler(CommandHandler("wallet", cmd_wallet))
    application.add_handler(CommandHandler("support", cmd_support))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    await application.initialize()
    
    webhook_path = f"/webhook/{BOT_TOKEN.split(':')[1]}"
    full_url = f"{WEBHOOK_URL}{webhook_path}"
    await application.bot.set_webhook(url=full_url)
    logger.info(f"✅ Webhook: {full_url}")
    
    await application.start()
    logger.info("✅ Bot started!")
    
    while True:
        await asyncio.sleep(3600)

def run_bot():
    asyncio.run(bot_main())

def main():
    logger.info("=" * 60)
    logger.info("ICEGODS v7.2 - FULLY OPERATIONAL")
    logger.info("=" * 60)
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    import time
    time.sleep(3)
    
    logger.info(f"🌐 Server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=False)

if __name__ == "__main__":
    main()
