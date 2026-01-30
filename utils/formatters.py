"""Message formatting utilities."""

from typing import List, Optional
from datetime import datetime
from config.constants import EMOJI
from database.models import Bot, User


def format_welcome_message(user: User) -> str:
    """
    Format welcome message for new users.
    
    Args:
        user: User instance
        
    Returns:
        Formatted welcome message
    """
    name = user.display_name
    
    return f"""👋 **Welcome to ChatFuel, {name}!**

I help you create and manage professional Telegram bots without any coding knowledge.

**What you can do:**
{EMOJI['robot']} Create broadcast bots
{EMOJI['menu']} Build custom button menus
{EMOJI['form']} Collect data with forms
{EMOJI['broadcast']} Send messages to subscribers
{EMOJI['analytics']} Track engagement & analytics

Ready to create your first bot? Let's get started! 🚀
"""


def format_bot_created_message(bot: Bot) -> str:
    """
    Format success message after bot creation.
    
    Args:
        bot: Bot instance
        
    Returns:
        Formatted success message
    """
    # Only escape bot name, not username (usernames can't have markdown special chars except underscore which is allowed)
    from utils.helpers import escape_markdown
    
    bot_name = escape_markdown(bot.bot_name) if bot.bot_name else 'Not set'
    
    return f"""🎉 **Congratulations! Your bot is ready!**

**Bot:** @{bot.bot_username}
**Name:** {bot_name}

Your bot is now active and ready to accept subscribers!

**Next steps:**
{EMOJI['broadcast']} Send your first broadcast
{EMOJI['menu']} Create button menus
{EMOJI['form']} Build a form
{EMOJI['settings']} Configure bot settings

What would you like to do first?
"""


def format_bot_info(bot: Bot) -> str:
    """
    Format bot information display.
    
    Args:
        bot: Bot instance
        
    Returns:
        Formatted bot info
    """
    from utils.helpers import format_datetime, escape_markdown
    
    status = f"{EMOJI['success']} Active" if bot.is_active else f"{EMOJI['error']} Inactive"
    
    # Only escape bot name and description, not username
    bot_name = escape_markdown(bot.bot_name) if bot.bot_name else 'Not set'
    
    info = f"""**Bot Information**

**Username:** @{bot.bot_username}
**Name:** {bot_name}
**Status:** {status}

{EMOJI['subscribers']} **Subscribers:** {bot.subscriber_count}
{EMOJI['menu']} **Menus:** {len(bot.button_menus)}
{EMOJI['form']} **Forms:** {len([f for f in bot.forms if f.is_active])}

**Created:** {format_datetime(bot.created_at, include_time=False)}
"""
    
    if bot.description:
        description = escape_markdown(bot.description)
        info += f"\n**Description:**\n{description}"
    
    return info


def format_subscriber_stats(bot: Bot) -> str:
    """
    Format subscriber statistics.
    
    Args:
        bot: Bot instance
        
    Returns:
        Formatted statistics
    """
    active = len([s for s in bot.subscribers if s.is_active])
    total = len(bot.subscribers)
    inactive = total - active
    
    return f"""📊 **Subscriber Statistics**

{EMOJI['success']} **Active:** {active}
{EMOJI['error']} **Inactive:** {inactive}
{EMOJI['subscribers']} **Total:** {total}
"""


def format_menu_preview(menu_name: str, buttons: List) -> str:
    """
    Format button menu preview.
    
    Args:
        menu_name: Name of the menu
        buttons: List of button objects
        
    Returns:
        Formatted menu preview
    """
    preview = f"**{menu_name} Menu Preview:**\n\n"
    preview += "┌─────────────────────────┐\n"
    
    for button in buttons:
        button_text = button.button_text
        if button.button_type == 'url':
            icon = '🔗'
        elif button.button_type == 'command':
            icon = '💬'
        elif button.button_type == 'phone':
            icon = '📞'
        elif button.button_type == 'location':
            icon = '📍'
        else:
            icon = '🔘'
        
        preview += f"│  [{icon} {button_text}]  │\n"
    
    preview += "└─────────────────────────┘"
    
    return preview


