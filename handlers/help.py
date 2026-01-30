"""Help and tutorials handlers."""

from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboards import create_back_button
from config.constants import EMOJI


async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help menu."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        is_callback = True
    else:
        message = update.message
        is_callback = False
    
    text = f"""{EMOJI['help']} **Help & Support**

**Available Commands:**

{EMOJI['robot']} **/start** - Show main menu
{EMOJI['add']} **/addbot** - Create a new bot
{EMOJI['robot']} **/mybots** - List your bots
{EMOJI['help']} **/help** - Show this help message

**Need more help?**
Visit our documentation or contact support.

Coming soon:
• Video tutorials
• Step-by-step guides
• FAQ section
"""
    
    keyboard = create_back_button('back_to_main')
    
    if is_callback:
        await message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
    else:
        await message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
