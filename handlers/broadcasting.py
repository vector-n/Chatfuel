"""Broadcasting handlers (placeholder for Phase 2)."""

from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboards import create_back_button
from config.constants import EMOJI


async def show_broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show broadcast menu (placeholder)."""
    query = update.callback_query
    await query.answer()
    
    text = f"""{EMOJI['broadcast']} **New Broadcast**

This feature is coming in Phase 2!

You'll be able to:
• Send text messages
• Send photos with captions
• Send videos
• Add custom buttons
• Schedule posts

Stay tuned! 🚀
"""
    
    keyboard = create_back_button('back_to_main')
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
