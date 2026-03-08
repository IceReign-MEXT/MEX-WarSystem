#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
PAYMENT MONITOR & EXPIRY ALERT SYSTEM
Tracks all payments, sends reminders, auto-suspends expired accounts
═══════════════════════════════════════════════════════════════════════════
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import SessionLocal, Admin, ClientBot, Payment

logger = logging.getLogger(__name__)

class PaymentMonitor:
    def __init__(self, bot_app):
        self.app = bot_app
        self.reminder_days = [7, 3, 1]  # Days before expiry to remind
    
    async def run_monitor_loop(self):
        """Background task: Check payments daily"""
        logger.info("💰 Payment monitor started")
        
        while True:
            try:
                await self.check_expiring_subscriptions()
                await self.check_pending_payments()
                await self.check_client_bot_payments()  # Dev payments
                await asyncio.sleep(86400)  # Daily check
                
            except Exception as e:
                logger.error(f"Payment monitor error: {e}")
                await asyncio.sleep(3600)
    
    async def check_expiring_subscriptions(self):
        """Alert admins about upcoming expiry"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            
            for days in self.reminder_days:
                expiry_date = now + timedelta(days=days)
                
                expiring = db.query(Admin).filter(
                    Admin.expires_at <= expiry_date,
                    Admin.expires_at > expiry_date - timedelta(days=1),
                    Admin.is_active == True
                ).all()
                
                for admin in expiring:
                    days_left = (admin.expires_at - now).days
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("💎 Renew Now", url=f"https://t.me/{os.getenv('BOT_USERNAME')}?start=renew")],
                        [InlineKeyboardButton("📞 Support", url=f"https://t.me/{os.getenv('SUPPORT_USERNAME', 'MexRobert')}")]
                    ])
                    
                    try:
                        await self.app.bot.send_message(
                            admin.telegram_id,
                            f"""⏰ SUBSCRIPTION EXPIRING SOON!

Your admin access expires in {days_left} days!

⚠️ When expired:
• Your bots will STOP working
• Subscribers will be lost
• Revenue will pause

💎 RENEW NOW to keep earning!

Monthly: 5 SOL
Yearly: 50 SOL (Save 17%)""",
                            reply_markup=keyboard
                        )
                        logger.info(f"⏰ Sent expiry reminder to {admin.telegram_id}")
                    except Exception as e:
                        logger.error(f"Failed to notify {admin.telegram_id}: {e}")
        
        finally:
            db.close()
    
    async def check_pending_payments(self):
        """Follow up on pending payments"""
        db = SessionLocal()
        try:
            # Payments pending > 1 hour
            cutoff = datetime.utcnow() - timedelta(hours=1)
            
            pending = db.query(Payment).filter(
                Payment.status == 'pending',
                Payment.created_at < cutoff
            ).all()
            
            for payment in db.query(Admin).filter(Admin.telegram_id.in_([p.admin_id for p in pending])).all():
                try:
                    await self.app.bot.send_message(
                        payment.admin_id,
                        """⏳ PAYMENT PENDING

We noticed you started a subscription but haven't completed payment.

Need help?
• Check your wallet balance
• Verify the wallet address
• Contact support

Or click /start to try again."""
                    )
                except:
                    pass
        
        finally:
            db.close()
    
    async def check_client_bot_payments(self):
        """Monitor revenue from client bot subscribers"""
        db = SessionLocal()
        try:
            # This tracks payments made TO admins (from their subscribers)
            # And reminds admins to pay their commission to you (20%)
            
            bots = db.query(ClientBot).filter(ClientBot.is_active == True).all()
            
            for bot in bots:
                # Calculate expected commission (20% of revenue)
                expected_commission = bot.total_revenue_sol * 0.2
                
                if expected_commission > 5.0:  # Threshold to request payment
                    admin = db.query(Admin).filter(Admin.telegram_id == bot.admin_id).first()
                    
                    if admin:
                        try:
                            await self.app.bot.send_message(
                                admin.telegram_id,
                                f"""💰 COMMISSION DUE

Your bot @{bot.bot_username} has earned:
• Total Revenue: {bot.total_revenue_sol:.2f} SOL
• Your Share (80%): {bot.total_revenue_sol * 0.8:.2f} SOL
• Platform Fee (20%): {expected_commission:.2f} SOL

Please send {expected_commission:.2f} SOL to:
`{os.getenv('MASTER_WALLET')}`

Use /confirm to verify payment.

⚠️ Unpaid commissions may result in bot suspension."""
                            )
                        except:
                            pass
        
        finally:
            db.close()
    
    async def suspend_expired_accounts(self):
        """Auto-suspend expired admin accounts"""
        db = SessionLocal()
        try:
            expired = db.query(Admin).filter(
                Admin.expires_at < datetime.utcnow(),
                Admin.is_active == True
            ).all()
            
            for admin in expired:
                admin.is_active = False
                
                # Suspend all their bots
                for bot in admin.client_bots:
                    bot.is_active = False
                
                try:
                    await self.app.bot.send_message(
                        admin.telegram_id,
                        """❌ SUBSCRIPTION EXPIRED

Your account has been suspended.

To reactivate:
1. Send payment to platform wallet
2. Use /confirm TRANSACTION_HASH
3. Your bots will resume immediately

Support: @MexRobert"""
                    )
                except:
                    pass
            
            db.commit()
            logger.info(f"Suspended {len(expired)} expired accounts")
            
        finally:
            db.close()

