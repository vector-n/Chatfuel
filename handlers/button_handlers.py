"""
Button Handlers - Phase 3B

Comprehensive button management system:
- Button creation with multi-step wizard
- Button editing and deletion
- Button reordering
- Support for all action types (message, URL, submenu, form, webhook)
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from database.models import Bot as BotModel, ButtonMenu, MenuButton
from services.menu_service import (
    get_menu,
    get_menu_buttons,
    get_user_tier,
    check_button_limit,
    create_button,
    get_bot_menus
)
from config.constants import EMOJI, TIER_LIMITS
from utils.helpers import escape_markdown

logger = logging.getLogger(__name__)


# ==================== BUTTON CREATION WIZARD ====================

async def start_button_creation(menu_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Start the button creation wizard."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    # Check if user can add more buttons
    user_tier = get_user_tier(menu.bot_id, db)
    can_add, error_msg = check_button_limit(menu_id, user_tier, db)
    
    if not can_add:
        await update.callback_query.answer(error_msg, show_alert=True)
        
        # Show upgrade prompt
        keyboard = [[
            InlineKeyboardButton(
                "⭐ Upgrade Plan",
                callback_data=f"upgrade_prompt_{menu.bot_id}"
            )
        ], [
            InlineKeyboardButton(
                f"{EMOJI['back']} Back to Menu",
                callback_data=f"menu_edit_{menu_id}"
            )
        ]]
        
        await update.callback_query.message.edit_text(
            f"❌ {error_msg}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Clear any existing state and set button creation state
    if not context or not hasattr(context, 'user_data'):
        logger.error("Context or user_data missing in start_button_creation!")
        await update.callback_query.answer("Error: State management issue. Please try again.", show_alert=True)
        return
    
    if context.user_data is None:
        context.user_data = {}
    
    # Clear any other creation states
    context.user_data.pop('broadcast_compose', None)
    context.user_data.pop('menu_creation', None)
    context.user_data.pop('menu_edit', None)
    
    # Set button creation state
    context.user_data['button_creation'] = {
        'menu_id': menu_id,
        'bot_id': menu.bot_id,
        'step': 'button_text'
    }
    
    logger.info(f"Button creation state set: {context.user_data['button_creation']}")
    
    # Save to database (for webhook-based bots)
    from services.user_state_service import set_user_state
    user_telegram_id = update.callback_query.from_user.id
    set_user_state(db, menu.bot_id, user_telegram_id, context.user_data)
    logger.info(f"State saved to database for user {user_telegram_id}")
    
    text = f"""➕ **Add New Button**

Menu: **{escape_markdown(menu.menu_name)}**

**Step 1/3:** Enter the button text

What text should appear on the button?

Examples:
• 📞 Contact Us
• 🛒 Products
• 💬 Support
• 🔗 Website

