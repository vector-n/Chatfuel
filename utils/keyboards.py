"""Inline keyboard builders for the bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional
from config.constants import EMOJI, CALLBACK_PREFIX


def create_main_menu_keyboard(user_premium: bool = False) -> InlineKeyboardMarkup:
    """
    Create the main menu keyboard.
    
    Args:
        user_premium: Whether user has premium subscription
        
    Returns:
        InlineKeyboardMarkup with main menu options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                f"{EMOJI['robot']} My Bots",
                callback_data='main_mybots'
            ),
            InlineKeyboardButton(
                f"{EMOJI['broadcast']} New Post",
                callback_data='main_newpost'
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['analytics']} Analytics",
                callback_data='main_analytics'
            ),
            InlineKeyboardButton(
                f"{EMOJI['settings']} Settings",
                callback_data='main_settings'
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['premium']} Premium" if not user_premium else f"{EMOJI['star']} My Plan",
                callback_data='main_premium'
            ),
            InlineKeyboardButton(
                f"{EMOJI['help']} Help",
                callback_data='main_help'
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_bot_list_keyboard(bots: List, current_bot_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """
    Create keyboard with list of user's bots.
    
    Args:
        bots: List of Bot objects
        current_bot_id: ID of currently selected bot (if any)
        
    Returns:
        InlineKeyboardMarkup with bot list
    """
    keyboard = []
    
    for bot in bots:
        # Mark current bot with checkmark
        prefix = f"{EMOJI['success']} " if bot.id == current_bot_id else ""
        button_text = f"{prefix}@{bot.bot_username}"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"{CALLBACK_PREFIX['bot_select']}{bot.id}"
            )
        ])
    
    # Add "Create New Bot" button
    keyboard.append([
        InlineKeyboardButton(
            f"{EMOJI['add']} Create New Bot",
            callback_data='bot_create_new'
        )
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton(
            f"{EMOJI['back']} Back to Menu",
            callback_data='back_to_main'
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


def create_bot_management_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    """
    Create keyboard for managing a specific bot.
    
    Args:
        bot_id: ID of the bot
        
    Returns:
        InlineKeyboardMarkup with management options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                f"{EMOJI['broadcast']} Send Broadcast",
                callback_data=f"bot_broadcast_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['menu']} Button Menus",
                callback_data=f"bot_buttons_{bot_id}"
            ),
            InlineKeyboardButton(
                f"{EMOJI['form']} Forms",
                callback_data=f"bot_forms_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['subscribers']} Subscribers ({0})",  # Will be filled dynamically
                callback_data=f"bot_subscribers_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['settings']} Bot Settings",
                callback_data=f"bot_settings_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['delete']} Delete Bot",
                callback_data=f"{CALLBACK_PREFIX['bot_delete']}{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['back']} Back to Bots",
                callback_data='main_mybots'
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_confirmation_keyboard(
    confirm_callback: str,
    cancel_callback: str = 'cancel',
    confirm_text: str = "✅ Confirm",
    cancel_text: str = "❌ Cancel"
) -> InlineKeyboardMarkup:
    """
    Create a confirmation keyboard with Yes/No buttons.
    
    Args:
        confirm_callback: Callback data for confirm button
        cancel_callback: Callback data for cancel button
        confirm_text: Text for confirm button
        cancel_text: Text for cancel button
        
    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(confirm_text, callback_data=confirm_callback),
            InlineKeyboardButton(cancel_text, callback_data=cancel_callback),
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_bot_settings_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    """
    Create keyboard for bot settings.
    
    Args:
        bot_id: ID of the bot
        
    Returns:
        InlineKeyboardMarkup with settings options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                f"{EMOJI['edit']} Description",
                callback_data=f"settings_description_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['admin']} Manage Admins",
                callback_data=f"settings_admins_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🌐 Language",
                callback_data=f"settings_language_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['back']} Back",
                callback_data=f"bot_manage_{bot_id}"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
    additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None
) -> InlineKeyboardMarkup:
    """
    Create pagination keyboard.
    
    Args:
        current_page: Current page number (0-indexed)
        total_pages: Total number of pages
        callback_prefix: Prefix for page navigation callbacks
        additional_buttons: Additional buttons to add above pagination
        
    Returns:
        InlineKeyboardMarkup with pagination
    """
    keyboard = additional_buttons or []
    
    # Pagination row
    pagination_row = []
    
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton(
                f"{EMOJI['previous']} Previous",
                callback_data=f"{callback_prefix}_page_{current_page - 1}"
            )
        )
    
    # Page indicator
    pagination_row.append(
        InlineKeyboardButton(
            f"{current_page + 1}/{total_pages}",
            callback_data='page_info'
        )
    )
    
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton(
                f"{EMOJI['next']} Next",
                callback_data=f"{callback_prefix}_page_{current_page + 1}"
            )
        )
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    return InlineKeyboardMarkup(keyboard)


def create_back_button(callback_data: str, text: str = None) -> InlineKeyboardMarkup:
    """
    Create a simple back button keyboard.
    
    Args:
        callback_data: Callback data for the back button
        text: Custom text for back button
        
    Returns:
        InlineKeyboardMarkup with back button
    """
    text = text or f"{EMOJI['back']} Back"
    keyboard = [[InlineKeyboardButton(text, callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)


def create_premium_upsell_keyboard() -> InlineKeyboardMarkup:
    """
    Create keyboard for premium upsell.
    
    Returns:
        InlineKeyboardMarkup with premium options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                f"{EMOJI['star']} View Premium Plans",
                callback_data='premium_view_plans'
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['back']} Back",
                callback_data='back_to_main'
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_broadcast_type_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    """
    Create keyboard for selecting broadcast type.
    
    Args:
        bot_id: ID of the bot
        
    Returns:
        InlineKeyboardMarkup with content type options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "📝 Text Message",
                callback_data=f"broadcast_text_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🖼️ Photo with Caption",
                callback_data=f"broadcast_photo_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🎥 Video with Caption",
                callback_data=f"broadcast_video_{bot_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EMOJI['back']} Cancel",
                callback_data=f"bot_manage_{bot_id}"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_language_keyboard(current_lang: str = 'en') -> InlineKeyboardMarkup:
    """
    Create language selection keyboard.
    
    Args:
        current_lang: Currently selected language code
        
    Returns:
        InlineKeyboardMarkup with language options
    """
    from config.constants import SUPPORTED_LANGUAGES
    
    keyboard = []
    
    for code, name in SUPPORTED_LANGUAGES.items():
        prefix = f"{EMOJI['success']} " if code == current_lang else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{prefix}{name}",
                callback_data=f"lang_{code}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            f"{EMOJI['back']} Back",
            callback_data='back_to_main'
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)
