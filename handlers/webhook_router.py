"""
Webhook Router

Single Flask server that handles ALL webhooks on one port:
  - POST /{main_bot_token}          -> main bot updates (python-telegram-bot)
  - POST /webhook/<bot_username>    -> created bot updates (our custom routing)
  - GET  /health                    -> health check
  - GET  /webhook-info/<username>   -> debug info

Railway exposes exactly one port (PORT env var). Everything runs here.
"""

import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.error import TelegramError

from database import get_db
from database.models import Bot as BotModel
from utils.helpers import decrypt_token
from handlers.created_bot_handlers import handle_created_bot_update

logger = logging.getLogger(__name__)

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Created-bot webhooks
# ---------------------------------------------------------------------------

@app.route('/webhook/<bot_username>', methods=['POST'])
def webhook_handler(bot_username: str):
    """
    Webhook endpoint for a single created bot.
    Telegram POSTs updates here whenever someone interacts with @bot_username.
    """
    try:
        db = next(get_db())

        # 1. Find the bot
        bot_model = db.query(BotModel).filter(
            BotModel.bot_username == bot_username,
            BotModel.is_active == True
        ).first()

        if not bot_model:
            logger.warning(f"Webhook for unknown bot: @{bot_username}")
            return jsonify({"error": "Bot not found"}), 404

        # 2. Parse JSON body
        update_data = request.get_json(force=True)
        if not update_data:
            return jsonify({"error": "Empty update"}), 400

        # 3. Decrypt token
        bot_token = decrypt_token(bot_model.bot_token)
        if not bot_token:
            logger.error(f"Failed to decrypt token for @{bot_username}")
            return jsonify({"error": "Token error"}), 500

        # 4. Build Telegram objects
        telegram_bot = Bot(token=bot_token)
        update = Update.de_json(update_data, telegram_bot)

        # 5. Log
        if update.message:
            logger.info(f"[{bot_username}] msg from {update.message.from_user.id}: {update.message.text}")
        elif update.callback_query:
            logger.info(f"[{bot_username}] callback from {update.callback_query.from_user.id}: {update.callback_query.data}")

        # 6. Route -- run the async handler inside an event loop
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                handle_created_bot_update(
                    bot_model=bot_model,
                    update=update,
                    telegram_bot=telegram_bot,
                    db=db
                )
            )
        finally:
            loop.close()

        return jsonify({"ok": True}), 200

    except TelegramError as e:
        logger.error(f"Telegram error in webhook for @{bot_username}: {e}")
        return jsonify({"error": "Telegram error"}), 500

    except Exception as e:
        logger.error(f"Error in webhook for @{bot_username}: {e}", exc_info=True)
        return jsonify({"error": "Internal error"}), 500

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Main-bot webhook (python-telegram-bot posts here)
# ---------------------------------------------------------------------------
# Stored by main.py after the Application is built via set_ptb_application().

_ptb_application = None

# One long-lived event loop shared by initialize() and every process_update().
# PTB's httpx client binds to the loop it first sees; reusing this loop
# avoids the "Event loop is closed" crash on subsequent requests.
_ptb_loop = asyncio.new_event_loop()


def get_ptb_loop() -> asyncio.AbstractEventLoop:
    """Return the shared PTB event loop (used by main.py for initialize())."""
    return _ptb_loop


@app.route('/<path:token_path>', methods=['POST'])
def main_bot_webhook(token_path):
    """
    Catch-all for the main bot's webhook route.
    python-telegram-bot uses the bot token as the URL path.
    We forward the update to the Application's process_update().
    """
    global _ptb_application

    if _ptb_application is None:
        return jsonify({"error": "Application not ready"}), 503

    update_data = request.get_json(force=True)
    if not update_data:
        return jsonify({"error": "Empty"}), 400

    try:
        update = Update.de_json(update_data, _ptb_application.bot)
        
        # Process the update
        _ptb_loop.run_until_complete(_ptb_application.process_update(update))
        
        # CRITICAL: Flush persistence after each update so user_data is saved
        if _ptb_application.persistence:
            _ptb_loop.run_until_complete(_ptb_application.persistence.flush())
            logger.debug("Persistence flushed after update")
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Error processing main bot update: {e}", exc_info=True)
        return jsonify({"error": "Processing error"}), 500


def set_ptb_application(application):
    """Called from main.py to hand over the PTB Application instance."""
    global _ptb_application
    _ptb_application = application


# ---------------------------------------------------------------------------
# Utility routes
# ---------------------------------------------------------------------------

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "ChatFuel"}), 200


@app.route('/webhook-info/<bot_username>', methods=['GET'])
def get_webhook_info(bot_username: str):
    """Debug: show Telegram's view of a created bot's webhook."""
    try:
        db = next(get_db())
        bot_model = db.query(BotModel).filter(
            BotModel.bot_username == bot_username
        ).first()

        if not bot_model:
            return jsonify({"error": "Bot not found"}), 404

        bot_token = decrypt_token(bot_model.bot_token)
        telegram_bot = Bot(token=bot_token)

        loop = asyncio.new_event_loop()
        try:
            info = loop.run_until_complete(telegram_bot.get_webhook_info())
        finally:
            loop.close()

        return jsonify({
            "bot_username": bot_username,
            "webhook_url": info.url,
            "pending_update_count": info.pending_update_count,
            "last_error_date": str(info.last_error_date) if info.last_error_date else None,
            "last_error_message": info.last_error_message,
        }), 200

    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
