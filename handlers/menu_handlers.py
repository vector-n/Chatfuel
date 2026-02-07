"""
Menu Handlers - Phase 3

Handlers for button menu management in the admin interface.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from database.models import Bot as BotModel
from services.menu_service import (
    get_bot_menus,
    get_menu_buttons,
    get_user_tier,
    check_menu_limit,
    check_button_limit,
    create_menu,
    create_button,
    get_menu
)
from config.constants import EMOJI, TIER_LIMITS

logger = logging.getLogger(__name__)


async def handle_admin_menus(bot_model: BotModel, update: Update, telegram_bot, db: Session):
    """Show button menu management interface."""
    
    # Get user tier
    user_tier = get_user_tier(bot_model.id, db)
    limits = TIER_LIMITS.get(user_tier, TIER_LIMITS['free'])
    
    # Get existing menus
    menus = get_bot_menus(db, bot_model.id)
    menu_count = len(menus)
    
    # Check limits
    max_menus = limits['max_custom_menus']
    max_buttons = limits['max_buttons_per_menu']
    
    can_create_more, _ = check_menu_limit(bot_model.id, user_tier, db)
    
    text = f"""{EMOJI['menu']} **Button Menus**

Tier: **{user_tier.upper()}**
Menus: **{menu_count}**{"/" + str(max_menus) if max_menus != -1 else " (Unlimited)"}
Max buttons per menu: **{max_buttons if max_buttons != -1 else "Unlimited"}**
"""
    
    if menus:
        text += "\n**Your Menus:**\n"
        for menu in menus:
            buttons_count = len(get_menu_buttons(db, menu.id))
            default_badge = " 🏠" if menu.is_default_menu else ""
            parent_badge = f" ↳ (submenu)" if menu.parent_menu_id else ""
            text += f"\n• {menu.menu_name} ({buttons_count} buttons){default_badge}{parent_badge}"
    else:
        text += "\n_No menus created yet._"
    
    # Build keyboard
    keyboard = []
    
    # List existing menus as buttons
    for menu in menus[:5]:  # Show first 5
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ {menu.menu_name}",
                callback_data=f"menu_edit_{menu.id}"
            )
        ])
    
    # Create new menu button
    if can_create_more:
        keyboard.append([
            InlineKeyboardButton(
                f"➕ Create New Menu",
                callback_data=f"menu_create_{bot_model.id}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                f"⭐ Upgrade to Create More",
                callback_data=f"upgrade_prompt_{bot_model.id}"
            )
        ])
    
    # Template gallery
    keyboard.append([
        InlineKeyboardButton(
            f"🎨 Browse Templates",
            callback_data=f"menu_templates_{bot_model.id}"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Bot",
            callback_data=f"bot_manage_{bot_model.id}"
        )
    ])
    
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


async def handle_menu_edit(menu_id: int, update: Update, telegram_bot, db: Session):
    """Show menu edit interface."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    buttons = get_menu_buttons(db, menu_id)
    button_count = len(buttons)
    
    # Get user tier for limits
    user_tier = get_user_tier(menu.bot_id, db)
    limits = TIER_LIMITS.get(user_tier, TIER_LIMITS['free'])
    max_buttons = limits['max_buttons_per_menu']
    
    can_add_more, _ = check_button_limit(menu_id, user_tier, db)
    
    text = f"""✏️ **Edit Menu: {menu.menu_name}**

Buttons: **{button_count}**{"/" + str(max_buttons) if max_buttons != -1 else " (Unlimited)"}
"""
    
    if menu.menu_description:
        text += f"\nDescription: _{menu.menu_description}_"
    
    if menu.is_default_menu:
        text += "\n🏠 *This is the default menu (shown on /start)*"
    
    if buttons:
        text += "\n\n**Buttons:**"
        for btn in buttons:
            emoji_display = f"{btn.emoji} " if btn.emoji else ""
            action_display = {
                'message': '💬 Message',
                'submenu': '📂 Submenu',
                'url': '🔗 URL',
                'form': '📝 Form',
                'webhook': '🔧 Webhook'
            }.get(btn.action_type, btn.action_type)
            text += f"\n• {emoji_display}{btn.button_text} → {action_display}"
    
    keyboard = []
    
    # Add button
    if can_add_more:
        keyboard.append([
            InlineKeyboardButton(
                "➕ Add Button",
                callback_data=f"btn_add_{menu_id}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                "⭐ Upgrade for More Buttons",
                callback_data=f"upgrade_prompt_{menu.bot_id}"
            )
        ])
    
    # Edit buttons
    if buttons:
        keyboard.append([
            InlineKeyboardButton(
                "✏️ Edit Buttons",
                callback_data=f"btn_list_{menu_id}"
            )
        ])
    
    # Menu settings
    keyboard.append([
        InlineKeyboardButton(
            "⚙️ Menu Settings",
            callback_data=f"menu_settings_{menu_id}"
        ),
        InlineKeyboardButton(
            "🗑️ Delete Menu",
            callback_data=f"menu_delete_{menu_id}"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Menus",
            callback_data=f"admin_menus_{menu.bot_id}"
        )
    ])
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def start_menu_creation(bot_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Start the menu creation flow."""
    
    # IMPORTANT: Clear any existing broadcast composition state
    if context and context.user_data:
        # Clear broadcast state if it exists
        if 'broadcast_compose' in context.user_data:
            del context.user_data['broadcast_compose']
        
        # Set menu creation state
        context.user_data['menu_creation'] = {
            'bot_id': bot_id,
            'step': 'name'
        }
        
        # Save to database (for webhook-based bots)
        from services.user_state_service import set_user_state
        user_telegram_id = update.callback_query.from_user.id
        set_user_state(db, bot_id, user_telegram_id, context.user_data)
    
    text = """➕ **Create New Menu**

Please send me the name for your new menu.

For example:
• Main Menu
• Products
• Services
• Support

Send the menu name now:"""
    
    keyboard = [[
        InlineKeyboardButton(
            f"{EMOJI['cancel']} Cancel",
            callback_data=f"admin_menus_{bot_id}"
        )
    ]]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def receive_menu_name(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Receive menu name and create the menu."""
    
    # Check if we're in menu creation mode
    creation_data = context.user_data.get('menu_creation')
    if not creation_data or creation_data.get('step') != 'name':
        return False
    
    bot_id = creation_data['bot_id']
    menu_name = update.message.text.strip()
    
    if len(menu_name) < 2:
        await update.message.reply_text(
            "❌ Menu name is too short. Please send a name with at least 2 characters."
        )
        return True
    
    if len(menu_name) > 100:
        await update.message.reply_text(
            "❌ Menu name is too long. Please keep it under 100 characters."
        )
        return True
    
    # Create the menu
    menu, error = create_menu(
        db=db,
        bot_id=bot_id,
        menu_name=menu_name
    )
    
    if error:
        await update.message.reply_text(
            f"❌ {error}\n\nUpgrade your plan to create more menus.",
            parse_mode='Markdown'
        )
        # Clear state
        context.user_data.pop('menu_creation', None)
        
        # Save to database
        from services.user_state_service import set_user_state
        user_telegram_id = update.message.from_user.id
        set_user_state(db, bot_id, user_telegram_id, context.user_data)
        
        return True
    
    # Clear state
    context.user_data.pop('menu_creation', None)
    
    # Save cleared state to database
    from services.user_state_service import set_user_state
    user_telegram_id = update.message.from_user.id
    set_user_state(db, bot_id, user_telegram_id, context.user_data)
    
    # Show success and menu edit screen
    text = f"""✅ **Menu Created!**

Menu name: **{menu_name}**

Now you can add buttons to your menu."""
    
    keyboard = [[
        InlineKeyboardButton(
            "➕ Add First Button",
            callback_data=f"btn_add_{menu.id}"
        )
    ], [
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Menus",
            callback_data=f"admin_menus_{bot_id}"
        )
    ]]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return True


