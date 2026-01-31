"""
Bot Setup Service

Initializes newly created bots with webhooks, commands, and configuration.
"""

import logging
from telegram import Bot, BotCommand
from telegram.error import TelegramError
from config.settings import settings

logger = logging.getLogger(__name__)


async def setup_created_bot(bot_model, bot_token):
    """
    Initialize a newly created bot with webhook and commands.
    
    Args:
        bot_model: Bot database model instance
        bot_token: Decrypted bot token
        
    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        # Initialize Telegram Bot
        telegram_bot = Bot(token=bot_token)
        
        # 1. Set webhook
        webhook_url = f"{settings.WEBHOOK_URL}/webhook/{bot_model.bot_username}"
        
        logger.info(f"Setting webhook for @{bot_model.bot_username} to {webhook_url}")
        
        await telegram_bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True  # Clear any pending updates
        )
        
        # 2. Set bot commands (visible in Telegram menu)
        commands = [
            BotCommand("start", "🏠 Start the bot"),
            BotCommand("broadcast", "📣 Send broadcast to subscribers"),
            BotCommand("subscribers", "👥 View your subscribers"),
            BotCommand("stats", "📊 View bot statistics"),
            BotCommand("menu", "🎨 Create button menus"),
            BotCommand("settings", "⚙️ Bot settings"),
            BotCommand("help", "❓ Get help"),
        ]
        
        await telegram_bot.set_my_commands(commands)
        logger.info(f"Set {len(commands)} commands for @{bot_model.bot_username}")
        
        # 3. Set bot description (shown in bot info)
        description = (
            f"Welcome to {bot_model.bot_name}! 🎉\n\n"
            f"This bot is powered by ChatFuel - manage your subscribers "
            f"and broadcasts easily.\n\n"
            f"Use /start to begin!"
        )
        
        await telegram_bot.set_my_description(description)
        
        # 4. Set short description (shown in chat list)
        short_description = f"Powered by ChatFuel 🚀"
        await telegram_bot.set_my_short_description(short_description)
        
        logger.info(f"✅ Bot @{bot_model.bot_username} setup completed successfully")
        
        return True
        
    except TelegramError as e:
        logger.error(f"❌ Telegram error setting up bot @{bot_model.bot_username}: {e}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error setting up bot @{bot_model.bot_username}: {e}")
        return False


async def remove_webhook(bot_token, bot_username):
    """
    Remove webhook from a bot (used when bot is deleted).
    
    Args:
        bot_token: Decrypted bot token
        bot_username: Bot username for logging
        
    Returns:
        bool: True if successful
    """
    try:
        telegram_bot = Bot(token=bot_token)
        await telegram_bot.delete_webhook(drop_pending_updates=True)
        logger.info(f"✅ Webhook removed for @{bot_username}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error removing webhook for @{bot_username}: {e}")
        return False


async def test_bot_token(bot_token):
    """
    Test if a bot token is valid by calling getMe.
    
    Args:
        bot_token: Bot token to test
        
    Returns:
        tuple: (is_valid, bot_info, error_message)
    """
    try:
        telegram_bot = Bot(token=bot_token)
        bot_info = await telegram_bot.get_me()
        
        return True, {
            'id': bot_info.id,
            'username': bot_info.username,
            'first_name': bot_info.first_name,
            'can_join_groups': bot_info.can_join_groups,
            'can_read_all_group_messages': bot_info.can_read_all_group_messages,
        }, None
        
    except TelegramError as e:
        return False, None, str(e)
        
    except Exception as e:
        return False, None, f"Unknown error: {str(e)}"


async def update_bot_info(bot_model, bot_token):
    """
    Update bot information from Telegram.
    
    Args:
        bot_model: Bot database model
        bot_token: Decrypted bot token
        
    Returns:
        bool: True if successful
    """
    try:
        telegram_bot = Bot(token=bot_token)
        bot_info = await telegram_bot.get_me()
        
        # Update bot info in database
        bot_model.bot_name = bot_info.first_name
        bot_model.bot_username = bot_info.username
        bot_model.bot_id = bot_info.id
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating bot info: {e}")
        return False


def generate_bot_start_link(bot_username):
    """
    Generate a t.me link to start a bot.
    
    Args:
        bot_username: Bot username (without @)
        
    Returns:
        str: t.me link
    """
    return f"https://t.me/{bot_username}?start=setup"


def get_webhook_url(bot_username):
    """
    Get webhook URL for a bot.
    
    Args:
        bot_username: Bot username
        
    Returns:
        str: Webhook URL
    """
    return f"{settings.WEBHOOK_URL}/webhook/{bot_username}"
