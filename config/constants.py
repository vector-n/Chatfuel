"""Application constants and limits."""

from enum import Enum


# ==================== SUBSCRIPTION TIERS ====================

class SubscriptionTier(str, Enum):
    """Subscription tier names."""
    FREE = "free"
    BASIC = "basic"
    ADVANCED = "advanced"
    BUSINESS = "business"


# ==================== TIER LIMITS ====================

TIER_LIMITS = {
    SubscriptionTier.FREE: {
        'max_bots': 3,
        'max_admins_per_bot': 2,
        'max_custom_menus': 3,
        'max_active_forms': 1,
        'max_form_questions': 5,
        'max_form_responses_per_month': 20,
        'max_scheduled_posts_per_month': 0,
        'max_autopost_sources': 0,
        'can_export_data': False,
        'can_use_webhooks': False,
        'can_ab_test': False,
        'ab_test_variants': 0,
        'has_analytics': True,
        'advanced_analytics': False,
        'white_label': False,
        'priority_support': False,
    },
    SubscriptionTier.BASIC: {
        'max_bots': 10,
        'max_admins_per_bot': 5,
        'max_custom_menus': -1,  # -1 means unlimited
        'max_active_forms': 3,
        'max_form_questions': 10,
        'max_form_responses_per_month': 100,
        'max_scheduled_posts_per_month': 10,
        'max_autopost_sources': 0,
        'can_export_data': True,
        'can_use_webhooks': False,
        'can_ab_test': False,
        'ab_test_variants': 0,
        'has_analytics': True,
        'advanced_analytics': True,
        'white_label': False,
        'priority_support': False,
    },
    SubscriptionTier.ADVANCED: {
        'max_bots': 20,
        'max_admins_per_bot': 10,
        'max_custom_menus': -1,
        'max_active_forms': 10,
        'max_form_questions': -1,
        'max_form_responses_per_month': 1000,
        'max_scheduled_posts_per_month': -1,
        'max_autopost_sources': 1,
        'can_export_data': True,
        'can_use_webhooks': False,
        'can_ab_test': True,
        'ab_test_variants': 2,
        'has_analytics': True,
        'advanced_analytics': True,
        'white_label': False,
        'priority_support': True,
    },
    SubscriptionTier.BUSINESS: {
        'max_bots': -1,
        'max_admins_per_bot': -1,
        'max_custom_menus': -1,
        'max_active_forms': -1,
        'max_form_questions': -1,
        'max_form_responses_per_month': -1,
        'max_scheduled_posts_per_month': -1,
        'max_autopost_sources': 5,
        'can_export_data': True,
        'can_use_webhooks': True,
        'can_ab_test': True,
        'ab_test_variants': 5,
        'has_analytics': True,
        'advanced_analytics': True,
        'white_label': True,
        'priority_support': True,
    }
}


# ==================== PRICING ====================

SUBSCRIPTION_PRICES = {
    SubscriptionTier.BASIC: {
        'usd': 4.99,
        'stars': 50,  # Telegram Stars (approximate)
        'currency': 'USD',
    },
    SubscriptionTier.ADVANCED: {
        'usd': 9.99,
        'stars': 100,
        'currency': 'USD',
    },
    SubscriptionTier.BUSINESS: {
        'usd': 19.99,
        'stars': 200,
        'currency': 'USD',
    }
}

# One-time purchases
ADDON_PRICES = {
    'scheduled_post_pack': {'usd': 1.99, 'stars': 20},  # 10 extra scheduled posts
    'autopost_source': {'usd': 4.99, 'stars': 50},  # 1 additional auto-post source
    'extra_form': {'usd': 2.99, 'stars': 30},  # 1 additional form
}


# ==================== BUTTON TYPES ====================

class ButtonType(str, Enum):
    """Types of buttons that can be created."""
    URL = "url"
    COMMAND = "command"
    CALLBACK = "callback"
    PHONE = "phone"
    LOCATION = "location"
    PAYMENT = "payment"


# ==================== FORM QUESTION TYPES ====================

class QuestionType(str, Enum):
    """Types of form questions."""
    TEXT = "text"
    LONGTEXT = "longtext"
    EMAIL = "email"
    PHONE = "phone"
    NUMBER = "number"
    CHOICE = "choice"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    RATING = "rating"
    DATE = "date"
    FILE = "file"


# ==================== CONTENT TYPES ====================

class ContentType(str, Enum):
    """Types of content for broadcasts."""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    ANIMATION = "animation"


# ==================== BOT ADMIN ROLES ====================

class AdminRole(str, Enum):
    """Roles for bot administrators."""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


