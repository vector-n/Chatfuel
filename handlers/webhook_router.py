"""
Webhook Router

Handles incoming webhooks from all created bots and routes them to appropriate handlers.
This is the core of the decentralized bot system.
"""

import logging
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.error import TelegramError
from sqlalchemy.orm import Session

from database import get_db
from database.models import Bot as BotModel, User
from utils.helpers import decrypt_token
from handlers.created_bot_handlers import handle_created_bot_update
from handlers.admin_handlers import is_bot_owner

logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/webhook/<bot_username>', methods=['POST'])
async def webhook_handler(bot_username: str):
    """
    Universal webhook endpoint for all created bots.
    
    Flow:
    1. User interacts with @TheirBot
    2. Telegram sends update to: your-server.com/webhook/TheirBot
    3. We identify the bot, decrypt token, and route to handlers
    
    Args:
        bot_username: The username of the bot (from URL path)
    """
    try:
        # Get database session
        db = next(get_db())
        
        # 1. Find the bot in our database
        bot_model = db.query(BotModel).filter(
            BotModel.bot_username == bot_username,
            BotModel.is_active == True
        ).first()
        
        if not bot_model:
            logger.warning(f"Webhook received for unknown bot: @{bot_username}")
            return jsonify({"error": "Bot not found"}), 404
        
        # 2. Get the update from Telegram
        update_data = request.get_json(force=True)
        
        if not update_data:
            logger.error(f"Empty update received for @{bot_username}")
            return jsonify({"error": "Empty update"}), 400
        
        # 3. Decrypt bot token
        bot_token = decrypt_token(bot_model.bot_token)
        
        if not bot_token:
            logger.error(f"Failed to decrypt token for @{bot_username}")
            return jsonify({"error": "Token error"}), 500
        
        # 4. Create Telegram Bot instance
        telegram_bot = Bot(token=bot_token)
        
        # 5. Parse update
        try:
            update = Update.de_json(update_data, telegram_bot)
        except Exception as e:
            logger.error(f"Failed to parse update for @{bot_username}: {e}")
            return jsonify({"error": "Invalid update"}), 400
        
        # 6. Log the update
        user_id = None
        if update.message:
            user_id = update.message.from_user.id
            logger.info(f"📨 Message from {user_id} to @{bot_username}: {update.message.text}")
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            logger.info(f"🔘 Callback from {user_id} to @{bot_username}: {update.callback_query.data}")
        
        # 7. Route to appropriate handler
        await handle_created_bot_update(
            bot_model=bot_model,
            update=update,
            telegram_bot=telegram_bot,
            db=db
        )
        
        # 8. Return success
        return jsonify({"ok": True}), 200
        
    except TelegramError as e:
        logger.error(f"Telegram error in webhook for @{bot_username}: {e}")
        return jsonify({"error": "Telegram error"}), 500
        
    except Exception as e:
        logger.error(f"Error in webhook for @{bot_username}: {e}", exc_info=True)
        return jsonify({"error": "Internal error"}), 500
        
    finally:
        db.close()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "ChatFuel Webhook Router"
    }), 200


@app.route('/webhook-info/<bot_username>', methods=['GET'])
async def get_webhook_info(bot_username: str):
    """
    Get webhook information for a bot (for debugging).
    
    Args:
        bot_username: Bot username
    """
    try:
        db = next(get_db())
        
        bot_model = db.query(BotModel).filter(
            BotModel.bot_username == bot_username
        ).first()
        
        if not bot_model:
            return jsonify({"error": "Bot not found"}), 404
        
        # Get webhook info from Telegram
        bot_token = decrypt_token(bot_model.bot_token)
        telegram_bot = Bot(token=bot_token)
        
        webhook_info = await telegram_bot.get_webhook_info()
        
        return jsonify({
            "bot_username": bot_username,
            "webhook_url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return jsonify({"error": str(e)}), 500
        
    finally:
        db.close()


def start_webhook_server(host='0.0.0.0', port=8000):
    """
    Start the webhook server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    logger.info(f"🚀 Starting webhook server on {host}:{port}")
    app.run(host=host, port=port)
