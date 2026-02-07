"""
Menu Display Handlers - Phase 3B

Handles displaying button menus to bot subscribers and processing their interactions.
This is the public-facing menu system that subscribers see and interact with.
"""

import logging
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.orm import Session

from database.models import Bot as BotModel, Subscriber, MenuButton
from services.menu_service import (
    get_default_menu,
    get_menu,
    get_menu_buttons,
    set_user_context,
    go_back,
    get_breadcrumb,
    log_navigation
)
from utils.helpers import escape_markdown

logger = logging.getLogger(__name__)


async def show_menu_to_subscriber(
    bot_model: BotModel,
    menu_id: int,
    update: Update,
    telegram_bot: Bot,
    db: Session,
    subscriber: Subscriber,
    edit_message: bool = True
):
    """
    Display a menu to a subscriber with its buttons.
    
    Args:
        bot_model: Bot database model
        menu_id: ID of menu to display
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        subscriber: Subscriber model
        edit_message: Whether to edit existing message or send new one
    """
    menu = get_menu(db, menu_id)
    if not menu:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Menu not found."
        )
        return
    
    # Get menu buttons
    buttons = get_menu_buttons(db, menu_id, include_inactive=False)
    
    # Build menu text
    text = ""
    if menu.menu_description:
        text = f"{menu.menu_description}\n\n"
    else:
        text = f"**{escape_markdown(menu.menu_name)}**\n\n"
    
    if not buttons:
        text += "_This menu has no buttons yet._"
    
    # Build keyboard
    keyboard = []
    
    # Add menu buttons
    current_row = []
    current_row_position = -1
    
    for button in buttons:
        # Check if we need to start a new row
        if button.row_position != current_row_position:
            if current_row:
                keyboard.append(current_row)
            current_row = []
            current_row_position = button.row_position
        
        # Build button
        button_text = button.button_text
        if button.emoji:
            button_text = f"{button.emoji} {button_text}"
        
        if button.button_type == 'url':
            # URL buttons
            url = button.action_config.get('url', '')
            current_row.append(
                InlineKeyboardButton(button_text, url=url)
            )
        else:
            # Callback buttons
            callback_data = f"menu_btn_{button.id}_{menu_id}"
            current_row.append(
                InlineKeyboardButton(button_text, callback_data=callback_data)
            )
    
    # Add last row
    if current_row:
        keyboard.append(current_row)
    
    # Add back button if not root menu
    if menu.parent_menu_id:
        keyboard.append([
            InlineKeyboardButton(
                "🔙 Back",
                callback_data=f"menu_back_{menu_id}"
            )
        ])
    
    # Set user context
    set_user_context(db, bot_model.id, subscriber.id, menu_id)
    
    # Log navigation
    log_navigation(
        db=db,
        bot_id=bot_model.id,
        subscriber_id=subscriber.id,
        menu_id=menu_id,
        action_taken='view_menu'
    )
    
    # Send or edit message
    if edit_message and update.callback_query:
        try:
            await update.callback_query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Failed to edit message: {e}")
            # If edit fails, send new message
            await telegram_bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
                parse_mode='Markdown'
            )
    else:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
            parse_mode='Markdown'
        )


