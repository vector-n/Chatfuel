"""
Subscriber Service

Manages subscriber tracking, statistics, and queries.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import Subscriber, Bot, Broadcast

logger = logging.getLogger(__name__)


def create_or_update_subscriber(
    db: Session,
    bot_id: int,
    user_telegram_id: int,
    user_info: dict
) -> Subscriber:
    """
    Create a new subscriber or update existing one.
    
    Args:
        db: Database session
        bot_id: Bot ID
        user_telegram_id: User's Telegram ID
        user_info: Dict with user information (username, first_name, last_name, language)
        
    Returns:
        Subscriber: Created or updated subscriber
    """
    # Check if subscriber already exists
    subscriber = db.query(Subscriber).filter(
        Subscriber.bot_id == bot_id,
        Subscriber.user_telegram_id == user_telegram_id
    ).first()
    
    if subscriber:
        # Update existing subscriber
        subscriber.username = user_info.get('username')
        subscriber.first_name = user_info.get('first_name')
        subscriber.last_name = user_info.get('last_name')
        subscriber.language = user_info.get('language', 'en')
        subscriber.last_interaction = datetime.utcnow()
        
        # Reactivate if was inactive
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.subscribed_at = datetime.utcnow()
            logger.info(f"✅ Subscriber {user_telegram_id} reactivated for bot {bot_id}")
        
        db.commit()
        db.refresh(subscriber)
        
        logger.debug(f"Updated subscriber {user_telegram_id} for bot {bot_id}")
        
    else:
        # Create new subscriber
        subscriber = Subscriber(
            bot_id=bot_id,
            user_telegram_id=user_telegram_id,
            username=user_info.get('username'),
            first_name=user_info.get('first_name'),
            last_name=user_info.get('last_name'),
            language=user_info.get('language', 'en'),
            subscribed_at=datetime.utcnow(),
            last_interaction=datetime.utcnow(),
            is_active=True,
            is_blocked=False
        )
        
        db.add(subscriber)
        db.commit()
        db.refresh(subscriber)
        
        logger.info(f"✅ New subscriber {user_telegram_id} added to bot {bot_id}")
    
    return subscriber


def get_subscriber_count(bot_id: int, db: Session, active_only: bool = True) -> int:
    """
    Get total subscriber count for a bot.
    
    Args:
        bot_id: Bot ID
        db: Database session
        active_only: Count only active subscribers
        
    Returns:
        int: Subscriber count
    """
    query = db.query(Subscriber).filter(Subscriber.bot_id == bot_id)
    
    if active_only:
        query = query.filter(Subscriber.is_active == True)
    
    return query.count()


def get_subscribers(
    bot_id: int,
    db: Session,
    active_only: bool = True,
    limit: int = None,
    offset: int = 0
) -> list:
    """
    Get list of subscribers for a bot.
    
    Args:
        bot_id: Bot ID
        db: Database session
        active_only: Return only active subscribers
        limit: Maximum number to return
        offset: Offset for pagination
        
    Returns:
        list: List of Subscriber objects
    """
    query = db.query(Subscriber).filter(Subscriber.bot_id == bot_id)
    
    if active_only:
        query = query.filter(Subscriber.is_active == True)
    
    # Order by most recent first
    query = query.order_by(Subscriber.subscribed_at.desc())
    
    if offset:
        query = query.offset(offset)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_subscriber_stats(bot_id: int, db: Session) -> dict:
    """
    Get comprehensive subscriber statistics for a bot.
    
    Args:
        bot_id: Bot ID
        db: Database session
        
    Returns:
        dict: Statistics dictionary
    """
    total = db.query(Subscriber).filter(Subscriber.bot_id == bot_id).count()
    
    active = db.query(Subscriber).filter(
        Subscriber.bot_id == bot_id,
        Subscriber.is_active == True
    ).count()
    
    inactive = total - active
    
    # New subscribers in last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_last_7_days = db.query(Subscriber).filter(
        Subscriber.bot_id == bot_id,
        Subscriber.subscribed_at >= seven_days_ago
    ).count()
    
    # New subscribers in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_last_30_days = db.query(Subscriber).filter(
        Subscriber.bot_id == bot_id,
        Subscriber.subscribed_at >= thirty_days_ago
    ).count()
    
    # Total broadcasts sent (from broadcasts table)
    total_broadcasts = db.query(Broadcast).filter(
        Broadcast.bot_id == bot_id
    ).count()
    
    # Total button menus (Phase 3)
    from database.models import ButtonMenu
    total_menus = db.query(ButtonMenu).filter(
        ButtonMenu.bot_id == bot_id
    ).count()
    
    # Total forms (Phase 4)
    from database.models import Form
    total_forms = db.query(Form).filter(
        Form.bot_id == bot_id,
        Form.is_active == True
    ).count()
    
    return {
        'total': total,
        'active': active,
        'inactive': inactive,
        'new_last_7_days': new_last_7_days,
        'new_last_30_days': new_last_30_days,
        'total_broadcasts': total_broadcasts,
        'total_menus': total_menus,
        'total_forms': total_forms,
    }


def deactivate_subscriber(
    bot_id: int,
    user_telegram_id: int,
    db: Session,
    reason: str = 'user_action'
) -> bool:
    """
    Deactivate a subscriber (unsubscribe).
    
    Args:
        bot_id: Bot ID
        user_telegram_id: User's Telegram ID
        db: Database session
        reason: Reason for deactivation
        
    Returns:
        bool: True if successful
    """
    subscriber = db.query(Subscriber).filter(
        Subscriber.bot_id == bot_id,
        Subscriber.user_telegram_id == user_telegram_id
    ).first()
    
    if subscriber:
        subscriber.is_active = False
        subscriber.unsubscribed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Subscriber {user_telegram_id} deactivated from bot {bot_id}. Reason: {reason}")
        return True
    
    return False


def mark_subscriber_blocked(
    bot_id: int,
    user_telegram_id: int,
    db: Session
) -> bool:
    """
    Mark subscriber as blocked (bot was blocked by user).
    
    Args:
        bot_id: Bot ID
        user_telegram_id: User's Telegram ID
        db: Database session
        
    Returns:
        bool: True if successful
    """
    subscriber = db.query(Subscriber).filter(
        Subscriber.bot_id == bot_id,
        Subscriber.user_telegram_id == user_telegram_id
    ).first()
    
    if subscriber:
        subscriber.is_blocked = True
        subscriber.is_active = False
        db.commit()
        
        logger.info(f"Subscriber {user_telegram_id} marked as blocked for bot {bot_id}")
        return True
    
    return False


def search_subscribers(
    bot_id: int,
    db: Session,
    search_term: str,
    limit: int = 50
) -> list:
    """
    Search subscribers by name or username.
    
    Args:
        bot_id: Bot ID
        db: Database session
        search_term: Search term
        limit: Maximum results
        
    Returns:
        list: List of matching subscribers
    """
    search_pattern = f"%{search_term}%"
    
    subscribers = db.query(Subscriber).filter(
        Subscriber.bot_id == bot_id,
        Subscriber.is_active == True,
        (
            Subscriber.first_name.ilike(search_pattern) |
            Subscriber.last_name.ilike(search_pattern) |
            Subscriber.username.ilike(search_pattern)
        )
    ).limit(limit).all()
    
    return subscribers


def get_subscriber_growth(bot_id: int, db: Session, days: int = 30) -> dict:
    """
    Get subscriber growth data for charts.
    
    Args:
        bot_id: Bot ID
        db: Database session
        days: Number of days to analyze
        
    Returns:
        dict: Growth data
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Group by date
    growth_data = db.query(
        func.date(Subscriber.subscribed_at).label('date'),
        func.count(Subscriber.id).label('count')
    ).filter(
        Subscriber.bot_id == bot_id,
        Subscriber.subscribed_at >= start_date
    ).group_by(
        func.date(Subscriber.subscribed_at)
    ).order_by(
        func.date(Subscriber.subscribed_at)
    ).all()
    
    # Format for charts
    dates = []
    counts = []
    
    for row in growth_data:
        dates.append(row.date.strftime('%Y-%m-%d'))
        counts.append(row.count)
    
    return {
        'dates': dates,
        'counts': counts,
        'total_new': sum(counts)
    }


def export_subscribers(bot_id: int, db: Session, format: str = 'csv') -> str:
    """
    Export subscriber list (Phase 3 feature).
    
    Args:
        bot_id: Bot ID
        db: Database session
        format: Export format (csv, json)
        
    Returns:
        str: Exported data
    """
    # TODO: Implement in Phase 3
    subscribers = get_subscribers(bot_id, db, active_only=False, limit=None)
    
    if format == 'csv':
        # Return CSV string
        pass
    elif format == 'json':
        # Return JSON string
        pass
    
    return ""