def format_form_preview(form_name: str, questions: List) -> str:
    """
    Format form preview.
    
    Args:
        form_name: Name of the form
        questions: List of form questions
        
    Returns:
        Formatted form preview
    """
    preview = f"**📝 {form_name}**\n\n"
    
    for i, question in enumerate(questions, 1):
        required = "*" if question.is_required else ""
        type_icon = {
            'text': '✍️',
            'email': '📧',
            'phone': '📞',
            'choice': '☑️',
            'rating': '⭐',
            'number': '🔢',
            'date': '📅',
            'file': '📎',
        }.get(question.question_type, '❓')
        
        preview += f"{i}️⃣ {type_icon} {question.question_text}{required}\n"
        
        if question.question_type in ['choice', 'radio', 'checkbox']:
            if question.options:
                options = ', '.join(question.options)
                preview += f"   Options: {options}\n"
        
        preview += "\n"
    
    return preview


def format_broadcast_confirmation(
    content_type: str,
    subscriber_count: int,
    has_buttons: bool = False
) -> str:
    """
    Format broadcast confirmation message.
    
    Args:
        content_type: Type of content
        subscriber_count: Number of subscribers
        has_buttons: Whether broadcast has buttons
        
    Returns:
        Formatted confirmation message
    """
    type_emoji = {
        'text': '📝',
        'photo': '🖼️',
        'video': '🎥',
        'document': '📄',
    }.get(content_type, '📢')
    
    message = f"""{type_emoji} **Broadcast Preview**

**Type:** {content_type.title()}
**Recipients:** {subscriber_count} subscribers
**Includes buttons:** {'Yes' if has_buttons else 'No'}

Ready to send this broadcast?
"""
    
    return message


def format_error_message(error: str) -> str:
    """
    Format error message for display.
    
    Args:
        error: Error message (should already be escaped if needed)
        
    Returns:
        Formatted error message
    """
    return f"{EMOJI['error']} **Error**\n\n{error}"


def format_success_message(message: str) -> str:
    """
    Format success message for display.
    
    Args:
        message: Success message (should already be escaped if needed)
        
    Returns:
        Formatted success message
    """
    return f"{EMOJI['success']} {message}"


def format_limit_reached_message(
    resource: str,
    current: int,
    limit: int,
    tier: str
) -> str:
    """
    Format limit reached message.
    
    Args:
        resource: Name of the resource
        current: Current count
        limit: Maximum limit
        tier: Current tier
        
    Returns:
        Formatted message
    """
    from utils.helpers import get_tier_name
    
    return f"""{EMOJI['warning']} **Limit Reached**

You've reached the maximum number of {resource} allowed on your {get_tier_name(tier)} plan.

**Current:** {current}/{limit}

Upgrade to a premium plan to increase your limits!
"""


def format_premium_upsell(
    feature_name: str,
    available_in_tier: str
) -> str:
    """
    Format premium feature upsell message.
    
    Args:
        feature_name: Name of the feature
        available_in_tier: Tier where feature is available
        
    Returns:
        Formatted upsell message
    """
    from utils.helpers import get_tier_name
    
    return f"""{EMOJI['premium']} **Premium Feature**

**{feature_name}** is available in {get_tier_name(available_in_tier)} and above.

Upgrade now to unlock:
• {feature_name}
• And many more premium features!

View plans?
"""


def format_admin_list(admins: List) -> str:
    """
    Format list of bot admins.
    
    Args:
        admins: List of BotAdmin objects
        
    Returns:
        Formatted admin list
    """
    if not admins:
        return "No additional admins configured."
    
    admin_list = "**Bot Administrators:**\n\n"
    
    for admin in admins:
        role_icon = {
            'owner': '👑',
            'admin': '⭐',
            'editor': '✏️',
            'viewer': '👁️',
        }.get(admin.role, '👤')
        
        user_name = admin.user.display_name
        admin_list += f"{role_icon} **{user_name}** - {admin.role.title()}\n"
    
    return admin_list
