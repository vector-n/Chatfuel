"""Application settings and configuration."""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    BOT_USERNAME: str = os.getenv('BOT_USERNAME', 'chatfuelRobot')
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://localhost/chatfuel_db')
    
    # Environment
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    
    # Admin Users
    ADMIN_USER_IDS: str = os.getenv('ADMIN_USER_IDS', '')
    
    @property
    def admin_ids(self) -> List[int]:
        """Parse admin user IDs from comma-separated string."""
        if not self.ADMIN_USER_IDS:
            return []
        return [int(uid.strip()) for uid in self.ADMIN_USER_IDS.split(',') if uid.strip()]
    
    # Payment
    PAYMENT_PROVIDER_TOKEN: str = os.getenv('PAYMENT_PROVIDER_TOKEN', '')
    
    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'change-me-in-production')
    ENCRYPTION_KEY: str = os.getenv('ENCRYPTION_KEY', '')
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '30'))
    MAX_BROADCASTS_PER_DAY: int = int(os.getenv('MAX_BROADCASTS_PER_DAY', '10'))
    
    # Webhook (for production)
    WEBHOOK_URL: str = os.getenv('WEBHOOK_URL', '')
    WEBHOOK_PORT: int = int(os.getenv('WEBHOOK_PORT', '8443'))
    
    @property
    def USE_WEBHOOK(self) -> bool:
        """Use webhook in production, polling in development."""
        return self.ENVIRONMENT == 'production'
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Pagination
    ITEMS_PER_PAGE: int = 10


# Create global settings instance
settings = Settings()


def validate_settings():
    """Validate that all required settings are present."""
    errors = []
    
    if not settings.BOT_TOKEN:
        errors.append("BOT_TOKEN is required")
    
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")
    
    if settings.ENVIRONMENT == 'production':
        if not settings.WEBHOOK_URL:
            errors.append("WEBHOOK_URL is required in production")
        if settings.SECRET_KEY == 'change-me-in-production':
            errors.append("SECRET_KEY must be changed in production")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True
