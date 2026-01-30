"""Input validation utilities."""

import re
from typing import Optional, Tuple
import aiohttp
from config.constants import (
    MAX_MESSAGE_LENGTH,
    MAX_BUTTON_TEXT_LENGTH,
    MAX_CALLBACK_DATA_LENGTH,
)


async def validate_bot_token(token: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Validate a Telegram bot token by calling the Telegram API.
    
    Args:
        token: Bot token to validate
        
    Returns:
        Tuple of (is_valid, bot_info, error_message)
    """
    # Check token format
    if not re.match(r'^\d+:[A-Za-z0-9_-]{35}$', token):
        from utils.error_messages import get_error_message
        return False, None, get_error_message('invalid_token_format')
    
    # Try to get bot info from Telegram API
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{token}/getMe"
            async with session.get(url, timeout=10) as response:
                data = await response.json()
                
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    return True, bot_info, None
                else:
                    from utils.error_messages import get_error_message
                    error = data.get('description', 'Unknown error')
                    return False, None, get_error_message('token_api_error') + f"\n\n**Telegram says:** {error}"
                    
    except aiohttp.ClientError as e:
        from utils.error_messages import get_error_message
        return False, None, get_error_message('network_error')
    except Exception as e:
        from utils.error_messages import get_error_message
        return False, None, get_error_message('unknown_error')


def validate_message_text(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate message text length.
    
    Args:
        text: Message text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Message text cannot be empty"
    
    if len(text) > MAX_MESSAGE_LENGTH:
        return False, f"Message is too long. Maximum {MAX_MESSAGE_LENGTH} characters, got {len(text)}"
    
    return True, None


def validate_button_text(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate button text.
    
    Args:
        text: Button text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Button text cannot be empty"
    
    if len(text) > MAX_BUTTON_TEXT_LENGTH:
        return False, f"Button text is too long. Maximum {MAX_BUTTON_TEXT_LENGTH} characters"
    
    return True, None


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        return False, "Invalid URL format. Must start with http:// or https://"
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address format.
    
    Args:
        email: Email to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    if not email_pattern.match(email):
        return False, "Invalid email address format"
    
    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]+', '', phone)
    
    # Check if it's a valid international format
    phone_pattern = re.compile(r'^\+?[1-9]\d{7,14}$')
    
    if not phone_pattern.match(cleaned):
        return False, "Invalid phone number format. Use international format, e.g., +1234567890"
    
    return True, None


def validate_callback_data(data: str) -> Tuple[bool, Optional[str]]:
    """
    Validate callback data length.
    
    Args:
        data: Callback data to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(data) > MAX_CALLBACK_DATA_LENGTH:
        return False, f"Callback data is too long. Maximum {MAX_CALLBACK_DATA_LENGTH} characters"
    
    return True, None


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML text for Telegram.
    Allows only basic HTML tags that Telegram supports.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    # Telegram supports: b, strong, i, em, u, ins, s, strike, del, a, code, pre
    allowed_tags = ['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'a', 'code', 'pre']
    
    # This is a simple implementation - in production, use a library like bleach
    # For now, we'll just escape all HTML except allowed tags
    
    return text  # TODO: Implement proper HTML sanitization


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Telegram username format.
    
    Args:
        username: Username to validate (with or without @)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Remove @ if present
    clean_username = username.lstrip('@')
    
    # Telegram username rules: 5-32 characters, alphanumeric + underscores
    if len(clean_username) < 5:
        return False, "Username must be at least 5 characters long"
    
    if len(clean_username) > 32:
        return False, "Username must be at most 32 characters long"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', clean_username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, None


def parse_button_input(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse button input in format: "Button Text | action"
    
    Supported formats:
    - Text | https://example.com (URL button)
    - Text | /command (Command button)
    - Text | phone (Phone request button)
    - Text | location (Location request button)
    
    Args:
        text: Input text to parse
        
    Returns:
        Tuple of (button_text, button_type, button_action) or (None, None, error)
    """
    if '|' not in text:
        return None, None, "Invalid format. Use: Button Text | action"
    
    parts = text.split('|', 1)
    if len(parts) != 2:
        return None, None, "Invalid format. Use: Button Text | action"
    
    button_text = parts[0].strip()
    action = parts[1].strip()
    
    # Validate button text
    is_valid, error = validate_button_text(button_text)
    if not is_valid:
        return None, None, error
    
    # Determine button type and validate action
    if action.lower() == 'phone':
        return button_text, 'phone', 'phone'
    
    elif action.lower() == 'location':
        return button_text, 'location', 'location'
    
    elif action.startswith('http://') or action.startswith('https://'):
        is_valid, error = validate_url(action)
        if not is_valid:
            return None, None, error
        return button_text, 'url', action
    
    elif action.startswith('/'):
        # Command button
        return button_text, 'command', action
    
    else:
        return None, None, f"Unknown action type: {action}. Use URL, /command, phone, or location"
