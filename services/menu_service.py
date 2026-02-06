"""
Menu Service - Phase 3

Handles advanced menu operations with tier limit enforcement.
"""

import logging
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import (
    Bot as BotModel,
    ButtonMenu,
    MenuButton,
    MenuNavigationLog,
    MenuTemplate,
    UserMenuContext,
    User
)
from config.constants import TIER_LIMITS

logger = logging.getLogger(__name__)


# ==================== TIER LIMIT CHECKS ====================

def check_menu_limit(bot_id: int, user_tier: str, db: Session) -> Tuple[bool, str]:
    """
    Check if user can create more menus based on their tier.
    
    Returns:
        Tuple[bool, str]: (can_create, error_message)
    """
    # Get tier limit
    limits = TIER_LIMITS.get(user_tier, TIER_LIMITS['free'])
    max_menus = limits['max_custom_menus']
    
    # -1 means unlimited
    if max_menus == -1:
        return (True, "")
    
    # Count current menus
    current_count = db.query(ButtonMenu).filter(
        ButtonMenu.bot_id == bot_id
    ).count()
    
    if current_count >= max_menus:
        return (False, f"Menu limit reached ({max_menus} menus). Upgrade to create more menus.")
    
    return (True, "")


def check_button_limit(menu_id: int, user_tier: str, db: Session) -> Tuple[bool, str]:
    """
    Check if user can add more buttons to a menu based on their tier.
    
    Returns:
        Tuple[bool, str]: (can_create, error_message)
    """
    # Get tier limit
    limits = TIER_LIMITS.get(user_tier, TIER_LIMITS['free'])
    max_buttons = limits['max_buttons_per_menu']
    
    # -1 means unlimited
    if max_buttons == -1:
        return (True, "")
    
    # Count current buttons in menu
    current_count = db.query(MenuButton).filter(
        MenuButton.menu_id == menu_id,
        MenuButton.is_active == True
    ).count()
    
    if current_count >= max_buttons:
        return (False, f"Button limit reached ({max_buttons} buttons per menu). Upgrade for more buttons.")
    
    return (True, "")


def get_user_tier(bot_id: int, db: Session) -> str:
    """Get the subscription tier of the bot owner."""
    bot = db.query(BotModel).filter(BotModel.id == bot_id).first()
    if not bot:
        return 'free'
    
    user = db.query(User).filter(User.id == bot.user_id).first()
    if not user:
        return 'free'
    
    return user.premium_tier or 'free'


# ==================== MENU CRUD ====================

def create_menu(
    db: Session,
    bot_id: int,
    menu_name: str,
    menu_description: Optional[str] = None,
    parent_menu_id: Optional[int] = None,
    is_default: bool = False
) -> Tuple[Optional[ButtonMenu], Optional[str]]:
    """
    Create a new menu with tier limit checking.
    
    Returns:
        Tuple[Optional[ButtonMenu], Optional[str]]: (menu, error_message)
    """
    # Check tier limit
    user_tier = get_user_tier(bot_id, db)
    can_create, error_msg = check_menu_limit(bot_id, user_tier, db)
    
    if not can_create:
        return (None, error_msg)
    
    # Create menu
    menu = ButtonMenu(
        bot_id=bot_id,
        menu_name=menu_name,
        menu_description=menu_description,
        parent_menu_id=parent_menu_id,
        is_default_menu=is_default
    )
    
    db.add(menu)
    db.commit()
    db.refresh(menu)
    
    logger.info(f"✅ Menu '{menu_name}' created for bot {bot_id}")
    return (menu, None)


