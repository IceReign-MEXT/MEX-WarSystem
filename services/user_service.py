from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import User
from typing import Optional

def get_or_create_user(db: Session, telegram_id: int, username: Optional[str] = None,
                       first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
    """
    Retrieves a user by telegram_id or creates a new one if not found.
    Updates user details if they have changed.
    """
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        # Update user details if they've changed
        if user.username != username:
            user.username = username
        if user.first_name != first_name:
            user.first_name = first_name
        if user.last_name != last_name:
            user.last_name = last_name
        # db.commit() and db.refresh(user) will be handled by the session context
        return user
    else:
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.add(new_user)
        # db.commit() and db.refresh(new_user) will be handled by the session context
        return new_user

def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
    """Retrieves a user by their Telegram ID."""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def update_user_subscription(db: Session, user: User, is_subscribed: bool, days: int = 0) -> User:
    """Updates a user's subscription status and expiration date."""
    user.is_subscribed = is_subscribed
    if is_subscribed:
        user.subscription_expires_at = datetime.utcnow() + timedelta(days=days)
    else:
        user.subscription_expires_at = None
    db.commit()
    db.refresh(user)
    return user
