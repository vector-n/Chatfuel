"""
Broadcast Handlers

Handlers for composing and sending broadcasts to bot subscribers.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from sqlalchemy.orm import Session

from database import get_db
from database.models import Bot as BotModel
from services.broadcast_service import (
    create_broadcast,
    send_broadcast,
    get_broadcasts,
    get_broadcast,
    get_broadcast_stats,
    delete_broadcast
)
from services.subscriber_service import get_subscriber_count
from services.user_state_service import set_user_state, clear_user_state  # PHASE 2B
from utils.helpers import decrypt_token, escape_markdown
from config.constants import EMOJI

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Broadcast Menu
# ---------------------------------------------------------------------------

async def handle_broadcast_menu(
    bot_model: BotModel,
    update: Update,
    telegram_bot,
    db: Session
):
    """
    Show broadcast options menu.
    
    Args:
        bot_model: Bot database model
        update: Telegram update
        telegram_bot: Telegram Bot instance
        db: Database session
    """
    subscriber_count = get_subscriber_count(bot_model.id, db)
    
    text = f"""{EMOJI['broadcast']} **Broadcasting**

You have **{subscriber_count}** active subscribers.

Choose what you want to broadcast:
"""
    
    keyboard = [
        [
            InlineKeyboardButton("✉️ Text Message", callback_data=f"bc_text_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton("📸 Photo + Caption", callback_data=f"bc_photo_{bot_model.id}"),
            InlineKeyboardButton("🎥 Video + Caption", callback_data=f"bc_video_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton("📋 Broadcast History", callback_data=f"bc_history_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton(f"{EMOJI['back']} Back to Bot Menu", callback_data=f"bot_manage_{bot_model.id}"),
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


# ---------------------------------------------------------------------------
# Text Broadcast
# ---------------------------------------------------------------------------

async def start_text_broadcast(
    bot_model: BotModel,
    update: Update,
    telegram_bot,
    context: ContextTypes.DEFAULT_TYPE,
    db: Session = None
):
    """Start composing a text broadcast."""
    await update.callback_query.answer()
    
    user_telegram_id = update.effective_user.id
    
    # Store bot_id in context for next message
    context.user_data['broadcast_compose'] = {
        'bot_id': bot_model.id,
        'type': 'text'
    }
    
    # PHASE 2B: Persist state to database for webhook
    if db:
        set_user_state(db, bot_model.id, user_telegram_id, context.user_data)
    
    text = f"""✉️ **Text Broadcast**

Send me the text message you want to broadcast to all subscribers.

You can use **Markdown** formatting:
• \\*bold\\* for *bold*
• \\_italic\\_ for _italic_
• \\`code\\` for `code`
• \\[text\\](url) for links

Send your message now:
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['cancel']} Cancel", callback_data=f"bc_cancel_{bot_model.id}")],
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def receive_text_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Receive text broadcast content."""
    # Check if we're waiting for broadcast text
    compose_data = context.user_data.get('broadcast_compose')
    if not compose_data or compose_data.get('type') != 'text':
        return
    
    bot_id = compose_data['bot_id']
    text = update.message.text
    user_telegram_id = update.effective_user.id
    
    # Store the text
    compose_data['text'] = text
    context.user_data['broadcast_compose'] = compose_data
    
    # Show preview
    db = next(get_db())
    try:
        # PHASE 2B: Persist updated state
        set_user_state(db, bot_id, user_telegram_id, context.user_data)
        
        bot_model = db.query(BotModel).filter(BotModel.id == bot_id).first()
        subscriber_count = get_subscriber_count(bot_id, db)
        
        preview_text = f"""📝 **Broadcast Preview**

**Message:**
{text}

**Will be sent to:** {subscriber_count} subscribers

Ready to send?
"""
        
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJI['send']} Send Now", callback_data=f"bc_send_{bot_id}"),
            ],
            [
                InlineKeyboardButton(f"{EMOJI['edit']} Edit Message", callback_data=f"bc_text_{bot_id}"),
                InlineKeyboardButton(f"{EMOJI['cancel']} Cancel", callback_data=f"bc_cancel_{bot_id}"),
            ],
        ]
        
        await update.message.reply_text(
            preview_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Photo Broadcast
# ---------------------------------------------------------------------------

async def start_photo_broadcast(
    bot_model: BotModel,
    update: Update,
    telegram_bot,
    context: ContextTypes.DEFAULT_TYPE,
    db: Session = None
):
    """Start composing a photo broadcast."""
    await update.callback_query.answer()
    
    user_telegram_id = update.effective_user.id
    
    # Store bot_id in context
    context.user_data['broadcast_compose'] = {
        'bot_id': bot_model.id,
        'type': 'photo'
    }
    
    # PHASE 2B: Persist state to database for webhook
    if db:
        set_user_state(db, bot_model.id, user_telegram_id, context.user_data)
    
    text = f"""📸 **Photo Broadcast**

