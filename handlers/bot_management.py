"""Bot management handlers - create, list, delete bots."""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from database.models import Bot
from utils.decorators import with_user
from utils.keyboards import (
    create_bot_list_keyboard,
    create_bot_management_keyboard,
    create_confirmation_keyboard,
    create_back_button,
)
from utils.validators import validate_bot_token
from utils.formatters import (
    format_bot_created_message,
    format_bot_info,
    format_error_message,
    format_success_message,
    format_limit_reached_message,
)
from utils.permissions import check_limit
from utils.helpers import encrypt_token, decrypt_token
from config.constants import EMOJI
from services.bot_setup import setup_created_bot, generate_bot_start_link, remove_webhook

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_TOKEN = 1


@with_user
async def my_bots_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    db: Session,
    user
):
    """Show list of user's bots."""
    await show_my_bots(update, context, db, user)


async def show_my_bots(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session = None, user=None):
    """
    Display list of user's bots.
    
    Args:
        update: Telegram update
        context: Callback context
        db: Database session (optional)
        user: User instance (optional)
    """
    # Handle both command and callback
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        is_callback = True
    else:
        message = update.message
        is_callback = False
    
    # Get database session and user if not provided
    if db is None or user is None:
        from database import get_db
        from utils.helpers import get_user_or_create
        
        db = next(get_db())
        user = get_user_or_create(db, update.effective_user)
    
    bots = user.bots
    
    if not bots:
        text = f"""{EMOJI['robot']} **My Bots**

You don't have any bots yet.

Click "Create New Bot" to get started!

**How to create a bot:**
1. Talk to @BotFather on Telegram
2. Send /newbot and follow instructions
3. Copy the bot token
4. Return here and click "Create New Bot"
"""
        keyboard = create_bot_list_keyboard([], None)
    else:
        text = f"""{EMOJI['robot']} **My Bots** ({len(bots)})

Select a bot to manage:
"""
        keyboard = create_bot_list_keyboard(bots, None)
    
    if is_callback:
        await message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
    else:
        await message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')


@with_user
async def add_bot_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    db: Session,
    user
):
    """
    Start the add bot flow — sets user_data state so the next plain text
    message is captured by waiting_for_token_handler.
    """
    # Check if user has reached bot limit
    bot_count = len(user.bots)
    can_create, error_msg = check_limit(user, 'max_bots', bot_count)
    
    if not can_create:
        if update.callback_query:
            await update.callback_query.answer(error_msg, show_alert=True)
            return
        else:
            await update.message.reply_text(
                format_limit_reached_message("bots", bot_count, user.premium_tier),
                parse_mode='Markdown'
            )
            return
    
    text = f"""{EMOJI['add']} **Create New Bot**

To create a bot, I need your bot token from @BotFather.

**Steps:**
1. Open @BotFather
2. Send /newbot
3. Choose a name and username
4. Copy the bot token (long string like: 123456:ABC-DEF...)
5. Send the token to me

Send me your bot token now:
"""
    
    # Mark this user as waiting for a token
    context.user_data['waiting_for_bot_token'] = True
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, parse_mode='Markdown')


