"""
Broadcast Service

Handles creation, storage, and delivery of broadcasts to bot subscribers.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from telegram import Bot
from telegram.error import TelegramError, Forbidden

from database.models import Broadcast, Subscriber, BroadcastDelivery
from services.subscriber_service import mark_subscriber_blocked

logger = logging.getLogger(__name__)


def create_broadcast(
    db: Session,
    bot_id: int,
    content_type: str,
    text: Optional[str] = None,
    media_url: Optional[str] = None,
    media_file_id: Optional[str] = None,
    scheduled_for: Optional[datetime] = None
) -> Broadcast:
    """
    Create a new broadcast.
    
    Args:
        db: Database session
        bot_id: Bot ID
        content_type: Type of broadcast (text, photo, video)
        text: Text content or caption
        media_url: URL of media file
        media_file_id: Telegram file_id for media
        scheduled_for: Schedule for future delivery
        
    Returns:
        Broadcast: Created broadcast object
    """
    broadcast = Broadcast(
        bot_id=bot_id,
        content_type=content_type,
        text=text,
        media_url=media_url,
        media_file_id=media_file_id,
        status='draft',
        scheduled_for=scheduled_for,
        created_at=datetime.utcnow()
    )
    
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)
    
    logger.info(f"✅ Broadcast {broadcast.id} created for bot {bot_id}")
    
    return broadcast


def update_broadcast(
    db: Session,
    broadcast_id: int,
    **kwargs
) -> Optional[Broadcast]:
    """
    Update a broadcast.
    
    Args:
        db: Database session
        broadcast_id: Broadcast ID
        **kwargs: Fields to update
        
    Returns:
        Broadcast: Updated broadcast or None
    """
    broadcast = db.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
    
    if not broadcast:
        return None
    
    for key, value in kwargs.items():
        if hasattr(broadcast, key):
            setattr(broadcast, key, value)
    
    db.commit()
    db.refresh(broadcast)
    
    return broadcast


def get_broadcast(db: Session, broadcast_id: int) -> Optional[Broadcast]:
    """Get a broadcast by ID."""
    return db.query(Broadcast).filter(Broadcast.id == broadcast_id).first()


def get_broadcasts(
    db: Session,
    bot_id: int,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
) -> List[Broadcast]:
    """
    Get list of broadcasts for a bot.
    
    Args:
        db: Database session
        bot_id: Bot ID
        limit: Max results
        offset: Pagination offset
        status: Filter by status
        
    Returns:
        List of broadcasts
    """
    query = db.query(Broadcast).filter(Broadcast.bot_id == bot_id)
    
    if status:
        query = query.filter(Broadcast.status == status)
    
    query = query.order_by(Broadcast.sent_at.desc())
    
    if offset:
        query = query.offset(offset)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def delete_broadcast(db: Session, broadcast_id: int) -> bool:
    """Delete a broadcast (only if draft or failed)."""
    broadcast = db.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
    
    if not broadcast:
        return False
    
    if broadcast.status not in ['draft', 'failed']:
        logger.warning(f"Cannot delete broadcast {broadcast_id} with status {broadcast.status}")
        return False
    
    db.delete(broadcast)
    db.commit()
    
    logger.info(f"Broadcast {broadcast_id} deleted")
    return True


async def send_broadcast(
    broadcast_id: int,
    bot_token: str,
    db: Session,
    progress_callback=None
) -> Tuple[int, int]:
    """
    Send a broadcast to all active subscribers.
    
    Args:
        broadcast_id: Broadcast ID
        bot_token: Bot's Telegram token
        db: Database session
        progress_callback: Optional callback for progress updates (async function)
        
    Returns:
        Tuple[int, int]: (successful_sends, failed_sends)
    """
    # Get broadcast
    broadcast = db.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
    if not broadcast:
        logger.error(f"Broadcast {broadcast_id} not found")
        return (0, 0)
    
    # Update status to sending
    broadcast.status = 'sending'
    broadcast.sent_at = datetime.utcnow()
    db.commit()
    
    # Get all active subscribers
    subscribers = db.query(Subscriber).filter(
        Subscriber.bot_id == broadcast.bot_id,
        Subscriber.is_active == True,
        Subscriber.is_blocked == False
    ).all()
    
    total_subscribers = len(subscribers)
    broadcast.total_subscribers = total_subscribers
    db.commit()
    
    logger.info(f"📢 Starting broadcast {broadcast_id} to {total_subscribers} subscribers")
    
    # Create Telegram bot instance
    telegram_bot = Bot(token=bot_token)
    
    successful = 0
    failed = 0
    
    # Send to each subscriber
    for idx, subscriber in enumerate(subscribers, 1):
        try:
            # Send message based on content type
            if broadcast.content_type == 'text':
                await telegram_bot.send_message(
                    chat_id=subscriber.user_telegram_id,
                    text=broadcast.text,
                    parse_mode='Markdown'
                )
            elif broadcast.content_type == 'photo':
                if broadcast.media_file_id:
                    await telegram_bot.send_photo(
                        chat_id=subscriber.user_telegram_id,
                        photo=broadcast.media_file_id,
                        caption=broadcast.text,
                        parse_mode='Markdown'
                    )
                else:
                    # Fallback to URL
                    await telegram_bot.send_photo(
                        chat_id=subscriber.user_telegram_id,
                        photo=broadcast.media_url,
                        caption=broadcast.text,
                        parse_mode='Markdown'
                    )
            elif broadcast.content_type == 'video':
                if broadcast.media_file_id:
                    await telegram_bot.send_video(
                        chat_id=subscriber.user_telegram_id,
                        video=broadcast.media_file_id,
                        caption=broadcast.text,
                        parse_mode='Markdown'
                    )
                else:
                    # Fallback to URL
                    await telegram_bot.send_video(
                        chat_id=subscriber.user_telegram_id,
                        video=broadcast.media_url,
                        caption=broadcast.text,
                        parse_mode='Markdown'
                    )
            
            # Record successful delivery
            delivery = BroadcastDelivery(
                broadcast_id=broadcast_id,
                subscriber_id=subscriber.id,
                status='sent',
                sent_at=datetime.utcnow()
            )
            db.add(delivery)
            
            successful += 1
            logger.debug(f"✅ Sent to {subscriber.user_telegram_id}")
            
        except Forbidden as e:
            # User blocked the bot
            logger.warning(f"❌ User {subscriber.user_telegram_id} blocked bot")
            mark_subscriber_blocked(broadcast.bot_id, subscriber.user_telegram_id, db)
            
            delivery = BroadcastDelivery(
                broadcast_id=broadcast_id,
                subscriber_id=subscriber.id,
                status='failed',
                error_message='User blocked bot'
            )
            db.add(delivery)
            failed += 1
            
        except TelegramError as e:
            # Other Telegram errors (including chat not found)
            error_msg = str(e)
            logger.error(f"❌ Telegram error sending to {subscriber.user_telegram_id}: {e}")
            
            # Check if it's a "chat not found" error by message content
            if 'chat not found' in error_msg.lower():
                error_msg = 'Chat not found'
            
            delivery = BroadcastDelivery(
                broadcast_id=broadcast_id,
                subscriber_id=subscriber.id,
                status='failed',
                error_message=error_msg
            )
            db.add(delivery)
            failed += 1
            
        except Exception as e:
            # Unexpected errors
            logger.error(f"❌ Unexpected error sending to {subscriber.user_telegram_id}: {e}", exc_info=True)
            
            delivery = BroadcastDelivery(
                broadcast_id=broadcast_id,
                subscriber_id=subscriber.id,
                status='failed',
                error_message=str(e)
            )
            db.add(delivery)
            failed += 1
        
        # Commit after each send to save progress
        db.commit()
        
        # Rate limiting: 30 msgs/sec max, we'll do 25 to be safe
        # That's 40ms between messages
        await asyncio.sleep(0.04)
        
        # Call progress callback if provided
        if progress_callback and idx % 10 == 0:
            try:
                await progress_callback(idx, total_subscribers, successful, failed)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    # Update broadcast with final stats
    broadcast.successful_sends = successful
    broadcast.failed_sends = failed
    broadcast.status = 'sent' if successful > 0 else 'failed'
    broadcast.completed_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"✅ Broadcast {broadcast_id} complete: {successful} sent, {failed} failed")
    
    return (successful, failed)


def get_broadcast_stats(db: Session, broadcast_id: int) -> dict:
    """
    Get statistics for a broadcast.
    
    Args:
        db: Database session
        broadcast_id: Broadcast ID
        
    Returns:
        dict: Statistics
    """
    broadcast = db.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
    
    if not broadcast:
        return {}
    
    # Get delivery counts
    total_deliveries = db.query(BroadcastDelivery).filter(
        BroadcastDelivery.broadcast_id == broadcast_id
    ).count()
    
    successful_deliveries = db.query(BroadcastDelivery).filter(
        BroadcastDelivery.broadcast_id == broadcast_id,
        BroadcastDelivery.status == 'sent'
    ).count()
    
    failed_deliveries = db.query(BroadcastDelivery).filter(
        BroadcastDelivery.broadcast_id == broadcast_id,
        BroadcastDelivery.status == 'failed'
    ).count()
    
    return {
        'broadcast_id': broadcast.id,
        'status': broadcast.status,
        'content_type': broadcast.content_type,
        'created_at': broadcast.created_at,
        'sent_at': broadcast.sent_at,
        'completed_at': broadcast.completed_at,
        'total_subscribers': broadcast.total_subscribers,
        'successful_sends': successful_deliveries,
        'failed_sends': failed_deliveries,
        'total_deliveries': total_deliveries,
    }
