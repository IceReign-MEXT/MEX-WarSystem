from sqlalchemy.orm import Session
from models import User, TrackedWallet
from typing import List, Optional

def add_tracked_wallet(db: Session, user: User, address: str, chain: str, name: Optional[str] = None) -> Optional[TrackedWallet]:
    """Adds a new wallet to track for a user, if it doesn't already exist."""
    # Check if the wallet already exists for this user and chain
    existing_wallet = db.query(TrackedWallet).filter(
        TrackedWallet.user_id == user.id,
        TrackedWallet.address == address,
        TrackedWallet.chain == chain
    ).first()

    if existing_wallet:
        return None # Wallet already tracked

    new_wallet = TrackedWallet(
        user_id=user.id,
        address=address,
        chain=chain,
        name=name
    )
    db.add(new_wallet)
    db.commit()
    db.refresh(new_wallet)
    return new_wallet

def get_user_wallets(db: Session, user_id: int) -> List[TrackedWallet]:
    """Retrieves all wallets tracked by a specific user."""
    return db.query(TrackedWallet).filter(TrackedWallet.user_id == user_id).all()

def get_tracked_wallet_by_address(db: Session, user_id: int, address: str) -> Optional[TrackedWallet]:
    """Retrieves a specific tracked wallet for a user by address."""
    return db.query(TrackedWallet).filter(
        TrackedWallet.user_id == user_id,
        TrackedWallet.address == address
    ).first()

def remove_tracked_wallet(db: Session, wallet: TrackedWallet) -> bool:
    """Removes a tracked wallet from the database."""
    db.delete(wallet)
    db.commit()
    return True

def get_all_tracked_wallets(db: Session) -> List[TrackedWallet]:
    """Retrieves all tracked wallets for all users."""
    return db.query(TrackedWallet).all()
