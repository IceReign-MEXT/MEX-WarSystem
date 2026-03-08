#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
TRAFFIC ENGINE - Twitter + Telegram Auto-Growth
Posts signals, joins groups, DMs prospects automatically
═══════════════════════════════════════════════════════════════════════════
"""

import os
import asyncio
import logging
import random
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# TWITTER/X AUTO-POSTER
# ═══════════════════════════════════════════════════════════════════════

class TwitterPoster:
    def __init__(self):
        self.webhook_url = os.getenv("TWITTER_WEBHOOK")  # Or use Twitter API
        self.post_interval = 3600  # 1 hour
        self.hashtags = [
            "#Solana", "#Crypto", "#Altcoins", "#100x", "#Gems", 
            "#DeFi", "#Web3", "#Trading", "#Signals", "#Airdrops"
        ]
    
    async def generate_tweet(self):
        """Generate viral tweet content"""
        templates = [
            "🔥 NEW TOKEN ALERT\n\nJust detected: {token}\nMC: ${mc}K | Liq: ${liq}K\n\nEarly entry = Early profit\n\nJoin our bot for instant alerts:\nhttps://t.me/{bot}\n\n{hashtags}",
            
            "💎 {token} is pumping!\n\n+{gain}% in {time}\nDetected before Twitter knew about it\n\nDon't miss the next one:\nhttps://t.me/{bot}\n\n{hashtags}",
            
            "🚀 How I caught {token} at ${price}K MC\n\nNow at ${current}K MC\nThat's {x}x in {hours} hours\n\nMy secret? This bot:\nhttps://t.me/{bot}\n\n{hashtags}",
            
            "⚡ 3 tokens I found this week:\n1. {token1} - {x1}x\n2. {token2} - {x2}x  \n3. {token3} - {x3}x\n\nAll from one bot:\nhttps://t.me/{bot}\n\n{hashtags}",
        ]
        
        # Fake data for demo (replace with real detections)
        data = {
            'token': random.choice(['$BONK', '$WIF', '$PEPE', '$DOGE', '$SHIB']),
            'mc': random.randint(100, 500),
            'liq': random.randint(50, 200),
            'gain': random.randint(50, 500),
            'time': random.choice(['10min', '1h', '3h', '6h']),
            'price': random.randint(50, 200),
            'current': random.randint(300, 1000),
            'x': random.randint(3, 20),
            'hours': random.randint(2, 24),
            'token1': '$BONK', 'x1': random.randint(2, 10),
            'token2': '$WIF', 'x2': random.randint(3, 15),
            'token3': '$PEPE', 'x3': random.randint(5, 20),
            'bot': os.getenv('BOT_USERNAME', 'ICEMEXWarSystem_Bot'),
            'hashtags': ' '.join(random.sample(self.hashtags, 3))
        }
        
        template = random.choice(templates)
        return template.format(**data)
    
    async def post_loop(self):
        """Auto-post to Twitter every hour"""
        while True:
            try:
                tweet = await self.generate_tweet()
                logger.info(f"🐦 Tweeting: {tweet[:50]}...")
                
                # Here you would post via Twitter API
                # For now, log it (you can copy/paste to Twitter)
                print(f"\n{'='*60}\nTWEET READY:\n{tweet}\n{'='*60}\n")
                
                await asyncio.sleep(self.post_interval)
                
            except Exception as e:
                logger.error(f"Twitter error: {e}")
                await asyncio.sleep(3600)

# ═══════════════════════════════════════════════════════════════════════
# TELEGRAM GROUP AUTO-GROWTH
# ═══════════════════════════════════════════════════════════════════════

class TelegramGrowth:
    def __init__(self, bot_app):
        self.app = bot_app
        self.target_groups = [
            "@solana_traders",
            "@defi_alerts", 
            "@crypto_signals",
            "@altcoin_gems",
            "@whale_alerts"
        ]
        self.dm_templates = [
            "Hey! I saw you're into crypto. I built a bot that detects 100x tokens before they pump. Want early access? https://t.me/{bot}",
            
            "Hi! Noticed you're in trading groups. I made something that finds gems early - 80% revenue share for bot owners. Check it: https://t.me/{bot}",
            
            "👋 Crypto trader? I automated token detection with AI. Made 45 SOL last month. Deploy your own: https://t.me/{bot}",
        ]
    
    async def growth_loop(self):
        """Auto-join groups and DM active members"""
        while True:
            try:
                for group in self.target_groups:
                    logger.info(f"🎯 Targeting {group}")
                    
                    # Strategy 1: Post in group (if allowed)
                    try:
                        msg = await self.generate_group_post()
                        # await self.app.bot.send_message(group, msg)  # Uncomment when ready
                        logger.info(f"Would post to {group}: {msg[:50]}...")
                    except Exception as e:
                        logger.error(f"Can't post to {group}: {e}")
                    
                    # Strategy 2: DM recent joiners (aggressive)
                    # This requires the bot to be admin or have user list
                    # Use with caution - can get banned
                    
                    await asyncio.sleep(300)  # 5 min between groups
                
                await asyncio.sleep(3600)  # Wait 1 hour before next round
                
            except Exception as e:
                logger.error(f"Growth error: {e}")
                await asyncio.sleep(3600)
    
    async def generate_group_post(self):
        """Generate post for Telegram groups"""
        templates = [
            "🔥 Just caught {token} at {mc}K MC\nNow at {current}K MC ({x}x)\n\nHow? Auto-detection bot\nDeploy yours: https://t.me/{bot}\n\nDM me for free trial 👆",
            
            "💎 Found {token} before it pumped {gain}%\n\nThis bot scans DexScreener 24/7:\nhttps://t.me/{bot}\n\n80% revenue to bot owners\nLimited spots 🔥",
            
            "🚀 Anyone want passive SOL income?\n\nI deploy alert bots that earn while I sleep\nMade {profit} SOL this month\n\nStart here: https://t.me/{bot}\n\nFirst 10 get discount 👇"
        ]
        
        data = {
            'token': random.choice(['$BONK', '$WIF', '$PEPE']),
            'mc': random.randint(50, 200),
            'current': random.randint(300, 800),
            'x': random.randint(3, 15),
            'gain': random.randint(50, 400),
            'profit': random.randint(20, 150),
            'bot': os.getenv('BOT_USERNAME', 'ICEMEXWarSystem_Bot')
        }
        
        return random.choice(templates).format(**data)

# ═══════════════════════════════════════════════════════════════════════
# CONTENT CALENDAR
# ═══════════════════════════════════════════════════════════════════════

class ContentCalendar:
    """Pre-written posts for your channel @ICEGODSICEDEVIL"""
    
    POSTS = [
        {
            "time": "09:00",
            "text": """🌅 GOOD MORNING TRADERS

