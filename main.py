"""
ChatFuel Bot - Main Entry Point

A Telegram bot manager that helps users create and manage their own broadcast bots.
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Configuration
from config.settings import settings, validate_settings
from config.constants import CALLBACK_PREFIX

# Database
from database import init_db

# Handlers
from handlers.start import start_command, main_menu_callback
from handlers.bot_management import (
    my_bots_command,
    add_bot_conversation,
    select_bot_callback,
    delete_bot_callback,
    confirm_delete_bot,
)
from handlers.help import show_help_menu

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Send error message to user if possible
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
        except Exception:
            pass


def main():
    """Start the bot."""
    try:
        # Validate settings
        validate_settings()
        logger.info("✅ Settings validated successfully")
        
        # Initialize database
        init_db()
        logger.info("✅ Database initialized successfully")
        
        # Create application
        application = Application.builder().token(settings.BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", show_help_menu))
        application.add_handler(CommandHandler("mybots", my_bots_command))
        
        # Add conversation handler for adding bots
        application.add_handler(add_bot_conversation)
        
        # Add callback query handlers
        application.add_handler(CallbackQueryHandler(
            main_menu_callback,
            pattern='^(main_|back_to_main)'
        ))
        
        application.add_handler(CallbackQueryHandler(
            select_bot_callback,
            pattern=f'^({CALLBACK_PREFIX["bot_select"]}|bot_manage_)'
        ))
        
        application.add_handler(CallbackQueryHandler(
            delete_bot_callback,
            pattern=f'^{CALLBACK_PREFIX["bot_delete"]}'
        ))
        
        application.add_handler(CallbackQueryHandler(
            confirm_delete_bot,
            pattern='^confirm_delete_'
        ))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("🚀 Starting ChatFuel Bot...")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Bot username: @{settings.BOT_USERNAME}")
        
        if settings.USE_WEBHOOK:
            # Production mode with webhook
            application.run_webhook(
                listen="0.0.0.0",
                port=settings.WEBHOOK_PORT,
                url_path=settings.BOT_TOKEN,
                webhook_url=f"{settings.WEBHOOK_URL}/{settings.BOT_TOKEN}"
            )
        else:
            # Development mode with polling
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise


if __name__ == '__main__':
    main()
