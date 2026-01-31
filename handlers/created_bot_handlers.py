"""
Created Bot Handlers

Main handlers for updates received by created bots.
Routes to admin or public handlers based on whether user is the bot owner.
"""

import logging
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from sqlalchemy.orm import Session

from database.models import Bot as BotModel, User, Subscriber
from services.subscriber_service import create_or_update_subscriber, get_subscriber_count
from handlers.admin_handlers import handle_admin_update
from handlers.public_handlers import handle_public_update
from utils.helpers import escape_markdown

logger = logging.getLogger(__name__)


async def handle_created_bot_update(
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session
):
    """
    Main entry point for all updates to created bots.
    Determines if user is owner or subscriber and routes accordingly.
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
    """
    try:
        # Get user who sent the update
        if update.message:
            user = update.message.from_user
        elif update.callback_query:
            user = update.callback_query.from_user
        else:
            logger.warning(f"Unknown update type for @{bot_model.bot_username}")
            return
        
        user_telegram_id = user.id
        
        # Track this interaction (update last_activity)
        subscriber = create_or_update_subscriber(
            db=db,
            bot_id=bot_model.id,
            user_telegram_id=user_telegram_id,
            user_info={
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'language': user.language_code,
            }
        )
        
        # Check if this user is the bot owner
        platform_user = db.query(User).filter(
            User.telegram_id == user_telegram_id
        ).first()
        
        is_owner = (
            platform_user is not None and 
            platform_user.id == bot_model.user_id
        )
        
        # Log the interaction
        user_type = "OWNER" if is_owner else "SUBSCRIBER"
        logger.info(f"👤 {user_type} interaction: {user_telegram_id} → @{bot_model.bot_username}")
        
        # Route to appropriate handler
        if is_owner:
            # Owner gets admin features
            await handle_admin_update(
                bot_model=bot_model,
                update=update,
                telegram_bot=telegram_bot,
                db=db,
                subscriber=subscriber
            )
        else:
            # Regular subscriber gets public features
            await handle_public_update(
                bot_model=bot_model,
                update=update,
                telegram_bot=telegram_bot,
                db=db,
                subscriber=subscriber
            )
            
    except TelegramError as e:
        logger.error(f"Telegram error handling update for @{bot_model.bot_username}: {e}")
        # Try to send error message to user
        try:
            await telegram_bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ An error occurred. Please try again later."
            )
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error handling update for @{bot_model.bot_username}: {e}", exc_info=True)
        # Try to send error message to user
        try:
            await telegram_bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Something went wrong. Please try again."
            )
        except:
            pass


async def handle_start_command(
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session,
    is_owner: bool
):
    """
    Handle /start command in created bot.
    Shows different interface for owner vs subscriber.
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        is_owner: Whether user is the bot owner
    """
    if is_owner:
        await send_admin_welcome(bot_model, update, telegram_bot, db)
    else:
        await send_public_welcome(bot_model, update, telegram_bot, db)


async def send_admin_welcome(
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session
):
    """
    Send admin welcome message with management menu.
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
    """
    subscriber_count = get_subscriber_count(bot_model.id, db)
    bot_name = escape_markdown(bot_model.bot_name or bot_model.bot_username)
    
    text = f"""👋 **Welcome back, Admin!**

🤖 **Bot:** {bot_name}
👥 **Subscribers:** {subscriber_count}

**Manage your bot:**
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📢 Send Broadcast", callback_data=f"admin_broadcast_{bot_model.id}"),
            InlineKeyboardButton(f"👥 Subscribers ({subscriber_count})", callback_data=f"admin_subs_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton("🎨 Button Menus", callback_data=f"admin_menus_{bot_model.id}"),
            InlineKeyboardButton("📝 Forms", callback_data=f"admin_forms_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton("⚙️ Bot Settings", callback_data=f"admin_settings_{bot_model.id}"),
            InlineKeyboardButton("📊 Analytics", callback_data=f"admin_analytics_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data=f"admin_help_{bot_model.id}"),
        ],
    ]
    
    await telegram_bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    logger.info(f"✅ Sent admin welcome to @{bot_model.bot_username}")


async def send_public_welcome(
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session
):
    """
    Send public welcome message to regular subscribers.
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
    """
    # Get custom welcome message (if owner set one)
    welcome_message = bot_model.welcome_message
    
    if not welcome_message:
        # Default welcome message
        bot_name = escape_markdown(bot_model.bot_name or bot_model.bot_username)
        welcome_message = f"Welcome to {bot_name}! 🎉\n\nYou're now subscribed!"
    
    # TODO: Get main menu from button_menus table (Phase 3)
    # For now, show a simple keyboard
    keyboard = [
        [
            InlineKeyboardButton("ℹ️ About", callback_data=f"public_about_{bot_model.id}"),
            InlineKeyboardButton("❓ Help", callback_data=f"public_help_{bot_model.id}"),
        ],
    ]
    
    await telegram_bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    logger.info(f"✅ Sent public welcome to subscriber in @{bot_model.bot_username}")


async def handle_unknown_command(
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    is_owner: bool
):
    """
    Handle unknown commands.
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        is_owner: Whether user is the bot owner
    """
    if is_owner:
        text = (
            "❓ Unknown command.\n\n"
            "Use /start to see the admin menu."
        )
    else:
        text = (
            "❓ I don't understand that command.\n\n"
            "Use /start to see available options."
        )
    
    await telegram_bot.send_message(
        chat_id=update.effective_chat.id,
        text=text
    )