async def show_upgrade_prompt(bot_id: int, update: Update, telegram_bot):
    """Show upgrade prompt when limits are reached."""
    
    text = """⭐ **Upgrade to Get More**

You've reached your plan limit!

**Upgrade to unlock:**
✅ More menus
✅ More buttons per menu
✅ Advanced features
✅ Priority support

Choose your plan:"""
    
    keyboard = [
        [
            InlineKeyboardButton("📊 BASIC - $9/mo", callback_data=f"upgrade_basic_{bot_id}"),
        ],
        [
            InlineKeyboardButton("🚀 ADVANCED - $19/mo", callback_data=f"upgrade_advanced_{bot_id}"),
        ],
        [
            InlineKeyboardButton("💼 BUSINESS - $49/mo", callback_data=f"upgrade_business_{bot_id}"),
        ],
        [
            InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data=f"admin_menus_{bot_id}"),
        ]
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# ==================== MENU SETTINGS ====================

async def show_menu_settings(menu_id: int, update: Update, telegram_bot, db: Session):
    """Show menu settings interface."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    default_status = "✅ Yes" if menu.is_default_menu else "❌ No"
    command = menu.command_trigger or "Not set"
    
    text = f"""⚙️ **Menu Settings**

Menu: **{menu.menu_name}**

Description: _{menu.menu_description or 'Not set'}_
Default menu: {default_status}
Command: {command}
Layout: {menu.layout}

