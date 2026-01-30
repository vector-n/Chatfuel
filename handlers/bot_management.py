"""Bot management handlers - create, list, delete bots."""

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
from utils.helpers import encrypt_token
from config.constants import EMOJI

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
    Start the add bot conversation.
    
    Args:
        update: Telegram update
        context: Callback context
        db: Database session
        user: User instance
    """
    # Check if user has reached bot limit
    bot_count = len(user.bots)
    can_create, error_msg = check_limit(user, 'max_bots', bot_count)
    
    if not can_create:
        if update.callback_query:
            await update.callback_query.answer(error_msg, show_alert=True)
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                format_limit_reached_message("bots", bot_count, user.premium_tier),
                parse_mode='Markdown'
            )
            return ConversationHandler.END
    
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
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, parse_mode='Markdown')
    
    return WAITING_FOR_TOKEN


async def receive_bot_token(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Receive and validate bot token.
    
    Args:
        update: Telegram update
        context: Callback context
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
        
        # Validate token
        is_valid, bot_info, error = await validate_bot_token(token)
        
        if not is_valid:
            await status_msg.edit_text(
                format_error_message(f"Invalid bot token: {error}"),
                parse_mode='Markdown'
            )
            return WAITING_FOR_TOKEN
        
        # Check if bot already exists
        existing = db.query(Bot).filter(Bot.bot_username == bot_info['username']).first()
        if existing:
            await status_msg.edit_text(
                format_error_message(f"This bot (@{bot_info['username']}) is already registered!"),
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
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
        
        # Success message
        await status_msg.edit_text(
            format_bot_created_message(new_bot),
            reply_markup=create_bot_management_keyboard(new_bot.id),
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(f"Error creating bot: {str(e)}"),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    finally:
        db.close()


async def cancel_add_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel add bot conversation."""
    await update.message.reply_text(
        f"{EMOJI['cancel']} Bot creation cancelled.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END


async def select_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot selection from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    from database import get_db
    from config.constants import CALLBACK_PREFIX
    
    # Extract bot ID from callback data
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
        
        bot_username = escape_markdown(bot.bot_username)
        
        # Delete bot (cascades to all related data)
        db.delete(bot)
        db.commit()
        
        await query.edit_message_text(
            format_success_message(f"Bot @{bot_username} has been deleted successfully."),
            parse_mode='Markdown'
        )
    finally:
        db.close()


# Conversation handler for adding bots
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler

add_bot_conversation = ConversationHandler(
    entry_points=[
        CommandHandler('addbot', add_bot_start),
        CallbackQueryHandler(add_bot_start, pattern='^bot_create_new$'),
    ],
    states={
        WAITING_FOR_TOKEN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_bot_token),
        ],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_add_bot),
    ],
)
