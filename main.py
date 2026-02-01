"""
ChatFuel Bot - Main Entry Point

Single-server architecture:
  - In production (USE_WEBHOOK=true):
      One Flask app on Railway's PORT serves every webhook route.
      The main bot's token is used as its URL path, exactly like
      python-telegram-bot expects, but the actual HTTP server is Flask.

  - In development (USE_WEBHOOK=false):
      Main bot runs with polling (no HTTP needed for it).
      Flask still starts so created-bot webhooks work locally.
"""

import logging
import asyncio
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

# The single Flask app that serves all webhooks
from handlers.webhook_router import app as flask_app, set_ptb_application, get_ptb_loop

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Something went wrong. Please try again later."
            )
        except Exception:
            pass


def build_application() -> Application:
    """Build and return the python-telegram-bot Application with all handlers."""
    application = Application.builder().token(settings.BOT_TOKEN).build()

    # --- Command handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", show_help_menu))
    application.add_handler(CommandHandler("mybots", my_bots_command))

    # --- Conversation handler (add bot flow) ---
    application.add_handler(add_bot_conversation)

    # --- Callback handlers: main menu ---
    application.add_handler(CallbackQueryHandler(
        main_menu_callback,
        pattern='^(main_|back_to_main)'
    ))

    # --- Callback handlers: bot management ---
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

    # --- Callback handlers: help menu ---
    application.add_handler(CallbackQueryHandler(show_help_quickstart,   pattern='^help_quickstart$'))
    application.add_handler(CallbackQueryHandler(show_help_commands,     pattern='^help_commands$'))
    application.add_handler(CallbackQueryHandler(show_help_tutorials,    pattern='^help_tutorials$'))
    application.add_handler(CallbackQueryHandler(show_help_faq,          pattern='^help_faq$'))
    application.add_handler(CallbackQueryHandler(show_help_contact,      pattern='^help_contact$'))

    # --- Callback handlers: tutorials ---
    application.add_handler(CallbackQueryHandler(show_tutorial_first_bot, pattern='^tutorial_first_bot$'))
    application.add_handler(CallbackQueryHandler(show_tutorial_tokens,    pattern='^tutorial_tokens$'))
    application.add_handler(CallbackQueryHandler(show_tutorial_sharing,   pattern='^tutorial_sharing$'))

    # --- Global error handler ---
    application.add_error_handler(error_handler)

    return application


async def set_main_bot_webhook(application: Application):
    """Tell Telegram where to POST updates for the main bot."""
    webhook_url = f"{settings.WEBHOOK_URL}/{settings.BOT_TOKEN}"
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"Main bot webhook set to: {webhook_url}")


def main():
    """Start the bot."""
    try:
        validate_settings()
        logger.info("Settings validated successfully")

        init_db()
        logger.info("Database initialized successfully")

        # Build the main-bot Application (registers all handlers)
        application = build_application()

        # Hand it to the webhook router so it can forward updates
        set_ptb_application(application)

        logger.info("Starting ChatFuel Bot...")
        logger.info(f"Environment : {settings.ENVIRONMENT}")
        logger.info(f"Bot username: @{settings.BOT_USERNAME}")
        logger.info(f"Port        : {settings.WEBHOOK_PORT}")

        if settings.USE_WEBHOOK:
            # --- PRODUCTION ---
            # Initialize the Application (required before process_update works)
            # and tell Telegram where to POST updates.
            # Use the same long-lived loop that webhook_router reuses per-request;
            # PTB's httpx client binds to this loop and must not see it closed.
            ptb_loop = get_ptb_loop()
            ptb_loop.run_until_complete(application.initialize())
            ptb_loop.run_until_complete(set_main_bot_webhook(application))

            # Start the single Flask server.  It handles:
            #   POST /webhook/<username>  -> created bots
            #   POST /<token>             -> main bot (forwarded to Application)
            #   GET  /health
            logger.info("Starting Flask webhook server (production)...")
            flask_app.run(
                host='0.0.0.0',
                port=settings.WEBHOOK_PORT,
                debug=False
            )

        else:
            # --- DEVELOPMENT ---
            # Main bot uses polling (no HTTP needed for it).
            # But we still start Flask so created-bot webhooks work locally
            # if you ngrok or similar tunnel is set up.
            from threading import Thread

            def run_flask():
                logger.info("Starting Flask webhook server (dev, background)...")
                flask_app.run(host='0.0.0.0', port=settings.WEBHOOK_PORT, debug=False)

            flask_thread = Thread(target=run_flask, daemon=True)
            flask_thread.start()

            logger.info("Running main bot with polling (development)...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == '__main__':
    main()
