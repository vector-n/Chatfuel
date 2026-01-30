"""Permission and feature checking utilities."""

from typing import Tuple, Optional
from sqlalchemy.orm import Session
from database.models import User, Bot, BotAdmin
from config.constants import TIER_LIMITS, SubscriptionTier, AdminRole, ROLE_PERMISSIONS


def check_premium_feature(
    user: User,
    feature: str
) -> Tuple[bool, Optional[str]]:
    """
    Check if user has access to a premium feature.
    
    Args:
        user: User instance
        feature: Feature name (key in TIER_LIMITS)
        
    Returns:
        Tuple of (has_access, error_message)
    """
    tier = user.premium_tier
    limits = TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])
    
    # Check boolean features
    if feature in limits:
        has_access = limits[feature]
        if isinstance(has_access, bool):
            if not has_access:
                return False, f"This feature requires a premium subscription"
            return True, None
    
    return True, None


def check_limit(
    user: User,
    limit_type: str,
    current_count: int
) -> Tuple[bool, Optional[str]]:
    """
    Check if user is within limits for a resource.
    
    Args:
        user: User instance
        limit_type: Type of limit (e.g., 'max_bots', 'max_custom_menus')
        current_count: Current count of the resource
        
    Returns:
        Tuple of (within_limit, error_message)
    """
    tier = user.premium_tier
    limits = TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])
    
    max_allowed = limits.get(limit_type, 0)
    
    # -1 means unlimited
    if max_allowed == -1:
        return True, None
    
    if current_count >= max_allowed:
        from utils.helpers import get_tier_name
        return False, (
            f"You've reached your limit ({max_allowed}) for this resource on the "
            f"{get_tier_name(tier)} plan. Upgrade to increase your limits!"
        )
    
    return True, None


def can_user_manage_bot(
    db: Session,
    user_id: int,
    bot_id: int,
    action: str = 'can_edit_settings'
) -> Tuple[bool, Optional[str]]:
    """
    Check if user can perform an action on a bot.
    
    Args:
        db: Database session
        user_id: User ID
        bot_id: Bot ID
        action: Action to check (from ROLE_PERMISSIONS)
        
    Returns:
        Tuple of (can_perform, error_message)
    """
    # Check if user is the bot owner
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        return False, "Bot not found"
    
    if bot.user_id == user_id:
        # Owner can do everything
        return True, None
    
    # Check if user is an admin
    admin = db.query(BotAdmin).filter(
        BotAdmin.bot_id == bot_id,
        BotAdmin.user_id == user_id
    ).first()
    
    if not admin:
        return False, "You don't have permission to manage this bot"
    
    # Check role permissions
    role_perms = ROLE_PERMISSIONS.get(admin.role, {})
    can_perform = role_perms.get(action, False)
    
    if not can_perform:
        return False, f"Your role ({admin.role}) doesn't allow this action"
    
    return True, None


def get_remaining_quota(user: User, quota_type: str, current_usage: int) -> int:
    """
    Get remaining quota for a resource.
    
    Args:
        user: User instance
        quota_type: Type of quota (e.g., 'max_bots')
        current_usage: Current usage count
        
    Returns:
        Remaining quota (-1 for unlimited)
    """
    tier = user.premium_tier
    limits = TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])
    
    max_allowed = limits.get(quota_type, 0)
    
    if max_allowed == -1:
        return -1  # Unlimited
    
    remaining = max_allowed - current_usage
    return max(0, remaining)


def require_premium(tier: str = SubscriptionTier.BASIC):
    """
    Decorator to require premium subscription for a handler.
    
    Args:
        tier: Minimum required tier
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            from database import get_db
            from utils.helpers import get_user_or_create
            
            db = next(get_db())
            try:
                user = get_user_or_create(db, update.effective_user)
                
                tier_order = [
                    SubscriptionTier.FREE,
                    SubscriptionTier.BASIC,
                    SubscriptionTier.ADVANCED,
                    SubscriptionTier.BUSINESS
                ]
                
                required_level = tier_order.index(tier)
                user_level = tier_order.index(user.premium_tier)
                
                if user_level < required_level:
                    from utils.keyboards import create_premium_upsell_keyboard
                    from utils.helpers import get_tier_name
                    
                    await update.message.reply_text(
                        f"💎 **Premium Feature**\n\n"
                        f"This feature requires {get_tier_name(tier)} subscription.\n\n"
                        f"Upgrade to unlock this and many more features!",
                        reply_markup=create_premium_upsell_keyboard(),
                        parse_mode='Markdown'
                    )
                    return
                
                return await func(update, context, *args, **kwargs)
            finally:
                db.close()
        
        return wrapper
    return decorator


def get_user_tier_limits(user: User) -> dict:
    """
    Get all limits for user's current tier.
    
    Args:
        user: User instance
        
    Returns:
        Dictionary of limits
    """
    return TIER_LIMITS.get(user.premium_tier, TIER_LIMITS[SubscriptionTier.FREE])


def is_feature_available(user: User, feature: str) -> bool:
    """
    Check if a feature is available for user's tier.
    
    Args:
        user: User instance
        feature: Feature name
        
    Returns:
        True if available, False otherwise
    """
    limits = get_user_tier_limits(user)
    return limits.get(feature, False)
