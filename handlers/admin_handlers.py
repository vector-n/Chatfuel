"""
Admin Handlers

Handles all admin (bot owner) interactions within created bots.
Only accessible to the user who created the bot.
"""

import logging
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from sqlalchemy.orm import Session
from datetime import datetime

from database.models import Bot as BotModel, User, Subscriber
from services.subscriber_service import (
    get_subscriber_count,
    get_subscribers,
    get_subscriber_stats
)
# PHASE 2B: Broadcasting handlers
from handlers.broadcast_handlers import (
    handle_broadcast_menu,
    start_text_broadcast,
    start_photo_broadcast,
    start_video_broadcast,
    execute_broadcast,
    show_broadcast_history,
    cancel_broadcast,
    receive_text_broadcast,
    receive_photo_broadcast,
    receive_video_broadcast,
)
# PHASE 3: Menu handlers
from handlers.menu_handlers import (
    handle_admin_menus as handle_admin_menus_phase3,
    handle_menu_edit,
    start_menu_creation,
    receive_menu_name,
    show_upgrade_prompt
)
from utils.helpers import escape_markdown, format_datetime
from config.constants import EMOJI

logger = logging.getLogger(__name__)

# Conversation states for admin flows
WAITING_FOR_DESCRIPTION = 1
WAITING_FOR_COMMANDS = 2
WAITING_FOR_WELCOME_MESSAGE = 3


def is_bot_owner(user_telegram_id: int, bot_model: BotModel, db: Session) -> bool:
    """
    Check if a user is the owner of a bot.
    
    Args:
        user_telegram_id: User's Telegram ID
        bot_model: Bot database model
        db: Database session
        
    Returns:
        bool: True if user is the owner
    """
    platform_user = db.query(User).filter(
        User.telegram_id == user_telegram_id
    ).first()
    
    return (
        platform_user is not None and 
        platform_user.id == bot_model.user_id
    )