Send the button text now:"""
    
    keyboard = [[
        InlineKeyboardButton(
            f"{EMOJI['cancel']} Cancel",
            callback_data=f"menu_edit_{menu_id}"
        )
    ]]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def receive_button_text(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Receive button text and ask for action type."""
    
    # Check if we're in button creation mode
    if not context or not hasattr(context, 'user_data'):
        logger.error("Context or user_data is missing!")
        return False
    
    creation_data = context.user_data.get('button_creation')
    
    logger.info(f"receive_button_text called - creation_data: {creation_data}")
    
    if not creation_data or creation_data.get('step') != 'button_text':
        logger.warning(f"Not in button_text step. Current step: {creation_data.get('step') if creation_data else 'None'}")
        return False
    
    button_text = update.message.text.strip()
    
    # Validate button text
    if len(button_text) < 1:
        await update.message.reply_text(
            "❌ Button text is too short. Please send at least 1 character."
        )
        return True
    
    if len(button_text) > 64:
        await update.message.reply_text(
            "❌ Button text is too long. Please keep it under 64 characters."
        )
        return True
    
    # Save button text and move to next step
    creation_data['button_text'] = button_text
    creation_data['step'] = 'action_type'
    
    # Save to database
    from services.user_state_service import set_user_state
    user_telegram_id = update.message.from_user.id
    set_user_state(db, creation_data['bot_id'], user_telegram_id, context.user_data)
    
    # Show action type selection
    menu_id = creation_data['menu_id']
    menu = get_menu(db, menu_id)
    
    text = f"""✅ Button text set: **{escape_markdown(button_text)}**

**Step 2/3:** Choose action type

What should happen when someone clicks this button?"""
    
    keyboard = [
        [InlineKeyboardButton(
            "💬 Send Message",
            callback_data=f"btn_action_message_{menu_id}"
        )],
        [InlineKeyboardButton(
            "🔗 Open URL",
            callback_data=f"btn_action_url_{menu_id}"
        )],
        [InlineKeyboardButton(
            "📂 Open Submenu",
            callback_data=f"btn_action_submenu_{menu_id}"
        )],
        [InlineKeyboardButton(
            "📝 Launch Form",
            callback_data=f"btn_action_form_{menu_id}"
        )],
        [InlineKeyboardButton(
            f"{EMOJI['cancel']} Cancel",
            callback_data=f"menu_edit_{menu_id}"
        )]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return True


async def handle_action_type_selection(action_type: str, menu_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Handle action type selection."""
    
    creation_data = context.user_data.get('button_creation')
    if not creation_data or creation_data.get('step') != 'action_type':
        await update.callback_query.answer("Invalid state", show_alert=True)
        return
    
    creation_data['action_type'] = action_type
    
    menu = get_menu(db, menu_id)
    button_text = creation_data['button_text']
    
    # Save to database
    from services.user_state_service import set_user_state
    user_telegram_id = update.callback_query.from_user.id
    set_user_state(db, creation_data['bot_id'], user_telegram_id, context.user_data)
    
    if action_type == 'message':
        creation_data['step'] = 'message_content'
        
        text = f"""✅ Action type: **Send Message**
Button text: **{escape_markdown(button_text)}**

**Step 3/3:** Enter the message content

What message should be sent when the button is clicked?

You can use Markdown formatting:
• *bold*
• _italic_
• [link](url)

Send the message content now:"""
        
        keyboard = [[
            InlineKeyboardButton(
                f"{EMOJI['cancel']} Cancel",
                callback_data=f"menu_edit_{menu_id}"
            )
        ]]
        
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif action_type == 'url':
        creation_data['step'] = 'url_content'
        
        text = f"""✅ Action type: **Open URL**
Button text: **{escape_markdown(button_text)}**

**Step 3/3:** Enter the URL

What URL should open when the button is clicked?

Examples:
• https://example.com
• https://t.me/yourchannel
• https://docs.google.com/forms/...

Send the URL now:"""
        
        keyboard = [[
            InlineKeyboardButton(
                f"{EMOJI['cancel']} Cancel",
                callback_data=f"menu_edit_{menu_id}"
            )
        ]]
        
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif action_type == 'submenu':
        # Show list of available menus
        menus = get_bot_menus(db, menu.bot_id)
        
        # Exclude current menu and its children
        available_menus = [m for m in menus if m.id != menu_id and m.parent_menu_id != menu_id]
        
        if not available_menus:
            await update.callback_query.answer(
                "No other menus available. Create another menu first!",
                show_alert=True
            )
            return
        
        creation_data['step'] = 'submenu_selection'
        
        text = f"""✅ Action type: **Open Submenu**
Button text: **{escape_markdown(button_text)}**

**Step 3/3:** Select submenu

Which menu should open when the button is clicked?"""
        
        keyboard = []
        for submenu in available_menus[:10]:  # Show first 10
            keyboard.append([
                InlineKeyboardButton(
                    f"📂 {submenu.menu_name}",
                    callback_data=f"btn_submenu_{submenu.id}_{menu_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"{EMOJI['cancel']} Cancel",
                callback_data=f"menu_edit_{menu_id}"
            )
        ])
        
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif action_type == 'form':
        # TODO: Show list of available forms (Phase 4)
        await update.callback_query.answer(
            "Form buttons coming in Phase 4!",
            show_alert=True
        )
        creation_data['step'] = 'action_type'
    
    # Save updated state
    set_user_state(db, creation_data['bot_id'], user_telegram_id, context.user_data)


async def receive_message_content(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Receive message content and create the button."""
    
    creation_data = context.user_data.get('button_creation')
    if not creation_data or creation_data.get('step') != 'message_content':
        return False
    
    message_content = update.message.text
    
    if len(message_content) > 4096:
        await update.message.reply_text(
            "❌ Message is too long. Please keep it under 4096 characters."
        )
        return True
    
    # Create the button
    menu_id = creation_data['menu_id']
    button_text = creation_data['button_text']
    
    button, error = create_button(
        db=db,
        menu_id=menu_id,
        button_text=button_text,
        action_type='message',
        action_config={'message': message_content},
        button_type='callback'
    )
    
    if error:
        await update.message.reply_text(f"❌ {error}")
        context.user_data.pop('button_creation', None)
        return True
    
    # Clear state
    context.user_data.pop('button_creation', None)
    
    # Save cleared state
    from services.user_state_service import set_user_state
    user_telegram_id = update.message.from_user.id
    set_user_state(db, creation_data['bot_id'], user_telegram_id, context.user_data)
    
    # Show success
    text = f"""✅ **Button Created!**

Button: **{escape_markdown(button_text)}**
Action: Send message
Message preview: _{escape_markdown(message_content[:100])}..._"""
    
    keyboard = [[
        InlineKeyboardButton(
            "➕ Add Another Button",
            callback_data=f"btn_add_{menu_id}"
        )
    ], [
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Menu",
            callback_data=f"menu_edit_{menu_id}"
        )
    ]]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return True


async def receive_url_content(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Receive URL and create the button."""
    
    creation_data = context.user_data.get('button_creation')
    if not creation_data or creation_data.get('step') != 'url_content':
        return False
    
    url = update.message.text.strip()
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://', 'tg://')):
        await update.message.reply_text(
            "❌ Invalid URL. Please send a valid URL starting with http:// or https://"
        )
        return True
    
    # Create the button
    menu_id = creation_data['menu_id']
    button_text = creation_data['button_text']
    
    button, error = create_button(
        db=db,
        menu_id=menu_id,
        button_text=button_text,
        action_type='url',
        action_config={'url': url},
        button_type='url'
    )
    
    if error:
        await update.message.reply_text(f"❌ {error}")
        context.user_data.pop('button_creation', None)
        return True
    
    # Clear state
    context.user_data.pop('button_creation', None)
    
    # Save cleared state
    from services.user_state_service import set_user_state
    user_telegram_id = update.message.from_user.id
    set_user_state(db, creation_data['bot_id'], user_telegram_id, context.user_data)
    
    # Show success
    text = f"""✅ **Button Created!**

Button: **{escape_markdown(button_text)}**
Action: Open URL
URL: {escape_markdown(url)}"""
    
    keyboard = [[
        InlineKeyboardButton(
            "➕ Add Another Button",
            callback_data=f"btn_add_{menu_id}"
        )
    ], [
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Menu",
            callback_data=f"menu_edit_{menu_id}"
        )
    ]]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return True


async def handle_submenu_selection(submenu_id: int, menu_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Handle submenu selection and create button."""
    
    creation_data = context.user_data.get('button_creation')
    if not creation_data or creation_data.get('step') != 'submenu_selection':
        await update.callback_query.answer("Invalid state", show_alert=True)
        return
    
    submenu = get_menu(db, submenu_id)
    if not submenu:
        await update.callback_query.answer("Submenu not found", show_alert=True)
        return
    
    button_text = creation_data['button_text']
    
    # Create the button
    button, error = create_button(
        db=db,
        menu_id=menu_id,
        button_text=button_text,
        action_type='submenu',
        action_config={'target_menu_id': submenu_id},
        button_type='callback',
        target_menu_id=submenu_id
    )
    
    if error:
        await update.callback_query.answer(error, show_alert=True)
        context.user_data.pop('button_creation', None)
        return
    
    # Clear state
    context.user_data.pop('button_creation', None)
    
    # Save cleared state
    from services.user_state_service import set_user_state
    user_telegram_id = update.callback_query.from_user.id
    set_user_state(db, creation_data['bot_id'], user_telegram_id, context.user_data)
    
    # Show success
    text = f"""✅ **Button Created!**

Button: **{escape_markdown(button_text)}**
Action: Open submenu
Target: **{escape_markdown(submenu.menu_name)}**"""
    
    keyboard = [[
        InlineKeyboardButton(
            "➕ Add Another Button",
            callback_data=f"btn_add_{menu_id}"
        )
    ], [
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Menu",
            callback_data=f"menu_edit_{menu_id}"
        )
    ]]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# ==================== BUTTON MANAGEMENT ====================

async def show_button_list(menu_id: int, update: Update, telegram_bot, db: Session):
    """Show list of buttons with edit/delete options."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    buttons = get_menu_buttons(db, menu_id)
    
    if not buttons:
        await update.callback_query.answer("No buttons in this menu yet", show_alert=True)
        return
    
    text = f"""✏️ **Edit Buttons**

Menu: **{escape_markdown(menu.menu_name)}**

Select a button to edit or delete:"""
    
    keyboard = []
    
    for btn in buttons:
        emoji_display = f"{btn.emoji} " if btn.emoji else ""
        action_icon = {
            'message': '💬',
            'submenu': '📂',
            'url': '🔗',
            'form': '📝',
            'webhook': '🔧'
        }.get(btn.action_type, '•')
        
        keyboard.append([
            InlineKeyboardButton(
                f"{action_icon} {emoji_display}{btn.button_text}",
                callback_data=f"btn_edit_{btn.id}_{menu_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Menu",
            callback_data=f"menu_edit_{menu_id}"
        )
    ])
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_button_edit(button_id: int, menu_id: int, update: Update, telegram_bot, db: Session):
    """Show button edit interface."""
    
    button = db.query(MenuButton).filter(MenuButton.id == button_id).first()
    if not button:
        await update.callback_query.answer("Button not found", show_alert=True)
        return
    
    menu = get_menu(db, menu_id)
    
    # Build button info
    emoji_display = f"{button.emoji} " if button.emoji else ""
    action_type_display = {
        'message': '💬 Send Message',
        'submenu': '📂 Open Submenu',
        'url': '🔗 Open URL',
        'form': '📝 Launch Form',
        'webhook': '🔧 Webhook'
    }.get(button.action_type, button.action_type)
    
    # Get action details
    action_details = ""
    if button.action_type == 'message':
        message = button.action_config.get('message', '')
        action_details = f"Message: _{escape_markdown(message[:100])}..._"
    elif button.action_type == 'url':
        url = button.action_config.get('url', '')
        action_details = f"URL: {escape_markdown(url)}"
    elif button.action_type == 'submenu':
        target_menu = get_menu(db, button.target_menu_id)
        if target_menu:
            action_details = f"Target: **{escape_markdown(target_menu.menu_name)}**"
    
    text = f"""✏️ **Edit Button**

Text: **{emoji_display}{escape_markdown(button.button_text)}**
Action: {action_type_display}
{action_details}

What would you like to do?"""
    
    keyboard = [
        [InlineKeyboardButton(
            "✏️ Edit Text",
            callback_data=f"btn_edit_text_{button_id}_{menu_id}"
        )],
        [InlineKeyboardButton(
            "🔄 Change Action",
            callback_data=f"btn_edit_action_{button_id}_{menu_id}"
        )],
        [InlineKeyboardButton(
            "🗑️ Delete Button",
            callback_data=f"btn_delete_confirm_{button_id}_{menu_id}"
        )],
        [InlineKeyboardButton(
            f"{EMOJI['back']} Back to List",
            callback_data=f"btn_list_{menu_id}"
        )]
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def confirm_button_delete(button_id: int, menu_id: int, update: Update, telegram_bot, db: Session):
    """Show button deletion confirmation."""
    
    button = db.query(MenuButton).filter(MenuButton.id == button_id).first()
    if not button:
        await update.callback_query.answer("Button not found", show_alert=True)
        return
    
    text = f"""🗑️ **Delete Button?**

Are you sure you want to delete this button?

Button: **{escape_markdown(button.button_text)}**

⚠️ This action cannot be undone!"""
    
    keyboard = [
        [InlineKeyboardButton(
            "✅ Yes, Delete",
            callback_data=f"btn_delete_{button_id}_{menu_id}"
        )],
        [InlineKeyboardButton(
            f"{EMOJI['cancel']} Cancel",
            callback_data=f"btn_edit_{button_id}_{menu_id}"
        )]
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def delete_button(button_id: int, menu_id: int, update: Update, telegram_bot, db: Session):
    """Delete a button."""
    
    button = db.query(MenuButton).filter(MenuButton.id == button_id).first()
    if not button:
        await update.callback_query.answer("Button not found", show_alert=True)
        return
    
    button_text = button.button_text
    
    # Soft delete (set is_active to False)
    button.is_active = False
    db.commit()
    
    logger.info(f"✅ Button '{button_text}' deleted from menu {menu_id}")
    
    await update.callback_query.answer("Button deleted successfully! ✅")
    
    # Return to button list
    await show_button_list(menu_id, update, telegram_bot, db)
