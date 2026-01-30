"""Helper utility functions."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from database.models import User, Bot
from config.constants import SubscriptionTier


def get_user_or_create(db: Session, telegram_user) -> User:
    """
    Get existing user or create new one.
    
    Args:
        db: Database session
        telegram_user: Telegram User object from update
        
    Returns:
        User model instance
    """
    user = db.query(User).filter(User.telegram_id == telegram_user.id).first()
    
    if not user:
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language=telegram_user.language_code or 'en',
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update user info if changed
        updated = False
        if user.username != telegram_user.username:
            user.username = telegram_user.username
            updated = True
        if user.first_name != telegram_user.first_name:
            user.first_name = telegram_user.first_name
            updated = True
        if user.last_name != telegram_user.last_name:
            user.last_name = telegram_user.last_name
            updated = True
        
        user.last_activity = datetime.utcnow()
        
        if updated:
            db.commit()
            db.refresh(user)
    
    return user


def get_user_active_bot(db: Session, user_id: int) -> Optional[Bot]:
    """
    Get user's most recently used bot or first bot.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Bot instance or None
    """
    # For now, just get the first bot
    # Later, we can track which bot the user last interacted with
    bot = db.query(Bot).filter(
        Bot.user_id == user_id,
        Bot.is_active == True
    ).first()
    
    return bot


def format_subscriber_count(count: int) -> str:
    """
    Format subscriber count for display.
    
    Args:
        count: Number of subscribers
        
    Returns:
        Formatted string (e.g., "1.2K", "5.3M")
    """
    if count < 1000:
        return str(count)
    elif count < 1000000:
        return f"{count/1000:.1f}K"
    else:
        return f"{count/1000000:.1f}M"


def format_datetime(dt: datetime, include_time: bool = True) -> str:
    """
    Format datetime for display.
    
    Args:
        dt: Datetime to format
        include_time: Whether to include time
        
    Returns:
        Formatted datetime string
    """
    if not dt:
        return "Never"
    
    now = datetime.utcnow()
    diff = now - dt
    
    # If within last 24 hours, show relative time
    if diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        if minutes < 1:
            return "Just now"
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    
    elif diff < timedelta(hours=24):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    
    # Otherwise show date
    if include_time:
        return dt.strftime("%b %d, %Y at %H:%M UTC")
    else:
        return dt.strftime("%b %d, %Y")


def calculate_completion_rate(total: int, completed: int) -> float:
    """
    Calculate completion rate percentage.
    
    Args:
        total: Total count
        completed: Completed count
        
    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 1)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def get_tier_name(tier: str) -> str:
    """
    Get display name for subscription tier.
    
    Args:
        tier: Tier code
        
    Returns:
        Display name
    """
    tier_names = {
        SubscriptionTier.FREE: "Free",
        SubscriptionTier.BASIC: "Basic Pro",
        SubscriptionTier.ADVANCED: "Advanced Pro",
        SubscriptionTier.BUSINESS: "Business",
    }
    return tier_names.get(tier, "Unknown")


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def is_within_rate_limit(
    last_action_time: Optional[datetime],
    cooldown_seconds: int
) -> bool:
    """
    Check if action is within rate limit.
    
    Args:
        last_action_time: Time of last action
        cooldown_seconds: Cooldown period in seconds
        
    Returns:
        True if action is allowed, False otherwise
    """
    if not last_action_time:
        return True
    
    time_since_last = datetime.utcnow() - last_action_time
    return time_since_last.total_seconds() >= cooldown_seconds


def generate_bot_stats_summary(bot: Bot) -> str:
    """
    Generate a summary of bot statistics.
    
    Args:
        bot: Bot instance
        
    Returns:
        Formatted statistics string
    """
    from config.constants import EMOJI
    
    stats = [
        f"{EMOJI['subscribers']} **Subscribers:** {bot.subscriber_count}",
        f"{EMOJI['menu']} **Menus:** {len(bot.button_menus)}",
        f"{EMOJI['form']} **Forms:** {len([f for f in bot.forms if f.is_active])}",
        f"{EMOJI['broadcast']} **Broadcasts:** {len(bot.broadcasts)}",
    ]
    
    return "\n".join(stats)


def encrypt_token(token: str) -> str:
    """
    Encrypt bot token for storage.
    
    Args:
        token: Plain text token
        
    Returns:
        Encrypted token
    """
    # TODO: Implement actual encryption using cryptography library
    # For now, just return as-is (MUST BE FIXED IN PRODUCTION!)
    from cryptography.fernet import Fernet
    from config.settings import settings
    
    if not settings.ENCRYPTION_KEY:
        # In development, just return plain text with warning
        print("⚠️ WARNING: No encryption key set! Token stored in plain text!")
        return token
    
    try:
        f = Fernet(settings.ENCRYPTION_KEY.encode())
        encrypted = f.encrypt(token.encode())
        return encrypted.decode()
    except Exception as e:
        print(f"⚠️ Encryption error: {e}")
        return token


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt bot token from storage.
    
    Args:
        encrypted_token: Encrypted token
        
    Returns:
        Plain text token
    """
    # TODO: Implement actual decryption
    from cryptography.fernet import Fernet
    from config.settings import settings
    
    if not settings.ENCRYPTION_KEY:
        return encrypted_token
    
    try:
        f = Fernet(settings.ENCRYPTION_KEY.encode())
        decrypted = f.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"⚠️ Decryption error: {e}")
        return encrypted_token


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
