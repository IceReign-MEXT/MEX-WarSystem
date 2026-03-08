#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
GROUP MONITOR & AUTO-RECRUITMENT ENGINE
Automatically detects groups, welcomes users, converts to subscribers
═══════════════════════════════════════════════════════════════════════════
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import SessionLocal, ClientBot, Subscriber

logger = logging.getLogger(__name__)

class GroupMonitor:
    def __init__(self, bot_app):
        self.app = bot_app
        self.welcome_delay = 30  # Seconds before welcome message
    
    async def on_bot_added(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Triggered when bot is added to a group"""
        chat = update.effective_chat
        bot_member = update.effective_user
        
        if bot_member.id != context.bot.id:
            return  # Not our bot being added
        
        logger.info(f"🆕 Bot added to group: {chat.id} ({chat.title})")
        
        # Send setup instructions to group admins
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Setup Bot", url=f"https://t.me/{context.bot.username}?start=setup_{chat.id}")],
            [InlineKeyboardButton("📖 Documentation", url="https://t.me/CHINACRYPTOCROSSCHAINSNETWORKS")]
        ])
        
        await context.bot.send_message(
            chat.id,
            f"""🚀 ICEGODS Bot Activated in {chat.title}!

I'm a professional token alert bot with:
✅ Auto-detect new launches
✅ VIP/Whale/Premium tiers  
✅ Automatic airdrops
✅ Revenue sharing (80% to owner)

👑 Group Owner: Click "Setup Bot" to configure and start earning!

💬 Support: @MexRobert""",
            reply_markup=keyboard
        )
        
        # Notify master admin
        try:
            master_id = int(os.getenv("ADMIN_ID"))
            await context.bot.send_message(
                master_id,
                f"🆕 Bot added to group:\n"
                f"Name: {chat.title}\n"
                f"ID: {chat.id}\n"
                f"Members: {await self.get_member_count(context.bot, chat.id)}"
            )
        except Exception as e:
            logger.error(f"Failed to notify master: {e}")
    
    async def on_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome new members with conversion funnel"""
        chat = update.effective_chat
        new_members = update.message.new_chat_members
        
        for member in new_members:
            if member.is_bot:
                continue
            
            # Delayed welcome (don't spam immediately)
            await asyncio.sleep(self.welcome_delay)
            
            # Check if already subscriber
            db = SessionLocal()
            try:
                existing = db.query(Subscriber).filter(
                    Subscriber.telegram_id == member.id
                ).first()
                
                if existing:
                    continue  # Already in system
                
                # Send personalized welcome
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 Get VIP Alerts", url=f"https://t.me/{context.bot.username}?start=vip_{chat.id}")],
                    [InlineKeyboardButton("💎 Join Premium", url=f"https://t.me/{context.bot.username}?start=premium_{chat.id}")],
                    [InlineKeyboardButton("❓ How It Works", callback_data="explain_tiers")]
                ])
                
                await context.bot.send_message(
                    chat.id,
                    f"""👋 Welcome @{member.username or member.first_name}!

🔥 Want early access to 100x token launches?

This bot detects new tokens automatically:
• Before they pump 100x
• Before whales buy in  
• Before Twitter knows

💎 VIP: 0.5 SOL/month (Basic alerts)
🥈 Whale: 1 SOL/month (Early access)
💎 Premium: 2.5 SOL/month (Instant alerts + airdrops)

⚡ Click below to subscribe 👇""",
                    reply_markup=keyboard,
                    reply_to_message_id=update.message.message_id
                )
                
                logger.info(f"👋 Welcomed {member.id} in {chat.id}")
                
            finally:
                db.close()
    
    async def get_member_count(self, bot, chat_id):
        """Get group member count"""
        try:
            count = await bot.get_chat_member_count(chat_id)
            return count
        except:
            return "Unknown"
    
    async def broadcast_to_groups(self, message: str, bot_token: str, exclude=None):
        """Send message to all groups where bot is active"""
        db = SessionLocal()
        try:
            bot = db.query(ClientBot).filter(ClientBot.bot_token == bot_token).first()
            if not bot:
                return
            
            # Get all groups this bot manages
            # This would need additional tracking in database
            pass
            
        finally:
            db.close()