What would you like to edit?"""
    
    keyboard = [
        [InlineKeyboardButton(
            "✏️ Edit Name",
            callback_data=f"menu_edit_name_{menu_id}"
        )],
        [InlineKeyboardButton(
            "📝 Edit Description",
            callback_data=f"menu_edit_desc_{menu_id}"
        )],
        [InlineKeyboardButton(
            "🏠 Set as Default Menu",
            callback_data=f"menu_set_default_{menu_id}"
        )],
        [InlineKeyboardButton(
            "⌨️ Set Command Trigger",
            callback_data=f"menu_set_cmd_{menu_id}"
        )],
        [InlineKeyboardButton(
            f"{EMOJI['back']} Back to Menu",
            callback_data=f"menu_edit_{menu_id}"
        )]
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def start_menu_name_edit(menu_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Start editing menu name."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    # Set state
    if context and context.user_data:
        context.user_data['menu_edit'] = {
            'menu_id': menu_id,
            'bot_id': menu.bot_id,
            'step': 'name'
        }
        
        from services.user_state_service import set_user_state
        user_telegram_id = update.callback_query.from_user.id
        set_user_state(db, menu.bot_id, user_telegram_id, context.user_data)
    
    text = f"""✏️ **Edit Menu Name**

Current name: **{menu.menu_name}**

Send the new menu name:"""
    
    keyboard = [[
        InlineKeyboardButton(
            f"{EMOJI['cancel']} Cancel",
            callback_data=f"menu_settings_{menu_id}"
        )
    ]]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def receive_menu_name_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Receive new menu name."""
    
    edit_data = context.user_data.get('menu_edit')
    if not edit_data or edit_data.get('step') != 'name':
        return False
    
    new_name = update.message.text.strip()
    menu_id = edit_data['menu_id']
    
    if len(new_name) < 2:
        await update.message.reply_text("❌ Menu name is too short. Please send at least 2 characters.")
        return True
    
    if len(new_name) > 100:
        await update.message.reply_text("❌ Menu name is too long. Please keep it under 100 characters.")
        return True
    
    menu = get_menu(db, menu_id)
    old_name = menu.menu_name
    menu.menu_name = new_name
    db.commit()
    
    logger.info(f"✅ Menu {menu_id} renamed: '{old_name}' → '{new_name}'")
    
    # Clear state
    context.user_data.pop('menu_edit', None)
    
    from services.user_state_service import set_user_state
    user_telegram_id = update.message.from_user.id
    set_user_state(db, edit_data['bot_id'], user_telegram_id, context.user_data)
    
    text = f"""✅ **Menu Renamed!**

Old name: {old_name}
New name: **{new_name}**"""
    
    keyboard = [[
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Settings",
            callback_data=f"menu_settings_{menu_id}"
        )
    ]]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return True


