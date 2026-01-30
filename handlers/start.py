"""Start command and main menu handlers."""

from telegram import Update
from telegram.ext import ContextTypes
from utils.decorators import with_user
from utils.keyboards import create_main_menu_keyboard
from utils.formatters import format_welcome_message
from config.constants import EMOJI


@with_user
async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    db,
    user
):
    """
    Handle /start command - show welcome message and main menu.
    
    Args:
        update: Telegram update
        context: Callback context
        db: Database session
        user: User instance
    """
    welcome_text = format_welcome_message(user)
    
    # Check if user has any bots
    bot_count = len(user.bots)
    
    if bot_count == 0:
        welcome_text += f"\n\n{EMOJI['add']} You don't have any bots yet. Click 'My Bots' to create your first one!"
    else:
        welcome_text += f"\n\n{EMOJI['robot']} You have {bot_count} bot{'s' if bot_count != 1 else ''} configured."
    
    keyboard = create_main_menu_keyboard(user.is_premium)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle main menu callbacks from inline keyboard.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Import handlers dynamically to avoid circular imports
    from handlers.bot_management import show_my_bots
    from handlers.broadcasting import show_broadcast_menu
    from handlers.help import show_help_menu
    
    # Route to appropriate handler based on callback data
    if callback_data == 'main_mybots':
        await show_my_bots(update, context)
    
    elif callback_data == 'main_newpost':
        await show_broadcast_menu(update, context)
    
    elif callback_data == 'main_analytics':
        await query.edit_message_text(
            f"{EMOJI['chart']} **Analytics**\n\nThis feature is coming soon!",
            parse_mode='Markdown'
        )
    
    elif callback_data == 'main_settings':
        await query.edit_message_text(
            f"{EMOJI['settings']} **Settings**\n\nThis feature is coming soon!",
            parse_mode='Markdown'
        )
    
    elif callback_data == 'main_premium':
        await query.edit_message_text(
            f"{EMOJI['premium']} **Premium Plans**\n\nThis feature is coming soon!",
            parse_mode='Markdown'
        )
    
    elif callback_data == 'main_help':
        await show_help_menu(update, context)
    
    elif callback_data == 'back_to_main':
        # Show main menu
        from database import get_db
        from utils.helpers import get_user_or_create
        
        db = next(get_db())
        try:
            user = get_user_or_create(db, update.effective_user)
            keyboard = create_main_menu_keyboard(user.is_premium)
            
            await query.edit_message_text(
                "🏠 **Main Menu**\n\nWhat would you like to do?",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        finally:
            db.close()