def create_button(
    db: Session,
    menu_id: int,
    button_text: str,
    action_type: str,
    action_config: Dict,
    emoji: Optional[str] = None,
    row: int = 0,
    col: int = 0,
    button_type: str = 'callback',
    target_menu_id: Optional[int] = None,
    requires_premium: bool = False
) -> Tuple[Optional[MenuButton], Optional[str]]:
    """
    Create a new button with tier limit checking.
    
    Returns:
        Tuple[Optional[MenuButton], Optional[str]]: (button, error_message)
    """
    # Get bot_id from menu
    menu = db.query(ButtonMenu).filter(ButtonMenu.id == menu_id).first()
    if not menu:
        return (None, "Menu not found")
    
    # Check tier limit
    user_tier = get_user_tier(menu.bot_id, db)
    can_create, error_msg = check_button_limit(menu_id, user_tier, db)
    
    if not can_create:
        return (None, error_msg)
    
    # Create button
    button = MenuButton(
        menu_id=menu_id,
        button_text=button_text,
        emoji=emoji,
        row_position=row,
        column_position=col,
        button_type=button_type,
        action_type=action_type,
        action_config=action_config,
        target_menu_id=target_menu_id,
        visible_to_premium_only=requires_premium
    )
    
    db.add(button)
    db.commit()
    db.refresh(button)
    
    logger.info(f"✅ Button '{button_text}' created in menu {menu_id}")
    return (button, None)


def get_menu(db: Session, menu_id: int) -> Optional[ButtonMenu]:
    """Get a menu by ID."""
    return db.query(ButtonMenu).filter(ButtonMenu.id == menu_id).first()


def get_bot_menus(db: Session, bot_id: int, include_inactive: bool = False) -> List[ButtonMenu]:
    """Get all menus for a bot."""
    query = db.query(ButtonMenu).filter(ButtonMenu.bot_id == bot_id)
    
    if not include_inactive:
        query = query.filter(ButtonMenu.is_active == True)
    
    return query.all()


def get_menu_buttons(db: Session, menu_id: int, include_inactive: bool = False) -> List[MenuButton]:
    """Get all buttons for a menu."""
    query = db.query(MenuButton).filter(MenuButton.menu_id == menu_id)
    
    if not include_inactive:
        query = query.filter(MenuButton.is_active == True)
    
    query = query.order_by(MenuButton.row_position, MenuButton.column_position, MenuButton.sort_order)
    
    return query.all()


def get_root_menus(db: Session, bot_id: int) -> List[ButtonMenu]:
    """Get all root-level menus (no parent) for a bot."""
    return db.query(ButtonMenu).filter(
        ButtonMenu.bot_id == bot_id,
        ButtonMenu.parent_menu_id.is_(None),
        ButtonMenu.is_active == True
    ).all()


def get_child_menus(db: Session, parent_menu_id: int) -> List[ButtonMenu]:
    """Get all child menus of a parent menu."""
    return db.query(ButtonMenu).filter(
        ButtonMenu.parent_menu_id == parent_menu_id,
        ButtonMenu.is_active == True
    ).all()


def get_default_menu(db: Session, bot_id: int) -> Optional[ButtonMenu]:
    """Get the default menu for a bot (shown on /start)."""
    return db.query(ButtonMenu).filter(
        ButtonMenu.bot_id == bot_id,
        ButtonMenu.is_default_menu == True,
        ButtonMenu.is_active == True
    ).first()


# ==================== MENU NAVIGATION ====================

def get_user_context(db: Session, bot_id: int, subscriber_id: int) -> Optional[UserMenuContext]:
    """Get user's current menu context."""
    return db.query(UserMenuContext).filter(
        UserMenuContext.bot_id == bot_id,
        UserMenuContext.subscriber_id == subscriber_id
    ).first()


def set_user_context(
    db: Session,
    bot_id: int,
    subscriber_id: int,
    menu_id: int,
    session_id: Optional[str] = None
):
    """Set user's current menu context."""
    context = get_user_context(db, bot_id, subscriber_id)
    
    if context:
        # Update existing context
        # Build menu path
        menu_path = context.menu_path or []
        if menu_id not in menu_path:
            menu_path.append(menu_id)
        
        context.current_menu_id = menu_id
        context.menu_path = menu_path
        context.session_id = session_id
    else:
        # Create new context
        context = UserMenuContext(
            bot_id=bot_id,
            subscriber_id=subscriber_id,
            current_menu_id=menu_id,
            menu_path=[menu_id],
            session_id=session_id
        )
        db.add(context)
    
    db.commit()


