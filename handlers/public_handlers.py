"""
Public Handlers

Handles all interactions from regular subscribers (non-owners) in created bots.
Shows only the content that the bot owner has created.
"""

import logging
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.orm import Session

from database.models import Bot as BotModel, Subscriber
from utils.helpers import escape_markdown
from config.constants import EMOJI

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
            await handle_public_start(bot_model, update, telegram_bot, db)
        
        elif text == '/help':
            await handle_public_help(bot_model, update, telegram_bot, db)
        
        else:
            # Check if this matches any custom command (Phase 3)
            # For now, just echo unknown command
            await handle_public_unknown(bot_model, update, telegram_bot)
    
    # Handle callback queries
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith('public_about_'):
            await handle_public_about(bot_model, update, telegram_bot, db)
        
        elif data.startswith('public_help_'):
            await handle_public_help(bot_model, update, telegram_bot, db)
        
        elif data.startswith('public_back_'):
            await handle_public_start(bot_model, update, telegram_bot, db)
        
        # TODO: Handle custom button clicks (Phase 3)
        # elif data.startswith('menu_'):
        #     await handle_menu_button(bot_model, update, telegram_bot, db, data)


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
