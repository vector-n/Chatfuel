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