async def start_menu_description_edit(menu_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Start editing menu description."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    # Set state
    if context and context.user_data:
        context.user_data['menu_edit'] = {
            'menu_id': menu_id,
            'bot_id': menu.bot_id,
            'step': 'description'
        }
        
        from services.user_state_service import set_user_state
        user_telegram_id = update.callback_query.from_user.id
        set_user_state(db, menu.bot_id, user_telegram_id, context.user_data)
    
    current = menu.menu_description or "Not set"
    
    text = f"""📝 **Edit Menu Description**

Current description: _{current}_

Send the new description (or send /skip to remove):"""
    
    keyboard = [[
        InlineKeyboardButton(
            f"{EMOJI['cancel']} Cancel",
            callback_data=f"menu_settings_{menu_id}"
        )
    ]]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def receive_menu_description_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Receive new menu description."""
    
    edit_data = context.user_data.get('menu_edit')
    if not edit_data or edit_data.get('step') != 'description':
        return False
    
    new_description = update.message.text.strip()
    menu_id = edit_data['menu_id']
    
    menu = get_menu(db, menu_id)
    
    if new_description == '/skip':
        menu.menu_description = None
        new_description = "Removed"
    else:
        if len(new_description) > 500:
            await update.message.reply_text("❌ Description is too long. Please keep it under 500 characters.")
            return True
        menu.menu_description = new_description
    
    db.commit()
    
    logger.info(f"✅ Menu {menu_id} description updated")
    
    # Clear state
    context.user_data.pop('menu_edit', None)
    
    from services.user_state_service import set_user_state
    user_telegram_id = update.message.from_user.id
    set_user_state(db, edit_data['bot_id'], user_telegram_id, context.user_data)
    
    text = f"""✅ **Description Updated!**

New description: _{new_description}_"""
    
    keyboard = [[
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Settings",
            callback_data=f"menu_settings_{menu_id}"
        )
    ]]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return True


async def set_menu_as_default(menu_id: int, update: Update, telegram_bot, db: Session):
    """Set menu as default (shown on /start)."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    # Remove default flag from all other menus in this bot
    db.query(ButtonMenu).filter(
        ButtonMenu.bot_id == menu.bot_id,
        ButtonMenu.id != menu_id
    ).update({'is_default_menu': False})
    
    # Set this menu as default
    menu.is_default_menu = True
    db.commit()
    
    logger.info(f"✅ Menu {menu_id} set as default for bot {menu.bot_id}")
    
    await update.callback_query.answer("✅ Set as default menu!", show_alert=True)
    
    # Return to settings
    await show_menu_settings(menu_id, update, telegram_bot, db)


async def start_menu_command_edit(menu_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Start setting command trigger."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    # Set state
    if context and context.user_data:
        context.user_data['menu_edit'] = {
            'menu_id': menu_id,
            'bot_id': menu.bot_id,
            'step': 'command'
        }
        
        from services.user_state_service import set_user_state
        user_telegram_id = update.callback_query.from_user.id
        set_user_state(db, menu.bot_id, user_telegram_id, context.user_data)
    
    current = menu.command_trigger or "Not set"
    
    text = f"""⌨️ **Set Command Trigger**

Current command: {current}

Send the command that should open this menu.

Examples:
• /menu
• /products
• /support

Send the command now (or /skip to remove):"""
    
    keyboard = [[
        InlineKeyboardButton(
            f"{EMOJI['cancel']} Cancel",
            callback_data=f"menu_settings_{menu_id}"
        )
    ]]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def receive_menu_command_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Receive new command trigger."""
    
    edit_data = context.user_data.get('menu_edit')
    if not edit_data or edit_data.get('step') != 'command':
        return False
    
    command = update.message.text.strip()
    menu_id = edit_data['menu_id']
    
    menu = get_menu(db, menu_id)
    
    if command == '/skip':
        menu.command_trigger = None
        command = "Removed"
    else:
        if not command.startswith('/'):
            await update.message.reply_text("❌ Command must start with /")
            return True
        
        if len(command) > 100:
            await update.message.reply_text("❌ Command is too long.")
            return True
        
        menu.command_trigger = command
    
    db.commit()
    
    logger.info(f"✅ Menu {menu_id} command trigger set to: {command}")
    
    # Clear state
    context.user_data.pop('menu_edit', None)
    
    from services.user_state_service import set_user_state
    user_telegram_id = update.message.from_user.id
    set_user_state(db, edit_data['bot_id'], user_telegram_id, context.user_data)
    
    text = f"""✅ **Command Set!**

Command: {command}

Subscribers can now use this command to open the menu."""
    
    keyboard = [[
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Settings",
            callback_data=f"menu_settings_{menu_id}"
        )
    ]]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return True


# ==================== MENU DELETION ====================

async def confirm_menu_delete(menu_id: int, update: Update, telegram_bot, db: Session):
    """Show menu deletion confirmation."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    # Check if menu has child menus
    child_menus = db.query(ButtonMenu).filter(
        ButtonMenu.parent_menu_id == menu_id,
        ButtonMenu.is_active == True
    ).all()
    
    buttons = get_menu_buttons(db, menu_id)
    
    warning = ""
    if child_menus:
        warning = f"\n\n⚠️ This menu has {len(child_menus)} submenu(s) that will also be affected!"
    
    text = f"""🗑️ **Delete Menu?**

Are you sure you want to delete:
**{menu.menu_name}**

This menu has {len(buttons)} button(s).{warning}

⚠️ This action cannot be undone!"""
    
    keyboard = [
        [InlineKeyboardButton(
            "✅ Yes, Delete",
            callback_data=f"menu_delete_confirm_{menu_id}"
        )],
        [InlineKeyboardButton(
            f"{EMOJI['cancel']} Cancel",
            callback_data=f"menu_edit_{menu_id}"
        )]
    ]
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def delete_menu(menu_id: int, update: Update, telegram_bot, db: Session):
    """Delete a menu."""
    
    menu = get_menu(db, menu_id)
    if not menu:
        await update.callback_query.answer("Menu not found", show_alert=True)
        return
    
    bot_id = menu.bot_id
    menu_name = menu.menu_name
    
    # Soft delete (set is_active to False)
    menu.is_active = False
    
    # Also deactivate all buttons in this menu
    db.query(MenuButton).filter(
        MenuButton.menu_id == menu_id
    ).update({'is_active': False})
    
    db.commit()
    
    logger.info(f"✅ Menu '{menu_name}' (ID: {menu_id}) deleted from bot {bot_id}")
    
    await update.callback_query.answer("Menu deleted successfully! ✅")
    
    # Return to menu list
    from handlers.menu_handlers import handle_admin_menus
    from database.models import Bot as BotModel
    bot_model = db.query(BotModel).filter(BotModel.id == bot_id).first()
    
    await handle_admin_menus(bot_model, update, telegram_bot, db)