Send me a photo you want to broadcast.

After sending the photo, I'll ask for an optional caption.

Send your photo now:
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['cancel']} Cancel", callback_data=f"bc_cancel_{bot_model.id}")],
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def receive_photo_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Receive photo for broadcast."""
    compose_data = context.user_data.get('broadcast_compose')
    if not compose_data or compose_data.get('type') != 'photo':
        return
    
    # Get largest photo
    photo = update.message.photo[-1]
    file_id = photo.file_id
    user_telegram_id = update.effective_user.id
    
    # Store photo
    compose_data['media_file_id'] = file_id
    compose_data['caption'] = update.message.caption or ""
    context.user_data['broadcast_compose'] = compose_data
    
    bot_id = compose_data['bot_id']
    
    # Show preview
    db = next(get_db())
    try:
        # PHASE 2B: Persist updated state
        set_user_state(db, bot_id, user_telegram_id, context.user_data)
        
        subscriber_count = get_subscriber_count(bot_id, db)
        
        caption_text = compose_data['caption'] if compose_data['caption'] else "_No caption_"
        
        preview_text = f"""📸 **Photo Broadcast Preview**

**Caption:**
{caption_text}

**Will be sent to:** {subscriber_count} subscribers

Ready to send?
"""
        
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJI['send']} Send Now", callback_data=f"bc_send_{bot_id}"),
            ],
            [
                InlineKeyboardButton(f"{EMOJI['cancel']} Cancel", callback_data=f"bc_cancel_{bot_id}"),
            ],
        ]
        
        await update.message.reply_text(
            preview_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Video Broadcast
# ---------------------------------------------------------------------------

async def start_video_broadcast(
    bot_model: BotModel,
    update: Update,
    telegram_bot,
    context: ContextTypes.DEFAULT_TYPE,
    db: Session = None
):
    """Start composing a video broadcast."""
    await update.callback_query.answer()
    
    user_telegram_id = update.effective_user.id
    
    # Store bot_id in context
    context.user_data['broadcast_compose'] = {
        'bot_id': bot_model.id,
        'type': 'video'
    }
    
    # PHASE 2B: Persist state to database for webhook
    if db:
        set_user_state(db, bot_model.id, user_telegram_id, context.user_data)
    
    text = f"""🎥 **Video Broadcast**

Send me a video you want to broadcast.

After sending the video, I'll ask for an optional caption.

Send your video now:
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['cancel']} Cancel", callback_data=f"bc_cancel_{bot_model.id}")],
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def receive_video_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Receive video for broadcast."""
    compose_data = context.user_data.get('broadcast_compose')
    if not compose_data or compose_data.get('type') != 'video':
        return
    
    # Get video
    video = update.message.video
    file_id = video.file_id
    user_telegram_id = update.effective_user.id
    
    # Store video
    compose_data['media_file_id'] = file_id
    compose_data['caption'] = update.message.caption or ""
    context.user_data['broadcast_compose'] = compose_data
    
    bot_id = compose_data['bot_id']
    
    # Show preview
    db = next(get_db())
    try:
        # PHASE 2B: Persist updated state
        set_user_state(db, bot_id, user_telegram_id, context.user_data)
        
        subscriber_count = get_subscriber_count(bot_id, db)
        
        caption_text = compose_data['caption'] if compose_data['caption'] else "_No caption_"
        
        preview_text = f"""🎥 **Video Broadcast Preview**

**Caption:**
{caption_text}

**Will be sent to:** {subscriber_count} subscribers