ROLE_PERMISSIONS = {
    AdminRole.OWNER: {
        'can_delete_bot': True,
        'can_add_admins': True,
        'can_remove_admins': True,
        'can_edit_settings': True,
        'can_broadcast': True,
        'can_create_forms': True,
        'can_view_analytics': True,
    },
    AdminRole.ADMIN: {
        'can_delete_bot': False,
        'can_add_admins': True,
        'can_remove_admins': False,
        'can_edit_settings': True,
        'can_broadcast': True,
        'can_create_forms': True,
        'can_view_analytics': True,
    },
    AdminRole.EDITOR: {
        'can_delete_bot': False,
        'can_add_admins': False,
        'can_remove_admins': False,
        'can_edit_settings': True,
        'can_broadcast': True,
        'can_create_forms': True,
        'can_view_analytics': True,
    },
    AdminRole.VIEWER: {
        'can_delete_bot': False,
        'can_add_admins': False,
        'can_remove_admins': False,
        'can_edit_settings': False,
        'can_broadcast': False,
        'can_create_forms': False,
        'can_view_analytics': True,
    }
}


# ==================== LAYOUT OPTIONS ====================

class MenuLayout(str, Enum):
    """Button menu layout options."""
    ONE_COLUMN = "1col"
    TWO_COLUMN = "2col"
    THREE_COLUMN = "3col"
    CUSTOM = "custom"


# ==================== POST STATUS ====================

class PostStatus(str, Enum):
    """Status of scheduled posts."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RecurrenceType(str, Enum):
    """Post recurrence types."""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ==================== AUTO-POST PLATFORMS ====================

class AutoPostPlatform(str, Enum):
    """Supported auto-posting platforms."""
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    RSS = "rss"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    VIMEO = "vimeo"
    TWITCH = "twitch"


# ==================== LANGUAGES ====================

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'ar': 'العربية',
}


# ==================== RATE LIMITS ====================

RATE_LIMITS = {
    'broadcast_per_hour': 10,
    'api_calls_per_minute': 30,
    'form_submissions_per_hour': 100,
}


# ==================== EMOJI CONSTANTS ====================

EMOJI = {
    'robot': '🤖',
    'broadcast': '📢',
    'analytics': '📊',
    'settings': '⚙️',
    'help': '❓',
    'premium': '💎',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'back': '🔙',
    'next': '➡️',
    'previous': '⬅️',
    'add': '➕',
    'remove': '➖',
    'delete': '🗑️',
    'edit': '✏️',
    'save': '💾',
    'cancel': '🚫',
    'menu': '📱',
    'button': '🔘',
    'form': '📝',
    'calendar': '📅',
    'chart': '📈',
    'subscribers': '👥',
    'admin': '👤',
    'star': '⭐',
    'money': '💰',
    'clock': '🕐',
    'link': '🔗',
    'copy': '📋',
}


# ==================== MESSAGES ====================

DEFAULT_MESSAGES = {
    'welcome': (
        "👋 Welcome to ChatFuel Bot Manager!\n\n"
        "I help you create and manage professional Telegram bots without coding. "
        "Create custom menus, collect data with forms, broadcast to subscribers, and more!\n\n"
        "Let's get started! 🚀"
    ),
    'bot_created': (
        "🎉 Congratulations! Your bot has been created successfully!\n\n"
        "Bot: @{username}\n\n"
        "You can now:\n"
        "• Send broadcasts to subscribers\n"
        "• Create custom button menus\n"
        "• Build forms to collect data\n"
        "• And much more!\n\n"
        "What would you like to do first?"
    ),
    'upgrade_required': (
        "💎 Premium Feature\n\n"
        "This feature requires a premium subscription.\n\n"
        "Upgrade to unlock:\n"
        "• {feature_list}\n\n"
        "View plans and pricing?"
    ),
    'limit_reached': (
        "⚠️ Limit Reached\n\n"
        "You've reached the limit for {resource} on your current plan.\n\n"
        "Current: {current}/{limit}\n\n"
        "Upgrade to increase your limits?"
    ),
}


# ==================== VALIDATION ====================

MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
MAX_BUTTON_TEXT_LENGTH = 64
MAX_CALLBACK_DATA_LENGTH = 64
MAX_FORM_TITLE_LENGTH = 100
MAX_QUESTION_TEXT_LENGTH = 500
MAX_FILE_SIZE_MB = 50

# ==================== CALLBACK DATA PREFIXES ====================

# Used for inline keyboard callback data
CALLBACK_PREFIX = {
    'bot_select': 'bs_',
    'bot_delete': 'bd_',
    'menu_create': 'mc_',
    'menu_edit': 'me_',
    'menu_delete': 'md_',
    'form_create': 'fc_',
    'form_edit': 'fe_',
    'form_delete': 'fd_',
    'broadcast': 'br_',
    'schedule': 'sc_',
    'analytics': 'an_',
    'settings': 'st_',
    'premium': 'pr_',
    'payment': 'py_',
    'confirm': 'cf_',
    'cancel': 'cn_',
    'page': 'pg_',
}