async def handle_admin_update(
    bot_model: BotModel,
    update: Update,
    telegram_bot: Bot,
    db: Session,
    subscriber,
    context=None  # PHASE 2B: Added for broadcast state management
):
    """
    Route admin updates to appropriate handlers.
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
        subscriber: Subscriber model (owner is also a subscriber)
    """
    # Handle messages
    if update.message:
        # PHASE 2B: Check for photo broadcast
        if update.message.photo and context:
            compose_data = context.user_data.get('broadcast_compose')
            if compose_data and compose_data['type'] == 'photo':
                await receive_photo_broadcast(update, context)
                return
        
        # PHASE 2B: Check for video broadcast
        if update.message.video and context:
            compose_data = context.user_data.get('broadcast_compose')
            if compose_data and compose_data['type'] == 'video':
                await receive_video_broadcast(update, context)
                return
        
        text = update.message.text
        
        if text == '/start':
            await handle_admin_start(bot_model, update, telegram_bot, db)
        
        elif text == '/broadcast':
            await handle_broadcast_menu(bot_model, update, telegram_bot, db)  # PHASE 2B
        
        elif text == '/subscribers':
            await handle_admin_subscribers(bot_model, update, telegram_bot, db)
        
        elif text == '/stats':
            await handle_admin_stats(bot_model, update, telegram_bot, db)
        
        elif text == '/menu' or text == '/menus':
            await handle_admin_menus(bot_model, update, telegram_bot, db)
        
        elif text == '/forms':
            await handle_admin_forms(bot_model, update, telegram_bot, db)
        
        elif text == '/settings':
            await handle_admin_settings_menu(bot_model, update, telegram_bot, db)
        
        elif text == '/help':
            await handle_admin_help(bot_model, update, telegram_bot, db)
        
        else:
            # PHASE 2B: Check if we're composing a broadcast
            if context:
                compose_data = context.user_data.get('broadcast_compose')
                if compose_data and compose_data['type'] == 'text':
                    await receive_text_broadcast(update, context)
                    return
                
                # PHASE 3: Check if we're creating a menu
                menu_creation_data = context.user_data.get('menu_creation')
                if menu_creation_data:
                    handled = await receive_menu_name(update, context, db)
                    if handled:
                        return
            
            # Unknown command
            from handlers.created_bot_handlers import handle_unknown_command
            await handle_unknown_command(bot_model, update, telegram_bot, is_owner=True)
    
    # Handle callback queries
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith('admin_broadcast_'):
            await handle_broadcast_menu(bot_model, update, telegram_bot, db)  # PHASE 2B
        
        # PHASE 2B: Broadcast composition callbacks
        elif data.startswith('bc_text_'):
            await start_text_broadcast(bot_model, update, telegram_bot, context, db)
        
        elif data.startswith('bc_photo_'):
            await start_photo_broadcast(bot_model, update, telegram_bot, context, db)
        
        elif data.startswith('bc_video_'):
            await start_video_broadcast(bot_model, update, telegram_bot, context, db)
        
        elif data.startswith('bc_send_'):
            await execute_broadcast(bot_model, update, telegram_bot, context, db)
        
        elif data.startswith('bc_history_'):
            await show_broadcast_history(bot_model, update, telegram_bot, db)
        
        elif data.startswith('bc_cancel_'):
            await cancel_broadcast(bot_model, update, telegram_bot, context)
        
        # PHASE 2B: Back to bot menu from broadcast screens
        elif data.startswith('bot_manage_'):
            await handle_admin_start(bot_model, update, telegram_bot, db)
        
        # Original callbacks
        elif data.startswith('admin_subs_'):
            await handle_admin_subscribers(bot_model, update, telegram_bot, db)
        
        elif data.startswith('admin_menus_'):
            await handle_admin_menus(bot_model, update, telegram_bot, db)
        
        # PHASE 3: Menu management callbacks
        elif data.startswith('menu_edit_'):
            menu_id = int(data.split('_')[2])
            await handle_menu_edit(menu_id, update, telegram_bot, db)
        
        elif data.startswith('menu_create_'):
            await start_menu_creation(bot_model.id, update, context)
        
        elif data.startswith('upgrade_prompt_'):
            await show_upgrade_prompt(bot_model.id, update, telegram_bot)
        
        elif data.startswith('admin_forms_'):
            await handle_admin_forms(bot_model, update, telegram_bot, db)
        
        elif data.startswith('admin_settings_'):
            await handle_admin_settings_menu(bot_model, update, telegram_bot, db)
        
        elif data.startswith('admin_analytics_'):
            await handle_admin_stats(bot_model, update, telegram_bot, db)
        
        elif data.startswith('admin_help_'):
            await handle_admin_help(bot_model, update, telegram_bot, db)
        
        elif data.startswith('settings_edit_desc_'):
            await start_edit_description(bot_model, update, telegram_bot, db)
        
        elif data.startswith('settings_edit_commands_'):
            await start_edit_commands(bot_model, update, telegram_bot, db)
        
        elif data.startswith('settings_edit_welcome_'):
            await start_edit_welcome(bot_model, update, telegram_bot, db)
        
        elif data.startswith('settings_back_'):
            await handle_admin_start(bot_model, update, telegram_bot, db)


async def handle_admin_start(bot_model, update, telegram_bot, db):
    """Show admin main menu."""
    from handlers.created_bot_handlers import send_admin_welcome
    
    # If it's a callback query, edit the message
    if update.callback_query:
        # Delete old message and send new one (easier than editing with new keyboard)
        try:
            await update.callback_query.message.delete()
        except:
            pass
    
    await send_admin_welcome(bot_model, update, telegram_bot, db)




