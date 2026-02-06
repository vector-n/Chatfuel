"""
User State Service

Manages temporary user state for webhook-based bots.
Used for broadcast composition and other stateful interactions.
"""

import logging
from sqlalchemy.orm import Session
from database.models import UserState

logger = logging.getLogger(__name__)


def get_user_state(db: Session, bot_id: int, user_telegram_id: int) -> dict:
    """
    Get user state data.
    
    Args:
        db: Database session
        bot_id: Bot ID
        user_telegram_id: User's Telegram ID
        
    Returns:
        Dictionary of state data (empty dict if no state exists)
    """
    state = db.query(UserState).filter(
        UserState.bot_id == bot_id,
        UserState.user_telegram_id == user_telegram_id
    ).first()
    
    if state:
        return state.state_data or {}
    return {}


def set_user_state(db: Session, bot_id: int, user_telegram_id: int, state_data: dict):
    """
    Set/update user state data.
    
    Args:
        db: Database session
        bot_id: Bot ID
        user_telegram_id: User's Telegram ID
        state_data: Dictionary of state data to store
    """
    state = db.query(UserState).filter(
        UserState.bot_id == bot_id,
        UserState.user_telegram_id == user_telegram_id
    ).first()
    
    if state:
        state.state_data = state_data
    else:
        state = UserState(
            bot_id=bot_id,
            user_telegram_id=user_telegram_id,
            state_data=state_data
        )
        db.add(state)
    
    db.commit()
    logger.debug(f"Set state for bot={bot_id}, user={user_telegram_id}: {state_data}")


def update_user_state(db: Session, bot_id: int, user_telegram_id: int, key: str, value):
    """
    Update a specific key in user state.
    
    Args:
        db: Database session
        bot_id: Bot ID
        user_telegram_id: User's Telegram ID
        key: State key to update
        value: Value to set
    """
    state_data = get_user_state(db, bot_id, user_telegram_id)
    state_data[key] = value
    set_user_state(db, bot_id, user_telegram_id, state_data)


def clear_user_state(db: Session, bot_id: int, user_telegram_id: int, key: str = None):
    """
    Clear user state (entire state or specific key).
    
    Args:
        db: Database session
        bot_id: Bot ID
        user_telegram_id: User's Telegram ID
        key: Optional - specific key to clear (if None, clears all state)
    """
    if key:
        state_data = get_user_state(db, bot_id, user_telegram_id)
        if key in state_data:
            del state_data[key]
            set_user_state(db, bot_id, user_telegram_id, state_data)
    else:
        db.query(UserState).filter(
            UserState.bot_id == bot_id,
            UserState.user_telegram_id == user_telegram_id
        ).delete()
        db.commit()
        logger.debug(f"Cleared all state for bot={bot_id}, user={user_telegram_id}")
