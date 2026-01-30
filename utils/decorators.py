"""Decorators for handlers."""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db
from utils.helpers import get_user_or_create


def with_db(func):
    """
    Decorator to inject database session into handler.
    
    Usage:
        @with_db
        async def my_handler(update, context, db):
            # db is available here
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        db = next(get_db())
        try:
            return await func(update, context, db, *args, **kwargs)
        finally:
            db.close()
    
    return wrapper


def with_user(func):
    """
    Decorator to inject database session and user into handler.
    
    Usage:
        @with_user
        async def my_handler(update, context, db, user):
            # db and user are available here
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        db = next(get_db())
        try:
            user = get_user_or_create(db, update.effective_user)
            return await func(update, context, db, user, *args, **kwargs)
        finally:
            db.close()
    
    return wrapper


def admin_only(func):
    """
    Decorator to restrict command to admin users only.
    
    Usage:
        @admin_only
        async def admin_command(update, context):
            # only admins can access this
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from config.settings import settings
        
        user_id = update.effective_user.id
        
        if user_id not in settings.admin_ids:
            await update.message.reply_text(
                "⛔ This command is only available to administrators."
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