async def handle_menu_button_click(
    button_id: int,
    menu_id: int,
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session,
    subscriber: Subscriber
):
    """
    Handle when a subscriber clicks a menu button.
    
    Args:
        button_id: ID of clicked button
        menu_id: Current menu ID
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        subscriber: Subscriber model
    """
    button = db.query(MenuButton).filter(
        MenuButton.id == button_id,
        MenuButton.is_active == True
    ).first()
    
    if not button:
        await update.callback_query.answer("Button not found", show_alert=True)
        return
    
    # Log button click
    log_navigation(
        db=db,
        bot_id=bot_model.id,
        subscriber_id=subscriber.id,
        menu_id=menu_id,
        button_id=button_id,
        action_taken=f'click_{button.action_type}'
    )
    
    # Handle different action types
    if button.action_type == 'message':
        # Send message to user
        message = button.action_config.get('message', '')
        
        await update.callback_query.answer()
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            parse_mode='Markdown'
        )
        
        # Keep current menu visible
        await show_menu_to_subscriber(
            bot_model=bot_model,
            menu_id=menu_id,
            update=update,
            telegram_bot=telegram_bot,
            db=db,
            subscriber=subscriber,
            edit_message=False
        )
    
    elif button.action_type == 'submenu':
        # Navigate to submenu
        target_menu_id = button.action_config.get('target_menu_id') or button.target_menu_id
        
        if target_menu_id:
            await update.callback_query.answer()
            await show_menu_to_subscriber(
                bot_model=bot_model,
                menu_id=target_menu_id,
                update=update,
                telegram_bot=telegram_bot,
                db=db,
                subscriber=subscriber,
                edit_message=True
            )
        else:
            await update.callback_query.answer("Submenu not configured", show_alert=True)
    
    elif button.action_type == 'url':
        # URL buttons are handled by Telegram directly
        await update.callback_query.answer()
    
    elif button.action_type == 'form':
        # TODO: Launch form (Phase 4)
        await update.callback_query.answer("Form launching coming in Phase 4!", show_alert=True)
    
    elif button.action_type == 'webhook':
        # TODO: Trigger webhook (Phase 5)
        await update.callback_query.answer("Webhook triggers coming in Phase 5!", show_alert=True)
    
    else:
        await update.callback_query.answer("Unknown action type", show_alert=True)


async def handle_menu_back(
    menu_id: int,
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session,
    subscriber: Subscriber
):
    """
    Handle back button in menu navigation.
    
    Args:
        menu_id: Current menu ID
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        subscriber: Subscriber model
    """
    # Get previous menu from navigation path
    previous_menu_id = go_back(db, bot_model.id, subscriber.id)
    
    if previous_menu_id:
        await update.callback_query.answer()
        await show_menu_to_subscriber(
            bot_model=bot_model,
            menu_id=previous_menu_id,
            update=update,
            telegram_bot=telegram_bot,
            db=db,
            subscriber=subscriber,
            edit_message=True
        )
    else:
        # At root, show default menu or welcome message
        default_menu = get_default_menu(db, bot_model.id)
        
        if default_menu:
            await update.callback_query.answer()
            await show_menu_to_subscriber(
                bot_model=bot_model,
                menu_id=default_menu.id,
                update=update,
                telegram_bot=telegram_bot,
                db=db,
                subscriber=subscriber,
                edit_message=True
            )
        else:
            await update.callback_query.answer("Already at top level", show_alert=True)


async def handle_menu_command(
    command: str,
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session,
    subscriber: Subscriber
):
    """
    Handle menu command (e.g., /menu, /products).
    
    Args:
        command: Command string (e.g., "/menu")
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        subscriber: Subscriber model
    """
    from database.models import ButtonMenu
    
    # Find menu with this command trigger
    menu = db.query(ButtonMenu).filter(
        ButtonMenu.bot_id == bot_model.id,
        ButtonMenu.command_trigger == command,
        ButtonMenu.is_active == True
    ).first()
    
    if menu:
        await show_menu_to_subscriber(
            bot_model=bot_model,
            menu_id=menu.id,
            update=update,
            telegram_bot=telegram_bot,
            db=db,
            subscriber=subscriber,
            edit_message=False
        )
    else:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❓ Command not found: {command}"
        )


async def show_default_menu_on_start(
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session,
    subscriber: Subscriber
):
    """
    Show default menu when subscriber sends /start.
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        subscriber: Subscriber model
    """
    default_menu = get_default_menu(db, bot_model.id)
    
    if default_menu:
        # Show default menu
        await show_menu_to_subscriber(
            bot_model=bot_model,
            menu_id=default_menu.id,
            update=update,
            telegram_bot=telegram_bot,
            db=db,
            subscriber=subscriber,
            edit_message=False
        )
    else:
        # No default menu, show generic welcome
        bot_name = escape_markdown(bot_model.bot_name or bot_model.bot_username)
        welcome_message = f"Welcome to {bot_name}! 🎉\n\nYou're now subscribed!"
        
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_message,
            parse_mode='Markdown'
        )
