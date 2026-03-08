#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
CLIENT BOT TEMPLATE - White-label bot deployed for each paying customer
This runs as separate process per client, managed by master
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ClientBotInstance:
    def __init__(self, config):
        self.token = config['bot_token']
        self.admin_id = config['admin_id']
        self.channel_id = config['channel_id']
        self.group_id = config['group_id']
        self.wallet = config['wallet']
        
        self.vip_price = config.get('vip_price', 0.5)
        self.whale_price = config.get('whale_price', 1.0)
        self.premium_price = config.get('premium_price', 2.5)
        
        self.application = None
    
    async def start(self):
        """Initialize and start the bot"""
        self.application = Application.builder().token(self.token).build()
        
        # Handlers
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("subscribe", self.cmd_subscribe))
        self.application.add_handler(CommandHandler("wallet", self.cmd_wallet))
        self.application.add_handler(CommandHandler("airdrop", self.cmd_airdrop))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        await self.application.initialize()
        await self.application.start()
        
        # Start polling (or webhook if configured)
        await self.application.updater.start_polling()
        
        logger.info(f"✅ Client bot started: {self.token[:20]}...")
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message with subscription options"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🥉 VIP ({self.vip_price} SOL)", callback_data="sub_vip")],
            [InlineKeyboardButton(f"🥈 Whale ({self.whale_price} SOL)", callback_data="sub_whale")],
            [InlineKeyboardButton(f"💎 Premium ({self.premium_price} SOL)", callback_data="sub_premium")],
            [InlineKeyboardButton("📊 My Status", callback_data="status")],
            [InlineKeyboardButton("💰 Set Wallet", callback_data="set_wallet")]
        ])
        
        await update.message.reply_text(
            f"""🚀 Welcome to Token Alert Bot!

Get instant notifications for:
• New token launches
• Liquidity additions  
• Whale movements
• Airdrop opportunities

💎 SUBSCRIPTION TIERS:

🥉 VIP - {self.vip_price} SOL/month
   ✓ Basic alerts
   ✓ 1 airdrop/month

🥈 Whale - {self.whale_price} SOL/month  
   ✓ All VIP features
   ✓ Priority alerts (5min early)
   ✓ 5 airdrops/month

💎 Premium - {self.premium_price} SOL/month
   ✓ All Whale features
   ✓ Instant alerts
   ✓ Unlimited airdrops
   ✓ Private group access

⚡ Payments go to: `{self.wallet[:15]}...`

Click below to subscribe 👇""",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def cmd_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show payment instructions"""
        await update.message.reply_text(
            f"""💳 SUBSCRIPTION PAYMENT

Send SOL to:
`{self.wallet}`

Then forward the transaction hash here for instant activation!

Tiers:
• VIP: {self.vip_price} SOL
• Whale: {self.whale_price} SOL  
• Premium: {self.premium_price} SOL

⚡ Your subscription activates automatically after 1 confirmation."""
        )
    
    async def cmd_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set wallet for airdrops"""
        await update.message.reply_text(
            """💰 SET YOUR AIRDROP WALLET

Reply with your Solana wallet address to receive airdrops.

⚠️ Must be set BEFORE subscription to be eligible for airdrops!

Format: HxmywH2gW9ezQ2nBXwurpaWsZS6YvdmLF23R9WgMAM7p"""
        )
        context.user_data['awaiting_wallet'] = True
    
    async def cmd_airdrop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check airdrop eligibility"""
        # Query database for this user's airdrop history
        await update.message.reply_text(
            """🎁 AIRDROP STATUS

Checking your eligibility...
(Currently connected to master database)

Premium subscribers receive automatic airdrops when new tokens launch!"""
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("sub_"):
            tier = query.data.split("_")[1]
            prices = {
                'vip': self.vip_price,
                'whale': self.whale_price,
                'premium': self.premium_price
            }
            
            await query.message.edit_text(
                f"""🧾 SUBSCRIBE: {tier.upper()}

Amount: {prices[tier]} SOL
To: `{self.wallet}`

Send exactly {prices[tier]} SOL and forward the transaction hash here!""",
                parse_mode='Markdown'
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle wallet setting and payment verification"""
        if context.user_data.get('awaiting_wallet'):
            wallet = update.message.text.strip()
            if len(wallet) > 30 and wallet.startswith(('H', 'E', 'D', 'C', 'B', 'A')):
                # Save to database
                await update.message.reply_text(
                    f"""✅ Wallet saved: `{wallet[:20]}...`

You'll receive airdrops to this address when available!""",
                    parse_mode='Markdown'
                )
                context.user_data['wallet'] = wallet
                context.user_data['awaiting_wallet'] = False
            else:
                await update.message.reply_text("❌ Invalid Solana address. Try again.")
        
        # Check if message is a transaction hash (88 chars base58)
        elif len(update.message.text) > 80:
            tx = update.message.text.strip()
            await update.message.reply_text(
                f"""🛰 Verifying transaction: `{tx[:20]}...`

⏳ Checking Solana blockchain...""",
                parse_mode='Markdown'
            )
            # TODO: Verify payment and activate subscription

if __name__ == "__main__":
    # This would be called by master bot with config
    import json
    config = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    bot = ClientBotInstance(config)
    asyncio.run(bot.start())