Ready to send?
"""
        
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJI['send']} Send Now", callback_data=f"bc_send_{bot_id}"),
            ],
            [
                InlineKeyboardButton(f"{EMOJI['cancel']} Cancel", callback_data=f"bc_cancel_{bot_id}"),
            ],
        ]
        
        await update.message.reply_text(
            preview_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Send Broadcast
# ---------------------------------------------------------------------------

async def execute_broadcast(
    bot_model: BotModel,
    update: Update,
    telegram_bot,
    context: ContextTypes.DEFAULT_TYPE,
    db: Session
):
    """Execute the broadcast."""
    await update.callback_query.answer()
    
    compose_data = context.user_data.get('broadcast_compose')
    if not compose_data:
        await update.callback_query.message.edit_text(
            "❌ Broadcast data not found. Please start over."
        )
        return
    
    # Get subscriber count
    subscriber_count = get_subscriber_count(bot_model.id, db)
    
    if subscriber_count == 0:
        await update.callback_query.message.edit_text(
            "❌ You have no subscribers yet! Wait for users to start your bot first."
        )
        return
    
    # Create broadcast in database
    broadcast = create_broadcast(
        db=db,
        bot_id=bot_model.id,
        content_type=compose_data['type'],
        text=compose_data.get('text') or compose_data.get('caption'),
        media_file_id=compose_data.get('media_file_id')
    )
    
    # Show sending message
    status_message = await update.callback_query.message.edit_text(
        f"{EMOJI['loading']} **Sending broadcast...**\n\n"
        f"Progress: 0/{subscriber_count}\n"
        f"✅ Sent: 0\n"
        f"❌ Failed: 0"
    )
    
    # Progress callback
    async def update_progress(current, total, successful, failed):
        try:
            await status_message.edit_text(
                f"{EMOJI['loading']} **Sending broadcast...**\n\n"
                f"Progress: {current}/{total}\n"
                f"✅ Sent: {successful}\n"
                f"❌ Failed: {failed}"
            )
        except:
            pass
    
    # Decrypt bot token
    bot_token = decrypt_token(bot_model.bot_token)
    
    # Send broadcast
    successful, failed = await send_broadcast(
        broadcast_id=broadcast.id,
        bot_token=bot_token,
        db=db,
        progress_callback=update_progress
    )
    
    # Clear compose data
    context.user_data.pop('broadcast_compose', None)
    
    # Show final results
    result_text = f"""✅ **Broadcast Complete!**

📊 **Results:**
✅ Successfully sent: {successful}
❌ Failed: {failed}
📊 Total: {successful + failed}

{EMOJI['success']} Your message has been delivered!
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📋 View History", callback_data=f"bc_history_{bot_model.id}"),
            InlineKeyboardButton("📢 New Broadcast", callback_data=f"admin_broadcast_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton(f"{EMOJI['back']} Back to Bot", callback_data=f"bot_manage_{bot_model.id}"),
        ],
    ]
    
    await status_message.edit_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# ---------------------------------------------------------------------------
# Broadcast History
# ---------------------------------------------------------------------------

async def show_broadcast_history(
    bot_model: BotModel,
    update: Update,
    telegram_bot,
    db: Session
):
    """Show broadcast history."""
    broadcasts = get_broadcasts(db, bot_model.id, limit=10)
    
    text = f"""📋 **Broadcast History**

**Recent broadcasts:**
"""
    
    if broadcasts:
        for bc in broadcasts:
            # Determine status based on counts
            if bc.sent_count > 0:
                status_emoji = '✅'
            elif bc.failed_count > 0:
                status_emoji = '❌'
            else:
                status_emoji = '📝'
            
            date_str = bc.sent_at.strftime('%Y-%m-%d %H:%M') if bc.sent_at else 'Unknown'
            content_type_emoji = {
                'text': '✉️',
                'photo': '📸',
                'video': '🎥'
            }.get(bc.content_type, '📄')
            
            preview = bc.content_text[:30] + "..." if bc.content_text and len(bc.content_text) > 30 else bc.content_text or "No text"
            
            text += f"\n{status_emoji} {content_type_emoji} {preview}"
            text += f"\n   {date_str} • {bc.sent_count or 0} sent"
    else:
        text += "\nNo broadcasts yet."
    
    keyboard = [
        [
            InlineKeyboardButton("📢 New Broadcast", callback_data=f"admin_broadcast_{bot_model.id}"),
        ],
        [
            InlineKeyboardButton(f"{EMOJI['back']} Back to Bot", callback_data=f"bot_manage_{bot_model.id}"),
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


# ---------------------------------------------------------------------------
# Cancel Broadcast
# ---------------------------------------------------------------------------

async def cancel_broadcast(
    bot_model: BotModel,
    update: Update,
    telegram_bot,
    context: ContextTypes.DEFAULT_TYPE
):
    """Cancel broadcast composition."""
    await update.callback_query.answer("Broadcast cancelled")
    
    # Clear compose data
    context.user_data.pop('broadcast_compose', None)
    
    text = f"{EMOJI['cancel']} Broadcast cancelled."
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Menu", callback_data=f"admin_broadcast_{bot_model.id}")],
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