async def receive_bot_token(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Receive and validate bot token.
    
    Args:
        update: Telegram update
        context: Callback context
    # Clear the waiting flag immediately so only this one message is consumed
    context.user_data.pop('waiting_for_bot_token', None)

    """
    from database import get_db
    from utils.helpers import get_user_or_create
    
    db = next(get_db())
    try:
        user = get_user_or_create(db, update.effective_user)
        token = update.message.text.strip()
        
        # Show "validating..." message
        status_msg = await update.message.reply_text(
            f"{EMOJI['clock']} Validating bot token...",
            parse_mode='Markdown'
        )
        
        # Check bot limit FIRST before validating
        current_bot_count = len(user.bots)
        can_create, limit_msg = check_limit(user, 'max_bots', current_bot_count)
        
        if not can_create:
            await status_msg.edit_text(
                format_limit_reached_message(
                    'bots',
                    user.premium_tier,
                    limit_msg
                ),
                parse_mode='Markdown'
            )
            return
        
        # Validate token
        is_valid, bot_info, error = await validate_bot_token(token)
        
        if not is_valid:
            await status_msg.edit_text(
                format_error_message(f"Invalid bot token: {error}"),
                parse_mode='Markdown'
            )
            # Re-set flag so user can retry
            context.user_data['waiting_for_bot_token'] = True
            return
        
        # Check if bot already exists
        existing = db.query(Bot).filter(Bot.bot_username == bot_info['username']).first()
        if existing:
            await status_msg.edit_text(
                format_error_message(f"This bot (@{bot_info['username']}) is already registered!"),
                parse_mode='Markdown'
            )
            return
        
        # Update status message
        await status_msg.edit_text(
            f"{EMOJI['clock']} Setting up webhook and configuring bot...",
            parse_mode='Markdown'
        )
        
        # Create bot in database
        new_bot = Bot(
            user_id=user.id,
            bot_token=encrypt_token(token),
            bot_username=bot_info['username'],
            bot_name=bot_info.get('first_name', ''),
            bot_id=bot_info['id'],
        )
        
        db.add(new_bot)
        db.commit()
        db.refresh(new_bot)
        
        # Setup webhook and commands for the created bot
        setup_success = await setup_created_bot(new_bot, token)
        
        if not setup_success:
            # Webhook setup failed, but bot is created
            success_text = format_bot_created_message(new_bot)
            success_text += f"\n\n⚠️ Note: Webhook setup had issues. The bot may need reconfiguration."
        else:
            # Enhanced success message with instructions
            bot_link = generate_bot_start_link(bot_info['username'])
            
            success_text = f"""✅ **Bot Created Successfully!**

🤖 **Bot**: @{bot_info['username']}
📝 **Name**: {bot_info.get('first_name', 'N/A')}

🎉 **Your bot is ready!**

**Next Steps:**
1. Go to your bot: [Open @{bot_info['username']}]({bot_link})
2. Click "Start" or send /start
3. Your bot is now ready to receive subscribers!

**What you can do:**
📣 Send broadcasts to subscribers
👥 View subscriber list
📊 Check statistics
🎨 Create button menus

**Quick Actions:**
"""
        
        # Success message with keyboard
        await status_msg.edit_text(
            success_text,
            reply_markup=create_bot_management_keyboard(new_bot.id),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        await update.message.reply_text(
            format_error_message(f"Error creating bot: {str(e)}"),
            parse_mode='Markdown'
        )

    finally:
        db.close()


async def cancel_add_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel add bot flow — clears the waiting flag."""
    context.user_data.pop('waiting_for_bot_token', None)
    await update.message.reply_text(
        f"{EMOJI['cancel']} Bot creation cancelled.",
        parse_mode='Markdown'
    )


async def select_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot selection from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    from database import get_db
    from config.constants import CALLBACK_PREFIX
    
    # Extract bot ID from callback data
    # Handle both bot_select_ and bot_manage_ patterns
    if query.data.startswith('bot_manage_'):
        bot_id = int(query.data.replace('bot_manage_', ''))
    else:
        bot_id = int(query.data.replace(CALLBACK_PREFIX['bot_select'], ''))
    
    db = next(get_db())
    try:
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        
        if not bot:
            await query.answer("Bot not found!", show_alert=True)
            return
        
        # Show bot management screen
        text = format_bot_info(bot)
        keyboard = create_bot_management_keyboard(bot.id)
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    finally:
        db.close()


async def delete_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot deletion request."""
    query = update.callback_query
    await query.answer()
    
    from config.constants import CALLBACK_PREFIX
    
    # Extract bot ID
    bot_id = int(query.data.replace(CALLBACK_PREFIX['bot_delete'], ''))
    
    # Show confirmation
    text = f"""{EMOJI['warning']} **Delete Bot**

Are you sure you want to delete this bot?

**This action cannot be undone!**

All data including:
• Subscribers
• Button menus
• Forms and responses
• Broadcasts

Will be permanently deleted.
"""
    
    keyboard = create_confirmation_keyboard(
        confirm_callback=f"confirm_delete_{bot_id}",
        cancel_callback=f"bot_manage_{bot_id}",
        confirm_text=f"{EMOJI['delete']} Yes, Delete",
        cancel_text=f"{EMOJI['cancel']} Cancel"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def confirm_delete_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and execute bot deletion."""
    query = update.callback_query
    await query.answer()
    
    from database import get_db
    from utils.helpers import escape_markdown
    
    # Extract bot ID
    bot_id = int(query.data.replace('confirm_delete_', ''))
    
    db = next(get_db())
    try:
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        
        if not bot:
            await query.answer("Bot not found!", show_alert=True)
            return
        
        # Escape username to handle underscores in Markdown
        bot_username = escape_markdown(bot.bot_username)
        
        # Remove webhook before deleting
        try:
            token = decrypt_token(bot.bot_token)
            await remove_webhook(token, bot.bot_username)
            logger.info(f"Webhook removed for @{bot.bot_username}")
        except Exception as e:
            logger.warning(f"Could not remove webhook for @{bot.bot_username}: {e}")
        
        # Delete bot (cascades to all related data)
        db.delete(bot)
        db.commit()
        
        await query.edit_message_text(
            format_success_message(f"Bot @{bot_username} has been deleted successfully."),
            parse_mode='Markdown'
        )
    finally:
        db.close()


# Guard function: returns True only when user is waiting for a bot token
def _waiting_for_token(update, context):
    return context.user_data.get('waiting_for_bot_token', False)