async def handle_admin_subscribers(bot_model, update, telegram_bot, db):
    """Show subscriber list and stats."""
    subscriber_count = get_subscriber_count(bot_model.id, db)
    stats = get_subscriber_stats(bot_model.id, db)
    subscribers = get_subscribers(bot_model.id, db, limit=10)
    
    text = f"""{EMOJI['subscribers']} **Subscribers**

**Total:** {subscriber_count}
**Active:** {stats['active']}
**Inactive:** {stats['inactive']}

**Recent Subscribers:**
"""
    
    if subscribers:
        for sub in subscribers:
            name = escape_markdown(sub.first_name or "Unknown")
            username = f"@{sub.username}" if sub.username else ""
            joined = format_datetime(sub.subscribed_at, include_time=False)
            text += f"\n• {name} {username} - {joined}"
    else:
        text += "\nNo subscribers yet."
    
    text += "\n\n_Use /broadcast to send a message to all subscribers!_"
    
    keyboard = [
        [InlineKeyboardButton("📊 View All", callback_data=f"subs_viewall_{bot_model.id}")],
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Menu", callback_data=f"settings_back_{bot_model.id}")],
    ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


async def handle_admin_menus(bot_model, update, telegram_bot, db):
    """Show button menu builder (Phase 3)."""
    # Call Phase 3 implementation
    await handle_admin_menus_phase3(bot_model, update, telegram_bot, db)


async def handle_admin_forms(bot_model, update, telegram_bot, db):
    """Show form builder (Phase 4)."""
    text = f"""{EMOJI['form']} **Forms**

This feature will be available in Phase 4!

You'll be able to:
• Create data collection forms
• Add different question types
• View form responses
• Export data

Coming soon! 🚀
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Menu", callback_data=f"settings_back_{bot_model.id}")],
    ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


async def handle_admin_stats(bot_model, update, telegram_bot, db):
    """Show bot statistics."""
    subscriber_count = get_subscriber_count(bot_model.id, db)
    stats = get_subscriber_stats(bot_model.id, db)
    
    bot_name = escape_markdown(bot_model.bot_name or bot_model.bot_username)
    created = format_datetime(bot_model.created_at, include_time=False)
    
    text = f"""📊 **Bot Statistics**

**Bot:** {bot_name}
**Created:** {created}

**Subscribers:**
• Total: {subscriber_count}
• Active: {stats['active']}
• Inactive: {stats['inactive']}
• New (last 7 days): {stats['new_last_7_days']}
• New (last 30 days): {stats['new_last_30_days']}

**Content:**
• Broadcasts sent: {stats['total_broadcasts']}
• Button menus: {stats['total_menus']} (Phase 3)
• Forms: {stats['total_forms']} (Phase 4)

_More analytics coming in Phase 3!_
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Menu", callback_data=f"settings_back_{bot_model.id}")],
    ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


async def handle_admin_settings_menu(bot_model, update, telegram_bot, db):
    """Show bot settings menu."""
    bot_name = escape_markdown(bot_model.bot_name or bot_model.bot_username)
    
    text = f"""⚙️ **Bot Settings**

**Current Bot:** {bot_name}

What would you like to edit?
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📝 Edit Description", callback_data=f"settings_edit_desc_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton("🔧 Edit Commands", callback_data=f"settings_edit_commands_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton("👋 Edit Welcome Message", callback_data=f"settings_edit_welcome_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton(f"{EMOJI['back']} Back to Menu", callback_data=f"settings_back_{bot_model.id}"),
        ],
    ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


async def start_edit_description(bot_model, update, telegram_bot, db):
    """Start conversation to edit bot description."""
    text = """📝 **Edit Bot Description**

Current description will be shown when users view your bot's profile.

Send me the new description (max 512 characters):

_Send /cancel to abort_
"""
    
    await update.callback_query.message.edit_text(
        text,
        parse_mode='Markdown'
    )
    
    # TODO: Implement conversation handler (Phase 2 polish)
    # For now, just show the message


async def start_edit_commands(bot_model, update, telegram_bot, db):
    """Start conversation to edit bot commands."""
    text = """🔧 **Edit Bot Commands**

This feature will allow you to customize the commands shown in your bot's menu.

_Coming soon in Phase 2 polish!_

For now, your bot has these default commands:
• /start
• /broadcast
• /subscribers
• /stats
• /menu
• /settings
• /help
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data=f"admin_settings_{bot_model.id}")],
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def start_edit_welcome(bot_model, update, telegram_bot, db):
    """Start conversation to edit welcome message."""
    current_message = getattr(bot_model, 'welcome_message', None)
    current = escape_markdown(current_message or "Default welcome message")
    
    text = f"""👋 **Edit Welcome Message**

This is the message new subscribers see when they start your bot.

**Current welcome message:**
{current}

Send me the new welcome message:

_Send /cancel to abort_
"""
    
    await update.callback_query.message.edit_text(
        text,
        parse_mode='Markdown'
    )
    
    # TODO: Implement conversation handler (Phase 2 polish)


async def handle_admin_help(bot_model, update, telegram_bot, db):
    """Show admin help."""
    text = f"""❓ **Admin Help**

**Available Commands:**

📢 **/broadcast** - Send message to all subscribers
👥 **/subscribers** - View subscriber list
📊 **/stats** - View bot statistics
🎨 **/menu** - Create button menus (Phase 3)
📝 **/forms** - Create forms (Phase 4)
⚙️ **/settings** - Edit bot settings
❓ **/help** - Show this help

**Quick Tips:**

• Your subscribers only see the content YOU create
• Use /settings to customize your bot
• Check /stats to monitor growth
• Use /broadcast to engage your audience

Need more help? Contact support in the main ChatFuel bot!
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Menu", callback_data=f"settings_back_{bot_model.id}")],
    ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await telegram_bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