☕ Coffee + Signals = Profit

Today's early detections:
🔍 Scanning DexScreener...
🔍 Monitoring liquidity...
🔍 Tracking whale wallets...

🤖 Want instant alerts?
Deploy your own bot:
https://t.me/ICEMEXWarSystem_Bot

⚡ Only 47 spots left!"""
        },
        {
            "time": "14:00", 
            "text": """💎 SUCCESS STORY

@CryptoWhale deployed their bot 30 days ago:
• 127 VIP subscribers
• 45 SOL earned
• 3 hours of work total

"I set it up and forgot about it. Money just comes in."

🚀 Start your journey:
https://t.me/ICEMEXWarSystem_Bot

👑 What will YOU build?"""
        },
        {
            "time": "20:00",
            "text": """🔥 EVENING ALERTS

Market heating up! 
3 new launches detected in last 2 hours:

1. $XXX - 50K MC, 200K liq
2. $YYY - 30K MC, 150K liq  
3. $ZZZ - 80K MC, 400K liq

💰 Early birds catch 100x's

Get tomorrow's alerts first:
https://t.me/ICEMEXWarSystem_Bot

⏰ Price increases in 8 hours!"""
        }
    ]
    
    async def post_to_channel(self, bot, channel="@ICEGODSICEDEVIL"):
        """Post scheduled content"""
        for post in self.POSTS:
            try:
                await bot.send_message(channel, post["text"])
                logger.info(f"Posted to {channel}")
                await asyncio.sleep(3600)  # Wait between posts
            except Exception as e:
                logger.error(f"Post failed: {e}")

