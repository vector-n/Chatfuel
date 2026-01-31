"""
ChatFuel Bot - Main Entry Point

A Telegram bot manager that helps users create and manage their own broadcast bots.
Includes webhook server for handling created bots.
"""

import logging
import asyncio
from threading import Thread
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

# Configuration
from config.settings import settings, validate_settings
from config.constants import CALLBACK_PREFIX

# Database
from database import init_db

# Main bot handlers
from handlers.start import start_command, main_menu_callback
from handlers.bot_management import (
    my_bots_command,
    add_bot_conversation,
    select_bot_callback,
    delete_bot_callback,
    confirm_delete_bot,
)
from handlers.help import (
    show_help_menu,
    show_help_quickstart,
    show_help_commands,
    show_help_tutorials,
    show_help_faq,
    show_help_contact,
    show_tutorial_first_bot,
    show_tutorial_tokens,
    show_tutorial_sharing,
)

# Webhook server for created bots
from handlers.webhook_router import app as webhook_app

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


def start_webhook_server_thread():
    """Start Flask webhook server in a separate thread."""
    logger.info("🌐 Starting webhook server for created bots...")
    
    # Run Flask app
    webhook_app.run(
        host='0.0.0.0',
        port=settings.WEBHOOK_PORT,
        debug=False
    )


def main():
    """Start the bot."""
    try:
        # Validate settings
        validate_settings()
        logger.info("✅ Settings validated successfully")
        
        # Initialize database
        init_db()
        logger.info("✅ Database initialized successfully")
        
        # Create application for main bot
        application = Application.builder().token(settings.BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", show_help_menu))
        application.add_handler(CommandHandler("mybots", my_bots_command))
        
        # Add conversation handler for adding bots
        application.add_handler(add_bot_conversation)
        
        # Add callback query handlers - Main menu
        application.add_handler(CallbackQueryHandler(
            main_menu_callback,
            pattern='^(main_|back_to_main)'
        ))
        
        # Bot management callbacks
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
        
        # Help menu callbacks
        application.add_handler(CallbackQueryHandler(
            show_help_quickstart,
            pattern='^help_quickstart$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            show_help_commands,
            pattern='^help_commands$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            show_help_tutorials,
            pattern='^help_tutorials$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            show_help_faq,
            pattern='^help_faq$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            show_help_contact,
            pattern='^help_contact$'
        ))
        
        # Tutorial callbacks
        application.add_handler(CallbackQueryHandler(
            show_tutorial_first_bot,
            pattern='^tutorial_first_bot$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            show_tutorial_tokens,
            pattern='^tutorial_tokens$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            show_tutorial_sharing,
            pattern='^tutorial_sharing$'
        ))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        logger.info("🚀 Starting ChatFuel Bot...")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Bot username: @{settings.BOT_USERNAME}")
        
        if settings.USE_WEBHOOK:
            # Production mode with webhook
            logger.info(f"📡 Webhook URL: {settings.WEBHOOK_URL}")
            
            # Start webhook server in background thread for created bots
            webhook_thread = Thread(target=start_webhook_server_thread, daemon=True)
            webhook_thread.start()
            
            # Start main bot with webhook
            application.run_webhook(
                listen="0.0.0.0",
                port=8080,  # Main bot on port 8080
                url_path=settings.BOT_TOKEN,
                webhook_url=f"{settings.WEBHOOK_URL}/{settings.BOT_TOKEN}"
            )
        else:
            # Development mode with polling
            logger.info("🔄 Using polling mode (development)")
            
            # Start webhook server in background for created bots (still needed)
            webhook_thread = Thread(target=start_webhook_server_thread, daemon=True)
            webhook_thread.start()
            
            # Run main bot with polling
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise


if __name__ == '__main__':
    main()
