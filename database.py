#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
DATABASE LAYER - SQLAlchemy + Supabase PostgreSQL
Handles all persistence: admins, payments, bots, airdrops, referrals
═══════════════════════════════════════════════════════════════════════════
"""

import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")

# Handle Supabase connection pooling
if 'pooler.supabase' in DATABASE_URL:
    # Supabase requires session mode for SQLAlchemy
    DATABASE_URL = DATABASE_URL.replace('?sslmode=require', '')
    if '?' not in DATABASE_URL:
        DATABASE_URL += '?sslmode=require'

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Render/Supabase handle pooling
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ═══════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    plan_type = Column(String(20))  # monthly, yearly, lifetime
    expires_at = Column(DateTime)
    max_clients = Column(Integer, default=1)  # Starts at 1, increases with referrals
    referral_code = Column(String(20), unique=True)
    referred_by = Column(BigInteger, ForeignKey('admins.telegram_id'), nullable=True)
    referral_count = Column(Integer, default=0)
    total_earned_sol = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    payments = relationship("Payment", back_populates="admin")
    client_bots = relationship("ClientBot", back_populates="admin")
    airdrops = relationship("Airdrop", back_populates="admin")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, ForeignKey('admins.telegram_id'))
    amount_sol = Column(Float)
    plan_type = Column(String(20))
    tx_hash = Column(String(100), unique=True)
    status = Column(String(20), default='pending')  # pending, confirmed, failed
    confirmed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    admin = relationship("Admin", back_populates="payments")

class ClientBot(Base):
    __tablename__ = "client_bots"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, ForeignKey('admins.telegram_id'))
    bot_token = Column(String(200))
    bot_username = Column(String(100))
    channel_id = Column(BigInteger)
    group_id = Column(BigInteger)
    wallet_address = Column(String(50))
    
    # Pricing tiers set by admin
    vip_price = Column(Float, default=0.5)
    whale_price = Column(Float, default=1.0)
    premium_price = Column(Float, default=2.5)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deployed = Column(Boolean, default=False)
    deployed_at = Column(DateTime)
    last_ping = Column(DateTime)
    
    # Stats
    total_subscribers = Column(Integer, default=0)
    total_revenue_sol = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    admin = relationship("Admin", back_populates="client_bots")
    subscribers = relationship("Subscriber", back_populates="bot")

class Subscriber(Base):
    __tablename__ = "subscribers"
    
    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, ForeignKey('client_bots.id'))
    telegram_id = Column(BigInteger)
    tier = Column(String(20))  # free, vip, whale, premium
    expires_at = Column(DateTime)
    wallet_address = Column(String(50))  # For airdrops
    
    # Airdrop eligibility
    total_airdrops_received = Column(Integer, default=0)
    last_airdrop_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bot = relationship("ClientBot", back_populates="subscribers")

class Airdrop(Base):
    __tablename__ = "airdrops"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, ForeignKey('admins.telegram_id'))
    token_address = Column(String(50))
    token_symbol = Column(String(20))
    total_amount = Column(Float)
    per_vip_amount = Column(Float, default=100)
    per_whale_amount = Column(Float, default=500)
    per_premium_amount = Column(Float, default=1000)
    
    status = Column(String(20), default='pending')  # pending, active, completed, cancelled
    scheduled_at = Column(DateTime)
    executed_at = Column(DateTime)
    
    # Distribution tracking
    total_recipients = Column(Integer, default=0)
    successful_sends = Column(Integer, default=0)
    failed_sends = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    admin = relationship("Admin", back_populates="airdrops")

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, ForeignKey('admins.telegram_id'))
    referred_id = Column(BigInteger, ForeignKey('admins.telegram_id'))
    status = Column(String(20), default='pending')  # pending, converted, rewarded
    reward_days_added = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# ═══════════════════════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables initialized")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_admin(db, telegram_id, username=None, first_name=None):
    """Get existing admin or create new"""
    admin = db.query(Admin).filter(Admin.telegram_id == telegram_id).first()
    if not admin:
        import secrets
        referral_code = secrets.token_hex(4)
        admin = Admin(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referral_code=referral_code,
            max_clients=1  # Start with 1 bot slot
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin

def check_subscription(db, telegram_id):
    """Check if admin has active subscription"""
    admin = db.query(Admin).filter(Admin.telegram_id == telegram_id).first()
    if not admin:
        return False, None
    
    if admin.expires_at and admin.expires_at > datetime.utcnow():
        days_left = (admin.expires_at - datetime.utcnow()).days
        return True, days_left
    return False, 0

def add_referral_reward(db, admin_id, days=3):
    """Add referral reward days to admin subscription"""
    admin = db.query(Admin).filter(Admin.telegram_id == admin_id).first()
    if not admin:
        return False
    
    if admin.expires_at and admin.expires_at > datetime.utcnow():
        admin.expires_at += timedelta(days=days)
    else:
        admin.expires_at = datetime.utcnow() + timedelta(days=days)
    
    # Increase max clients every 3 referrals
    admin.referral_count += 1
    if admin.referral_count % 3 == 0:
        admin.max_clients += 1
    
    db.commit()
    return True

def get_stats(db):
    """Get platform statistics"""
    total_admins = db.query(Admin).count()
    active_admins = db.query(Admin).filter(Admin.expires_at > datetime.utcnow()).count()
    total_bots = db.query(ClientBot).count()
    active_bots = db.query(ClientBot).filter(ClientBot.is_active == True).count()
    total_revenue = db.query(Payment).filter(Payment.status == 'confirmed').with_entities(Payment.amount_sol).all()
    
    return {
        'total_admins': total_admins,
        'active_admins': active_admins,
        'total_bots': total_bots,
        'active_bots': active_bots,
        'total_revenue_sol': sum([r[0] for r in total_revenue]) if total_revenue else 0
    }

