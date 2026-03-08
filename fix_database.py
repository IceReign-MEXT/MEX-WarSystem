#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
DATABASE EMERGENCY FIX - Force create tables with proper schema
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found!")
    sys.exit(1)

def parse_db_url(url):
    """Parse PostgreSQL URL"""
    # Remove postgresql:// prefix
    url = url.replace('postgresql://', '').replace('postgres://', '')
    
    # Split credentials and host
    if '@' in url:
        credentials, host_db = url.split('@')
        user, password = credentials.split(':')
    else:
        raise ValueError("Invalid DATABASE_URL format")
    
    if '/' in host_db:
        host_port, database = host_db.split('/')
        if '?' in database:
            database = database.split('?')[0]
    else:
        raise ValueError("No database name in URL")
    
    if ':' in host_port:
        host, port = host_port.split(':')
    else:
        host = host_port
        port = "5432"
    
    return {
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'database': database
    }

def create_tables():
    """Manually create all tables with explicit SQL"""
    
    db_info = parse_db_url(DATABASE_URL)
    print(f"Connecting to {db_info['host']}:{db_info['port']}/{db_info['database']}")
    
    try:
        conn = psycopg2.connect(
            host=db_info['host'],
            port=db_info['port'],
            user=db_info['user'],
            password=db_info['password'],
            database=db_info['database'],
            sslmode='require'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Drop existing tables to start fresh (CAREFUL: This deletes data!)
        print("Dropping old tables if exist...")
        cursor.execute("""
            DROP TABLE IF EXISTS token_detections CASCADE;
            DROP TABLE IF EXISTS airdrops CASCADE;
            DROP TABLE IF EXISTS subscribers CASCADE;
            DROP TABLE IF EXISTS client_bots CASCADE;
            DROP TABLE IF EXISTS payments CASCADE;
            DROP TABLE IF EXISTS admins CASCADE;
        """)
        print("✅ Old tables dropped")
        
        # Create admins table
        print("Creating admins table...")
        cursor.execute("""
            CREATE TABLE admins (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(100),
                first_name VARCHAR(100),
                plan_type VARCHAR(20),
                expires_at TIMESTAMP,
                max_clients INTEGER DEFAULT 1 NOT NULL,
                referral_code VARCHAR(20) UNIQUE NOT NULL,
                referred_by BIGINT REFERENCES admins(telegram_id),
                referral_count INTEGER DEFAULT 0 NOT NULL,
                total_earned_sol FLOAT DEFAULT 0.0 NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)
        print("✅ admins table created")
        
        # Create payments table
        print("Creating payments table...")
        cursor.execute("""
            CREATE TABLE payments (
                id SERIAL PRIMARY KEY,
                admin_id BIGINT NOT NULL REFERENCES admins(telegram_id),
                amount_sol FLOAT NOT NULL,
                plan_type VARCHAR(20) NOT NULL,
                tx_hash VARCHAR(100) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                confirmed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)
        print("✅ payments table created")
        
        # Create client_bots table
        print("Creating client_bots table...")
        cursor.execute("""
            CREATE TABLE client_bots (
                id SERIAL PRIMARY KEY,
                admin_id BIGINT NOT NULL REFERENCES admins(telegram_id),
                bot_token VARCHAR(200) NOT NULL,
                bot_username VARCHAR(100),
                channel_id BIGINT,
                group_id BIGINT,
                wallet_address VARCHAR(50) NOT NULL,
                vip_price FLOAT DEFAULT 0.5 NOT NULL,
                whale_price FLOAT DEFAULT 1.0 NOT NULL,
                premium_price FLOAT DEFAULT 2.5 NOT NULL,
                target_token VARCHAR(50),
                min_liquidity_usd FLOAT DEFAULT 1000.0 NOT NULL,
                max_market_cap FLOAT DEFAULT 1000000.0 NOT NULL,
                airdrop_enabled BOOLEAN DEFAULT TRUE NOT NULL,
                airdrop_vip_amount FLOAT DEFAULT 100.0 NOT NULL,
                airdrop_whale_amount FLOAT DEFAULT 500.0 NOT NULL,
                airdrop_premium_amount FLOAT DEFAULT 1000.0 NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                is_deployed BOOLEAN DEFAULT FALSE NOT NULL,
                deployed_at TIMESTAMP,
                last_ping TIMESTAMP,
                total_subscribers INTEGER DEFAULT 0 NOT NULL,
                total_revenue_sol FLOAT DEFAULT 0.0 NOT NULL,
                total_alerts_sent INTEGER DEFAULT 0 NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)
        print("✅ client_bots table created")
        
        # Create subscribers table
        print("Creating subscribers table...")
        cursor.execute("""
            CREATE TABLE subscribers (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER NOT NULL REFERENCES client_bots(id),
                telegram_id BIGINT NOT NULL,
                username VARCHAR(100),
                tier VARCHAR(20) DEFAULT 'free' NOT NULL,
                expires_at TIMESTAMP,
                wallet_address VARCHAR(50),
                total_paid_sol FLOAT DEFAULT 0.0 NOT NULL,
                total_airdrops_received INTEGER DEFAULT 0 NOT NULL,
                last_airdrop_at TIMESTAMP,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)
        print("✅ subscribers table created")
        
        # Create airdrops table
        print("Creating airdrops table...")
        cursor.execute("""
            CREATE TABLE airdrops (
                id SERIAL PRIMARY KEY,
                admin_id BIGINT NOT NULL REFERENCES admins(telegram_id),
                bot_id INTEGER NOT NULL REFERENCES client_bots(id),
                token_address VARCHAR(50) NOT NULL,
                token_symbol VARCHAR(20) NOT NULL,
                token_name VARCHAR(100),
                total_amount FLOAT NOT NULL,
                per_vip_amount FLOAT DEFAULT 100.0 NOT NULL,
                per_whale_amount FLOAT DEFAULT 500.0 NOT NULL,
                per_premium_amount FLOAT DEFAULT 1000.0 NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                scheduled_at TIMESTAMP,
                executed_at TIMESTAMP,
                total_recipients INTEGER DEFAULT 0 NOT NULL,
                successful_sends INTEGER DEFAULT 0 NOT NULL,
                failed_sends INTEGER DEFAULT 0 NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)
        print("✅ airdrops table created")
        
        # Create token_detections table
        print("Creating token_detections table...")
        cursor.execute("""
            CREATE TABLE token_detections (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER NOT NULL REFERENCES client_bots(id),
                token_address VARCHAR(50) NOT NULL,
                token_symbol VARCHAR(20) NOT NULL,
                token_name VARCHAR(100),
                liquidity_usd FLOAT NOT NULL,
                market_cap_usd FLOAT NOT NULL,
                volume_24h FLOAT,
                price_usd FLOAT NOT NULL,
                detection_reason VARCHAR(50) NOT NULL,
                alert_sent BOOLEAN DEFAULT FALSE NOT NULL,
                alert_sent_at TIMESTAMP,
                subscribers_notified INTEGER DEFAULT 0 NOT NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)
        print("✅ token_detections table created")
        
        # Create indexes for performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX idx_admins_telegram_id ON admins(telegram_id);")
        cursor.execute("CREATE INDEX idx_payments_admin_id ON payments(admin_id);")
        cursor.execute("CREATE INDEX idx_payments_tx_hash ON payments(tx_hash);")
        cursor.execute("CREATE INDEX idx_client_bots_admin_id ON client_bots(admin_id);")
        cursor.execute("CREATE INDEX idx_subscribers_bot_id ON subscribers(bot_id);")
        cursor.execute("CREATE INDEX idx_airdrops_admin_id ON airdrops(admin_id);")
        cursor.execute("CREATE INDEX idx_token_detections_bot_id ON token_detections(bot_id);")
        print("✅ Indexes created")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ DATABASE SETUP COMPLETE!")
        print("="*60)
        print("\nAll tables created successfully:")
        print("  • admins")
        print("  • payments")
        print("  • client_bots")
        print("  • subscribers")
        print("  • airdrops")
        print("  • token_detections")
        print("\nYou can now run: python main.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("ICEGODS DATABASE EMERGENCY FIX")
    print("="*60)
    print("This will DELETE existing data and recreate tables.")
    print("Press Ctrl+C to cancel, or wait 3 seconds...")
    import time
    time.sleep(3)
    
    success = create_tables()
    sys.exit(0 if success else 1)