def go_back(db: Session, bot_id: int, subscriber_id: int) -> Optional[int]:
    """
    Navigate back to previous menu in the path.
    
    Returns:
        Optional[int]: Previous menu ID, or None if at root
    """
    context = get_user_context(db, bot_id, subscriber_id)
    
    if not context or not context.menu_path or len(context.menu_path) <= 1:
        return None
    
    # Remove current menu from path
    context.menu_path.pop()
    
    # Get previous menu
    previous_menu_id = context.menu_path[-1] if context.menu_path else None
    context.current_menu_id = previous_menu_id
    
    db.commit()
    
    return previous_menu_id


def get_breadcrumb(db: Session, bot_id: int, subscriber_id: int) -> List[ButtonMenu]:
    """Get the breadcrumb trail of menus user has navigated through."""
    context = get_user_context(db, bot_id, subscriber_id)
    
    if not context or not context.menu_path:
        return []
    
    menus = db.query(ButtonMenu).filter(
        ButtonMenu.id.in_(context.menu_path)
    ).all()
    
    # Sort by path order
    menu_dict = {m.id: m for m in menus}
    return [menu_dict[mid] for mid in context.menu_path if mid in menu_dict]


# ==================== ANALYTICS ====================

def log_navigation(
    db: Session,
    bot_id: int,
    subscriber_id: int,
    menu_id: Optional[int] = None,
    button_id: Optional[int] = None,
    action_taken: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Log menu navigation for analytics."""
    log = MenuNavigationLog(
        bot_id=bot_id,
        subscriber_id=subscriber_id,
        menu_id=menu_id,
        button_id=button_id,
        action_taken=action_taken,
        session_id=session_id
    )
    
    db.add(log)
    db.commit()


def get_menu_stats(db: Session, menu_id: int) -> Dict:
    """Get statistics for a menu."""
    # Total views
    total_views = db.query(MenuNavigationLog).filter(
        MenuNavigationLog.menu_id == menu_id
    ).count()
    
    # Unique visitors
    unique_visitors = db.query(func.count(func.distinct(MenuNavigationLog.subscriber_id))).filter(
        MenuNavigationLog.menu_id == menu_id
    ).scalar()
    
    # Button clicks per button
    button_clicks = db.query(
        MenuNavigationLog.button_id,
        func.count(MenuNavigationLog.id).label('click_count')
    ).filter(
        MenuNavigationLog.menu_id == menu_id,
        MenuNavigationLog.button_id.isnot(None)
    ).group_by(MenuNavigationLog.button_id).all()
    
    return {
        'total_views': total_views,
        'unique_visitors': unique_visitors,
        'button_clicks': {btn_id: count for btn_id, count in button_clicks}
    }


# ==================== MENU TEMPLATES ====================

def get_templates(db: Session, category: Optional[str] = None, public_only: bool = True) -> List[MenuTemplate]:
    """Get menu templates."""
    query = db.query(MenuTemplate)
    
    if public_only:
        query = query.filter(MenuTemplate.is_public == True)
    
    if category:
        query = query.filter(MenuTemplate.category == category)
    
    return query.order_by(MenuTemplate.usage_count.desc()).all()


def apply_template(db: Session, template_id: int, bot_id: int) -> Tuple[bool, str]:
    """
    Apply a menu template to a bot.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    template = db.query(MenuTemplate).filter(MenuTemplate.id == template_id).first()
    
    if not template:
        return (False, "Template not found")
    
    # Check tier limits
    user_tier = get_user_tier(bot_id, db)
    
    # TODO: Create menus and buttons from template.menu_structure
    # This will be a recursive function to create the menu tree
    
    # Increment usage count
    template.usage_count += 1
    db.commit()
    
    return (True, "Template applied successfully")
