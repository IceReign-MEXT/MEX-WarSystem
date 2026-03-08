#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
TOKEN DETECTION ENGINE - Automatic New Launch Detection
Integrates with DexScreener + Helius to detect 100x opportunities
═══════════════════════════════════════════════════════════════════════════
"""

import os
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database import SessionLocal, ClientBot, TokenDetection, Subscriber

logger = logging.getLogger(__name__)

DEXSCREENER_API = "https://api.dexscreener.com/latest"
HELIUS_KEY = os.getenv("HELIUS_API_KEY")

class TokenDetector:
    def __init__(self):
        self.session = None
        self.known_tokens = set()  # In-memory cache
        self.last_check = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_new_pairs(self, chain: str = "solana", limit: int = 50) -> List[Dict]:
        """Fetch recently created pairs from DexScreener"""
        try:
            url = f"{DEXSCREENER_API}/dex/pairs/{chain}"
            async with self.session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    logger.error(f"DexScreener error: {resp.status}")
                    return []
                
                data = await resp.json()
                pairs = data.get('pairs', [])
                
                # Filter for new pairs (created within last hour)
                new_pairs = []
                for pair in pairs[:limit]:
                    created_at = pair.get('pairCreatedAt', 0)
                    if created_at:
                        created_time = datetime.fromtimestamp(created_at / 1000)
                        if datetime.utcnow() - created_time < timedelta(hours=1):
                            new_pairs.append(pair)
                
                return new_pairs
                
        except Exception as e:
            logger.error(f"Error fetching pairs: {e}")
            return []
    
    async def analyze_token(self, token_address: str) -> Optional[Dict]:
        """Deep analysis using Helius + DexScreener"""
        try:
            # Get token metadata from Helius
            helius_url = f"https://api.helius.xyz/v0/tokens/?api-key={HELIUS_KEY}"
            async with self.session.post(helius_url, json={"mintAccounts": [token_address]}) as resp:
                if resp.status == 200:
                    helius_data = await resp.json()
                else:
                    helius_data = {}
            
            # Get price data from DexScreener
            dex_url = f"{DEXSCREENER_API}/dex/tokens/{token_address}"
            async with self.session.get(dex_url, timeout=30) as resp:
                if resp.status != 200:
                    return None
                
                dex_data = await resp.json()
                pairs = dex_data.get('pairs', [])
                
                if not pairs:
                    return None
                
                # Get best pair (highest liquidity)
                best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0))
                
                liquidity = float(best_pair.get('liquidity', {}).get('usd', 0) or 0)
                market_cap = float(best_pair.get('fdv', 0) or 0)
                volume_24h = float(best_pair.get('volume', {}).get('h24', 0) or 0)
                price = float(best_pair.get('priceUsd', 0) or 0)
                
                # Scoring algorithm
                score = 0
                reasons = []
                
                if liquidity > 50000:  # $50k+ liquidity
                    score += 30
                    reasons.append("high_liquidity")
                elif liquidity > 10000:  # $10k+ liquidity
                    score += 20
                    reasons.append("good_liquidity")
                
                if market_cap < 1000000:  # Under $1M market cap
                    score += 25
                    reasons.append("early_entry")
                
                if volume_24h > liquidity * 0.5:  # High volume relative to liquidity
                    score += 20
                    reasons.append("volume_spike")
                
                # Check for socials (rug pull protection)
                info = best_pair.get('info', {})
                if info.get('websites') or info.get('socials'):
                    score += 15
                    reasons.append("has_socials")
                
                return {
                    'token_address': token_address,
                    'symbol': best_pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                    'name': best_pair.get('baseToken', {}).get('name', 'Unknown'),
                    'liquidity_usd': liquidity,
                    'market_cap_usd': market_cap,
                    'volume_24h': volume_24h,
                    'price_usd': price,
                    'dex_id': best_pair.get('dexId', 'unknown'),
                    'pair_url': best_pair.get('url', ''),
                    'score': score,
                    'reasons': reasons,
                    'is_new': True
                }
                
        except Exception as e:
            logger.error(f"Error analyzing token {token_address}: {e}")
            return None
    
    async def detect_for_bot(self, bot_config: ClientBot) -> List[Dict]:
        """Detect tokens matching specific bot criteria"""
        opportunities = []
        
        # Fetch new pairs
        pairs = await self.fetch_new_pairs(limit=20)
        
        for pair in pairs:
            token_address = pair.get('baseToken', {}).get('address')
            
            if not token_address or token_address in self.known_tokens:
                continue
            
            # Analyze token
            analysis = await self.analyze_token(token_address)
            
            if analysis and analysis['score'] >= 50:  # Minimum quality threshold
                # Check against bot's filters
                if (analysis['liquidity_usd'] >= bot_config.min_liquidity_usd and 
                    analysis['market_cap_usd'] <= bot_config.max_market_cap):
                    
                    opportunities.append(analysis)
                    self.known_tokens.add(token_address)
                    
                    # Save to database
                    db = SessionLocal()
                    try:
                        detection = TokenDetection(
                            bot_id=bot_config.id,
                            token_address=analysis['token_address'],
                            token_symbol=analysis['symbol'],
                            token_name=analysis['name'],
                            liquidity_usd=analysis['liquidity_usd'],
                            market_cap_usd=analysis['market_cap_usd'],
                            volume_24h=analysis['volume_24h'],
                            price_usd=analysis['price_usd'],
                            detection_reason=','.join(analysis['reasons'])
                        )
                        db.add(detection)
                        db.commit()
                    except Exception as e:
                        logger.error(f"Error saving detection: {e}")
                    finally:
                        db.close()
        
        return opportunities

async def run_detection_loop():
    """Background task: Continuously scan for new tokens"""
    logger.info("🚀 Token detection engine started")
    
    while True:
        try:
            db = SessionLocal()
            
            # Get all active bots
            active_bots = db.query(ClientBot).filter(
                ClientBot.is_active == True,
                ClientBot.is_deployed == True
            ).all()
            
            db.close()
            
            async with TokenDetector() as detector:
                for bot in active_bots:
                    try:
                        opportunities = await detector.detect_for_bot(bot)
                        
                        if opportunities:
                            logger.info(f"🔥 Bot {bot.id}: Found {len(opportunities)} opportunities")
                            
                            # Here you would send alerts to subscribers
                            # await send_alerts_to_subscribers(bot, opportunities)
                            
                    except Exception as e:
                        logger.error(f"Error processing bot {bot.id}: {e}")
            
            # Wait before next scan (every 2 minutes)
            await asyncio.sleep(120)
            
        except Exception as e:
            logger.error(f"Detection loop error: {e}")
            await asyncio.sleep(60)

