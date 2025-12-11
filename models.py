from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base # Import Base from our database.py

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, index=True, nullable=True) # Telegram username
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_subscribed = Column(Boolean, default=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    wallets = relationship("TrackedWallet", back_populates="owner")
    alerts = relationship("PriceAlert", back_populates="owner")

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"

class TrackedWallet(Base):
    __tablename__ = "tracked_wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address = Column(String, index=True, nullable=False)
    chain = Column(String, index=True, nullable=False) # e.g., "ETH", "SOL", "BTC"
    name = Column(String, nullable=True) # User-defined name for the wallet
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="wallets")

    __table_args__ = (UniqueConstraint("user_id", "address", "chain", name="_user_address_chain_uc"),)

    def __repr__(self):
        return f"<TrackedWallet(user_id={self.user_id}, address='{self.address}', chain='{self.chain}')>"

class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False) # e.g., "ETH", "BTC", "SOL"
    target_price = Column(Float, nullable=False)
    currency = Column(String, default="USD", nullable=False) # e.g., "USD", "EUR"
    alert_when_above = Column(Boolean, default=True) # True for alert if price > target, False for price < target
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    triggered_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="alerts")

    def __repr__(self):
        return f"<PriceAlert(user_id={self.user_id}, symbol='{self.symbol}', target_price={self.target_price})>"

# We will add more models for subscriptions, transactions, etc., as we build out features.
