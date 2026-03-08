#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
AIRDROP MANAGER - Automatic Token Distribution System
Handles scheduled airdrops, eligibility checks, and Solana transfers
═══════════════════════════════════════════════════════════════════════════
"""

import os
import logging
import aiohttp
import asyncio
from datetime import datetime
from database import SessionLocal, Airdrop, Subscriber, Admin

logger = logging.getLogger(__name__)

HELIUS_KEY = os.getenv("HELIUS_API_KEY")
MASTER_WALLET = os.getenv("MASTER_WALLET")

class AirdropManager:
    def __init__(self):
        self.helius_url = f"https://api.helius.xyz/v0"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_airdrop(self, admin_id, token_address, token_symbol, total_amount, 
                            vip_amount=100, whale_amount=500, premium_amount=1000,
                            schedule_minutes=0):
        """Create new airdrop campaign"""
        db = SessionLocal()
        try:
            scheduled_time = datetime.utcnow()
            if schedule_minutes > 0:
                from datetime import timedelta
                scheduled_time += timedelta(minutes=schedule_minutes)
            
            airdrop = Airdrop(
                admin_id=admin_id,
                token_address=token_address,
                token_symbol=token_symbol,
                total_amount=total_amount,
                per_vip_amount=vip_amount,
                per_whale_amount=whale_amount,
                per_premium_amount=premium_amount,
                scheduled_at=scheduled_time,
                status='scheduled' if schedule_minutes > 0 else 'pending'
            )
            db.add(airdrop)
            db.commit()
            db.refresh(airdrop)
            
            logger.info(f"✅ Airdrop created: {airdrop.id} for {token_symbol}")
            return airdrop.id
        finally:
            db.close()
    
    async def get_eligible_subscribers(self, admin_id):
        """Get all paid subscribers across all admin's bots"""
        db = SessionLocal()
        try:
            # Get all bots for this admin
            admin = db.query(Admin).filter(Admin.telegram_id == admin_id).first()
            if not admin:
                return []
            
            eligible = []
            for bot in admin.client_bots:
                for sub in bot.subscribers:
                    if sub.tier in ['vip', 'whale', 'premium'] and sub.wallet_address:
                        # Check if subscription is active
                        if sub.expires_at and sub.expires_at > datetime.utcnow():
                            eligible.append({
                                'telegram_id': sub.telegram_id,
                                'tier': sub.tier,
                                'wallet': sub.wallet_address,
                                'bot_username': bot.bot_username
                            })
            
            return eligible
        finally:
            db.close()
    
    async def execute_airdrop(self, airdrop_id):
        """Execute the airdrop distribution"""
        db = SessionLocal()
        try:
            airdrop = db.query(Airdrop).filter(Airdrop.id == airdrop_id).first()
            if not airdrop or airdrop.status != 'pending':
                return False, "Invalid or already processed"
            
            eligible = await self.get_eligible_subscribers(airdrop.admin_id)
            if not eligible:
                airdrop.status = 'cancelled'
                db.commit()
                return False, "No eligible subscribers"
            
            airdrop.status = 'executing'
            airdrop.total_recipients = len(eligible)
            db.commit()
            
            # Calculate amounts per tier
            tier_amounts = {
                'vip': airdrop.per_vip_amount,
                'whale': airdrop.per_whale_amount,
                'premium': airdrop.per_premium_amount
            }
            
            successful = 0
            failed = 0
            
            for recipient in eligible:
                amount = tier_amounts.get(recipient['tier'], 0)
                if amount > 0:
                    # In production, this would call Solana transfer
                    # For now, simulate success (integrate Phantom/ Solana Pay)
                    success = await self._send_tokens(
                        recipient['wallet'],
                        airdrop.token_address,
                        amount
                    )
                    
                    if success:
                        successful += 1
                        # Update subscriber stats
                        sub = db.query(Subscriber).filter(
                            Subscriber.telegram_id == recipient['telegram_id']
                        ).first()
                        if sub:
                            sub.total_airdrops_received += 1
                            sub.last_airdrop_at = datetime.utcnow()
                    else:
                        failed += 1
            
            airdrop.status = 'completed'
            airdrop.successful_sends = successful
            airdrop.failed_sends = failed
            airdrop.executed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"✅ Airdrop {airdrop_id} completed: {successful}/{len(eligible)}")
            return True, f"Sent to {successful} recipients"
            
        finally:
            db.close()
    
    async def _send_tokens(self, to_wallet, token_address, amount):
        """Send tokens via Helius/ Solana - PLACEHOLDER for real implementation"""
        # TODO: Integrate with Solana web3.py or Helius transfer API
        # This requires private key management - use AWS KMS or similar in production
        logger.info(f"Would send {amount} tokens to {to_wallet}")
        return True  # Simulate success
    
    async def get_airdrop_stats(self, admin_id):
        """Get stats for admin's airdrops"""
        db = SessionLocal()
        try:
            airdrops = db.query(Airdrop).filter(Airdrop.admin_id == admin_id).all()
            return [{
                'id': a.id,
                'token': a.token_symbol,
                'status': a.status,
                'recipients': a.total_recipients,
                'successful': a.successful_sends,
                'date': a.executed_at or a.scheduled_at
            } for a in airdrops]
        finally:
            db.close()

# Background task runner
async def run_airdrop_scheduler():
    """Background task to check and execute scheduled airdrops"""
    while True:
        try:
            db = SessionLocal()
            pending = db.query(Airdrop).filter(
                Airdrop.status == 'scheduled',
                Airdrop.scheduled_at <= datetime.utcnow()
            ).all()
            
            for airdrop in pending:
                airdrop.status = 'pending'
                db.commit()
                
                async with AirdropManager() as manager:
                    await manager.execute_airdrop(airdrop.id)
            
            db.close()
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Airdrop scheduler error: {e}")
            await asyncio.sleep(60)

