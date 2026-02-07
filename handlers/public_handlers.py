"""
Public Handlers - Phase 3B Enhanced

Handles all interactions from regular subscribers (non-owners) in created bots.
Shows only the content that the bot owner has created.

Now includes full menu system integration!
"""

import logging
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.orm import Session

from database.models import Bot as BotModel, Subscriber
from utils.helpers import escape_markdown
from config.constants import EMOJI
from handlers.menu_display_handlers import (
    show_default_menu_on_start,
    handle_menu_button_click,
    handle_menu_back,
    handle_menu_command
)

logger = logging.getLogger(__name__)


async def handle_public_update(
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session,
    subscriber: Subscriber
):
    """
    Route public (subscriber) updates to appropriate handlers.
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        subscriber: Subscriber model
    """
    # Handle messages
    if update.message:
        text = update.message.text
        
        if text == '/start':
            # Show default menu if configured, otherwise show welcome
            await show_default_menu_on_start(bot_model, update, telegram_bot, db, subscriber)
        
        elif text == '/help':
            await handle_public_help(bot_model, update, telegram_bot, db)
        
        elif text and text.startswith('/'):
            # Check if this is a custom menu command
            await handle_menu_command(text, bot_model, update, telegram_bot, db, subscriber)
        
        else:
            # Unknown text message
            await handle_public_unknown(bot_model, update, telegram_bot)
    
    # Handle callback queries
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Phase 3B: Menu button clicks
        if data.startswith('menu_btn_'):
            # Format: menu_btn_{button_id}_{menu_id}
            parts = data.split('_')
            if len(parts) >= 4:
                button_id = int(parts[2])
                menu_id = int(parts[3])
                await handle_menu_button_click(
                    button_id, menu_id, bot_model, update, telegram_bot, db, subscriber
                )
        
        elif data.startswith('menu_back_'):
            # Format: menu_back_{menu_id}
            parts = data.split('_')
            if len(parts) >= 3:
                menu_id = int(parts[2])
                await handle_menu_back(menu_id, bot_model, update, telegram_bot, db, subscriber)
        
        elif data.startswith('public_about_'):
            await handle_public_about(bot_model, update, telegram_bot, db)
        
        elif data.startswith('public_help_'):
            await handle_public_help(bot_model, update, telegram_bot, db)
        
        elif data.startswith('public_back_'):
            await show_default_menu_on_start(bot_model, update, telegram_bot, db, subscriber)


async def handle_public_start(bot_model, update, telegram_bot, db):
    """Show public welcome message and main menu."""
    from handlers.created_bot_handlers import send_public_welcome
    
    # If it's a callback query, delete old message and send new one
    if update.callback_query:
        try:
            await update.callback_query.message.delete()
        except:
            pass
    
    await send_public_welcome(bot_model, update, telegram_bot, db)


async def handle_public_about(bot_model, update, telegram_bot, db):
    """Show information about the bot."""
    bot_name = escape_markdown(bot_model.bot_name or bot_model.bot_username)
    description = bot_model.description or "No description available."
    
    # Get subscriber count
    from services.subscriber_service import get_subscriber_count
    subscriber_count = get_subscriber_count(bot_model.id, db)
    
    text = f"""ℹ️ **About {bot_name}**

{escape_markdown(description)}

👥 **Subscribers:** {subscriber_count}

_This bot is powered by ChatFuel_ 🚀
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data=f"public_back_{bot_model.id}")],
    ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


async def handle_public_help(bot_model, update, telegram_bot, db):
    """Show help for subscribers."""
    bot_name = escape_markdown(bot_model.bot_name or bot_model.bot_username)
    
    text = f"""❓ **Help**

Welcome to {bot_name}!

**Available Commands:**
• /start - Return to main menu
• /help - Show this help

_More features coming soon!_

If you have questions, please contact the bot owner.
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data=f"public_back_{bot_model.id}")],
    ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


async def handle_public_unknown(bot_model, update, telegram_bot):
    """Handle unknown commands from subscribers."""
    text = (
        "❓ I don't understand that command.\n\n"
        "Use /start to see available options."
    )
    
    await telegram_bot.send_message(
        chat_id=update.effective_chat.id,
        text=text
    )


async def handle_menu_button_click(bot_model, update, telegram_bot, db, button_data):
    """
    Handle clicks on custom menu buttons (Phase 3).
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        button_data: Callback data from button
    """
    # TODO: Implement in Phase 3
    # Will load button from database and execute its action
    pass


async def handle_form_submission(bot_model, update, telegram_bot, db, form_id):
    """
    Handle form submission from subscribers (Phase 4).
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        form_id: ID of the form
    """
    # TODO: Implement in Phase 4
    # Will show form questions and collect responses
    pass
