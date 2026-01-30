"""Enhanced logging configuration for ChatFuel Bot."""

import logging
import sys
from datetime import datetime
from pathlib import Path

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(log_level: str = 'INFO', log_file: str = None):
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from some libraries
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    return root_logger


def log_user_action(logger, user_id: int, action: str, details: str = ""):
    """
    Log user action in a structured format.
    
    Args:
        logger: Logger instance
        user_id: Telegram user ID
        action: Action performed
        details: Additional details
    """
    message = f"[USER:{user_id}] {action}"
    if details:
        message += f" - {details}"
    logger.info(message)


def log_bot_action(logger, bot_id: int, action: str, details: str = ""):
    """
    Log bot-related action.
    
    Args:
        logger: Logger instance
        bot_id: Bot ID
        action: Action performed
        details: Additional details
    """
    message = f"[BOT:{bot_id}] {action}"
    if details:
        message += f" - {details}"
    logger.info(message)


def log_error_with_context(logger, error: Exception, context: dict = None):
    """
    Log error with additional context.
    
    Args:
        logger: Logger instance
        error: Exception object
        context: Additional context dict
    """
    import traceback
    
    error_msg = f"Error: {type(error).__name__}: {str(error)}"
    
    if context:
        error_msg += f"\nContext: {context}"
    
    error_msg += f"\nTraceback:\n{traceback.format_exc()}"
    
    logger.error(error_msg)


# Example usage patterns:
"""
from utils.logging_config import setup_logging, log_user_action, log_error_with_context

# In main.py
logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file='logs/chatfuel.log'  # Optional
)

# In handlers
log_user_action(logger, user.telegram_id, "created_bot", f"Bot: @{bot.bot_username}")
log_bot_action(logger, bot.id, "broadcast_sent", f"Subscribers: {count}")

# In error handlers
try:
    # some operation
except Exception as e:
    log_error_with_context(logger, e, {
        'user_id': user.id,
        'action': 'add_bot',
        'token_prefix': token[:10]
    })
"""
