#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
DATABASE LAYER - Fixed Schema with Proper Column Definitions
═══════════════════════════════════════════════════════════════════════════
"""

import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, BigInteger, ForeignKey, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set! Check your .env file")

# Fix Supabase URL format
if 'pooler.supabase' in DATABASE_URL:
    if '?sslmode=' not in DATABASE_URL:
        DATABASE_URL += '?sslmode=require'

logger.info(f"Connecting to database...")

try:
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=False,
        connect_args={'connect_timeout': 10}
    )
    # Test connection
    with engine.connect() as conn:
        logger.info("✅ Database connection successful")
except Exception as e:
    logger.error(f"❌ Database connection failed: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ═══════════════════════════════════════════════════════════════════════
# MODELS - EXPLICIT COLUMN DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    plan_type = Column(String(20), nullable=True)  # monthly, yearly, lifetime
    expires_at = Column(DateTime, nullable=True)
    max_clients = Column(Integer, default=1, nullable=False)
    referral_code = Column(String(20), unique=True, nullable=False)
    referred_by = Column(BigInteger, ForeignKey('admins.telegram_id'), nullable=True)
    referral_count = Column(Integer, default=0, nullable=False)
    total_earned_sol = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    admin_id = Column(BigInteger, ForeignKey('admins.telegram_id'), nullable=False)
    amount_sol = Column(Float, nullable=False)
    plan_type = Column(String(20), nullable=False)
    tx_hash = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ClientBot(Base):
    __tablename__ = "client_bots"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    admin_id = Column(BigInteger, ForeignKey('admins.telegram_id'), nullable=False)
    bot_token = Column(String(200), nullable=False)
    bot_username = Column(String(100), nullable=True)
    channel_id = Column(BigInteger, nullable=True)
    group_id = Column(BigInteger, nullable=True)
    wallet_address = Column(String(50), nullable=False)
    
    # Pricing tiers
    vip_price = Column(Float, default=0.5, nullable=False)
    whale_price = Column(Float, default=1.0, nullable=False)
    premium_price = Column(Float, default=2.5, nullable=False)
    
    # Token detection settings
    target_token = Column(String(50), nullable=True)  # Token contract to monitor
    min_liquidity_usd = Column(Float, default=1000.0, nullable=False)
    max_market_cap = Column(Float, default=1000000.0, nullable=False)  # 1M default
    
    # Airdrop config
    airdrop_enabled = Column(Boolean, default=True, nullable=False)
    airdrop_vip_amount = Column(Float, default=100.0, nullable=False)
    airdrop_whale_amount = Column(Float, default=500.0, nullable=False)
    airdrop_premium_amount = Column(Float, default=1000.0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_deployed = Column(Boolean, default=False, nullable=False)
    deployed_at = Column(DateTime, nullable=True)
    last_ping = Column(DateTime, nullable=True)
    
    # Stats
    total_subscribers = Column(Integer, default=0, nullable=False)
    total_revenue_sol = Column(Float, default=0.0, nullable=False)
    total_alerts_sent = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Subscriber(Base):
    __tablename__ = "subscribers"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    bot_id = Column(Integer, ForeignKey('client_bots.id'), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    username = Column(String(100), nullable=True)
    tier = Column(String(20), default='free', nullable=False)  # free, vip, whale, premium
    expires_at = Column(DateTime, nullable=True)
    wallet_address = Column(String(50), nullable=True)
    
    # Tracking
    total_paid_sol = Column(Float, default=0.0, nullable=False)
    total_airdrops_received = Column(Integer, default=0, nullable=False)
    last_airdrop_at = Column(DateTime, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Airdrop(Base):
    __tablename__ = "airdrops"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    admin_id = Column(BigInteger, ForeignKey('admins.telegram_id'), nullable=False)
    bot_id = Column(Integer, ForeignKey('client_bots.id'), nullable=False)
    token_address = Column(String(50), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    token_name = Column(String(100), nullable=True)
    
    # Distribution amounts
    total_amount = Column(Float, nullable=False)
    per_vip_amount = Column(Float, default=100.0, nullable=False)
    per_whale_amount = Column(Float, default=500.0, nullable=False)
    per_premium_amount = Column(Float, default=1000.0, nullable=False)
    
    # Status tracking
    status = Column(String(20), default='pending', nullable=False)  # pending, scheduled, active, completed, cancelled
    scheduled_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    
    # Results
    total_recipients = Column(Integer, default=0, nullable=False)
    successful_sends = Column(Integer, default=0, nullable=False)
    failed_sends = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class TokenDetection(Base):
    __tablename__ = "token_detections"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    bot_id = Column(Integer, ForeignKey('client_bots.id'), nullable=False)
    
    # Token info
    token_address = Column(String(50), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    token_name = Column(String(100), nullable=True)
    
    # Detection metrics
    liquidity_usd = Column(Float, nullable=False)
    market_cap_usd = Column(Float, nullable=False)
    volume_24h = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=False)
    
    # Detection reason
    detection_reason = Column(String(50), nullable=False)  # new_launch, liquidity_spike, volume_spike, whale_buy
    
    # Alert status
    alert_sent = Column(Boolean, default=False, nullable=False)
    alert_sent_at = Column(DateTime, nullable=True)
    subscribers_notified = Column(Integer, default=0, nullable=False)
    
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# ═══════════════════════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════

def init_db():
    """Create all tables with error handling"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"✅ Tables created: {tables}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise

def get_db():
    """Get database session with error handling"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_or_create_admin(db: Session, telegram_id: int, username: str = None, first_name: str = None):
    """Get existing admin or create new"""
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == telegram_id).first()
        if not admin:
            import secrets
            referral_code = secrets.token_hex(4)
            admin = Admin(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                referral_code=referral_code,
                max_clients=1
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            logger.info(f"✅ New admin created: {telegram_id}")
        return admin
    except Exception as e:
        db.rollback()
        logger.error(f"Error in get_or_create_admin: {e}")
        raise

def check_subscription(db: Session, telegram_id: int):
    """Check if admin has active subscription"""
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == telegram_id).first()
        if not admin:
            return False, 0
        
        if admin.expires_at and admin.expires_at > datetime.utcnow():
            days_left = (admin.expires_at - datetime.utcnow()).days
            return True, days_left
        return False, 0
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False, 0

def add_referral_reward(db: Session, admin_id: int, days: int = 3):
    """Add referral reward days to admin subscription"""
    try:
        admin = db.query(Admin).filter(Admin.telegram_id == admin_id).first()
        if not admin:
            return False
        
        if admin.expires_at and admin.expires_at > datetime.utcnow():
            admin.expires_at += timedelta(days=days)
        else:
            admin.expires_at = datetime.utcnow() + timedelta(days=days)
        
        admin.referral_count += 1
        if admin.referral_count % 3 == 0:
            admin.max_clients += 1
        
        db.commit()
        logger.info(f"✅ Referral reward added to {admin_id}: +{days} days")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding referral reward: {e}")
        return False

def get_stats(db: Session):
    """Get platform statistics with error handling"""
    try:
        from sqlalchemy import func
        
        total_admins = db.query(Admin).count()
        active_admins = db.query(Admin).filter(Admin.expires_at > datetime.utcnow()).count()
        total_bots = db.query(ClientBot).count()
        active_bots = db.query(ClientBot).filter(ClientBot.is_active == True).count()
        
        total_revenue = db.query(func.sum(Payment.amount_sol)).filter(Payment.status == 'confirmed').scalar() or 0.0
        
        return {
            'total_admins': total_admins,
            'active_admins': active_admins,
            'total_bots': total_bots,
            'active_bots': active_bots,
            'total_revenue_sol': float(total_revenue)
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            'total_admins': 0,
            'active_admins': 0,
            'total_bots': 0,
            'active_bots': 0,
            'total_revenue_sol': 0.0
        }

