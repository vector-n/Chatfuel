"""Database models for ChatFuel Bot."""

from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, String, Text, Boolean, Integer,
    DateTime, ForeignKey, UniqueConstraint, ARRAY, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from config.constants import SubscriptionTier, AdminRole

Base = declarative_base()


class User(Base):
    """User model - represents ChatFuel bot users."""
    
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    language = Column(String(10), default='en')
    
    # Subscription info
    premium_tier = Column(String(20), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Trial tracking
    trial_used = Column(Boolean, default=False)
    trial_started_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bots = relationship('Bot', back_populates='owner', cascade='all, delete-orphan')
    bot_admins = relationship('BotAdmin', back_populates='user', foreign_keys='BotAdmin.user_id', cascade='all, delete-orphan')
    payments = relationship('Payment', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
    
    @property
    def is_premium(self):
        """Check if user has active premium subscription."""
        if self.premium_tier == SubscriptionTier.FREE:
            return False
        if self.subscription_expires_at and self.subscription_expires_at < datetime.utcnow():
            return False
        return True
    
    @property
    def display_name(self):
        """Get user's display name."""
        if self.first_name:
            name = self.first_name
            if self.last_name:
                name += f" {self.last_name}"
            return name
        return self.username or f"User {self.telegram_id}"


class Bot(Base):
    """Bot model - represents user-created bots."""
    
    __tablename__ = 'bots'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Bot credentials (encrypted)
    bot_token = Column(String(255), nullable=False)
    bot_username = Column(String(255), nullable=False, index=True)
    bot_name = Column(String(255))
    bot_id = Column(BigInteger)  # Telegram bot ID
    
    # Bot settings
    description = Column(Text)
    language = Column(String(10), default='en')
    is_active = Column(Boolean, default=True)
    webhook_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship('User', back_populates='bots')
    admins = relationship('BotAdmin', back_populates='bot', cascade='all, delete-orphan')
    subscribers = relationship('Subscriber', back_populates='bot', cascade='all, delete-orphan')
    button_menus = relationship('ButtonMenu', back_populates='bot', cascade='all, delete-orphan')
    forms = relationship('Form', back_populates='bot', cascade='all, delete-orphan')
    broadcasts = relationship('Broadcast', back_populates='bot', cascade='all, delete-orphan')
    scheduled_posts = relationship('ScheduledPost', back_populates='bot', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Bot(id={self.id}, username={self.bot_username}, owner_id={self.user_id})>"
    
    @property
    def subscriber_count(self):
        """Get count of active subscribers."""
        return len([s for s in self.subscribers if s.is_active])


class BotAdmin(Base):
    """Bot admins - users who can manage a bot."""
    
    __tablename__ = 'bot_admins'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(BigInteger, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    role = Column(String(20), default=AdminRole.EDITOR)
    added_at = Column(DateTime, default=datetime.utcnow)
    added_by_user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    bot = relationship('Bot', back_populates='admins')
    user = relationship('User', back_populates='bot_admins', foreign_keys=[user_id])
    added_by = relationship('User', foreign_keys=[added_by_user_id])
    
    __table_args__ = (
        UniqueConstraint('bot_id', 'user_id', name='unique_bot_admin'),
    )
    
    def __repr__(self):
        return f"<BotAdmin(bot_id={self.bot_id}, user_id={self.user_id}, role={self.role})>"


class Subscriber(Base):
    """Subscribers to created bots."""
    
    __tablename__ = 'subscribers'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(BigInteger, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Subscriber info
    user_telegram_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    
    # Timestamps
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    unsubscribed_at = Column(DateTime, nullable=True)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    
    # Segmentation
    tags = Column(ARRAY(String), default=[])
    custom_fields = Column(JSON, default={})
    
    # Relationships
    bot = relationship('Bot', back_populates='subscribers')
    
    __table_args__ = (
        UniqueConstraint('bot_id', 'user_telegram_id', name='unique_bot_subscriber'),
    )
    
    def __repr__(self):
        return f"<Subscriber(id={self.id}, bot_id={self.bot_id}, user_id={self.user_telegram_id})>"
    
    @property
    def display_name(self):
        """Get subscriber's display name."""
        if self.first_name:
            name = self.first_name
            if self.last_name:
                name += f" {self.last_name}"
            return name
        return self.username or f"User {self.user_telegram_id}"


class ButtonMenu(Base):
    """Custom button menus for bots."""
    
    __tablename__ = 'button_menus'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(BigInteger, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True)
    
    menu_name = Column(String(255), nullable=False)
    is_main_menu = Column(Boolean, default=False)
    command_trigger = Column(String(100))  # e.g., /menu, /products
    layout = Column(String(20), default='1col')
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bot = relationship('Bot', back_populates='button_menus')
    buttons = relationship('Button', back_populates='menu', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<ButtonMenu(id={self.id}, name={self.menu_name}, bot_id={self.bot_id})>"


class Button(Base):
    """Individual buttons in menus."""
    
    __tablename__ = 'buttons'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    menu_id = Column(BigInteger, ForeignKey('button_menus.id', ondelete='CASCADE'), nullable=False, index=True)
    
    button_text = Column(String(255), nullable=False)
    button_type = Column(String(20), nullable=False)  # url, command, callback, phone, location
    button_action = Column(Text, nullable=False)  # URL, command, callback_data
    
    # Position in menu
    position = Column(Integer, default=0)
    row_position = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    menu = relationship('ButtonMenu', back_populates='buttons')
    clicks = relationship('ButtonClick', back_populates='button', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Button(id={self.id}, text={self.button_text}, type={self.button_type})>"


class ButtonClick(Base):
    """Track button clicks for analytics."""
    
    __tablename__ = 'button_clicks'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    button_id = Column(BigInteger, ForeignKey('buttons.id', ondelete='CASCADE'), nullable=False, index=True)
    user_telegram_id = Column(BigInteger, index=True)
    clicked_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    button = relationship('Button', back_populates='clicks')
    
    def __repr__(self):
        return f"<ButtonClick(button_id={self.button_id}, user_id={self.user_telegram_id})>"


class Form(Base):
    """Forms for data collection."""
    
    __tablename__ = 'forms'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(BigInteger, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True)
    
    form_name = Column(String(255), nullable=False)
    description = Column(Text)
    welcome_message = Column(Text)
    thank_you_message = Column(Text)
    
    # Settings
    is_active = Column(Boolean, default=True)
    allow_multiple_submissions = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    max_responses = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bot = relationship('Bot', back_populates='forms')
    questions = relationship('FormQuestion', back_populates='form', cascade='all, delete-orphan', order_by='FormQuestion.position')
    responses = relationship('FormResponse', back_populates='form', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Form(id={self.id}, name={self.form_name}, bot_id={self.bot_id})>"
    
    @property
    def response_count(self):
        """Get total number of responses."""
        return len(self.responses)


class FormQuestion(Base):
    """Questions in a form."""
    
    __tablename__ = 'form_questions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    form_id = Column(BigInteger, ForeignKey('forms.id', ondelete='CASCADE'), nullable=False, index=True)
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)
    is_required = Column(Boolean, default=False)
    
    # Options for choice/radio/checkbox questions
    options = Column(JSON, nullable=True)
    
    # Validation rules
    validation_rules = Column(JSON, nullable=True)
    placeholder_text = Column(String(255))
    
    # Position in form
    position = Column(Integer, default=0)
    
    # Conditional logic (premium feature)
    conditional_logic = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    form = relationship('Form', back_populates='questions')
    answers = relationship('FormAnswer', back_populates='question', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<FormQuestion(id={self.id}, type={self.question_type}, form_id={self.form_id})>"


class FormResponse(Base):
    """User responses to forms."""
    
    __tablename__ = 'form_responses'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    form_id = Column(BigInteger, ForeignKey('forms.id', ondelete='CASCADE'), nullable=False, index=True)
    
    user_telegram_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255))
    
    completed_at = Column(DateTime, nullable=True)
    time_taken = Column(Integer)  # seconds
    is_complete = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    form = relationship('Form', back_populates='responses')
    answers = relationship('FormAnswer', back_populates='response', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<FormResponse(id={self.id}, form_id={self.form_id}, user_id={self.user_telegram_id})>"


class FormAnswer(Base):
    """Individual answers in form responses."""
    
    __tablename__ = 'form_answers'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    response_id = Column(BigInteger, ForeignKey('form_responses.id', ondelete='CASCADE'), nullable=False, index=True)
    question_id = Column(BigInteger, ForeignKey('form_questions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    answer_text = Column(Text)
    answer_file_id = Column(String(255))  # For file uploads
    
    answered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    response = relationship('FormResponse', back_populates='answers')
    question = relationship('FormQuestion', back_populates='answers')
    
    def __repr__(self):
        return f"<FormAnswer(id={self.id}, question_id={self.question_id})>"


class Broadcast(Base):
    """Broadcast messages sent to subscribers."""
    
    __tablename__ = 'broadcasts'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(BigInteger, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True)
    
    content_type = Column(String(20), nullable=False)
    content_text = Column(Text)
    media_file_id = Column(String(255))
    button_menu_id = Column(BigInteger, ForeignKey('button_menus.id', ondelete='SET NULL'), nullable=True)
    
    # Stats
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    # A/B Testing
    is_test = Column(Boolean, default=False)
    variant_group = Column(String(50))
    
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    bot = relationship('Bot', back_populates='broadcasts')
    button_menu = relationship('ButtonMenu')
    stats = relationship('BroadcastStat', back_populates='broadcast', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Broadcast(id={self.id}, bot_id={self.bot_id}, type={self.content_type})>"


class BroadcastStat(Base):
    """Analytics for broadcasts."""
    
    __tablename__ = 'broadcast_stats'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    broadcast_id = Column(BigInteger, ForeignKey('broadcasts.id', ondelete='CASCADE'), nullable=False, index=True)
    
    user_telegram_id = Column(BigInteger, index=True)
    was_delivered = Column(Boolean, default=False)
    was_read = Column(Boolean, default=False)
    button_clicked = Column(String(255))
    clicked_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    broadcast = relationship('Broadcast', back_populates='stats')
    
    def __repr__(self):
        return f"<BroadcastStat(broadcast_id={self.broadcast_id}, user_id={self.user_telegram_id})>"


class BroadcastDelivery(Base):
    """Track individual broadcast deliveries to subscribers."""
    
    __tablename__ = 'broadcast_deliveries'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    broadcast_id = Column(BigInteger, ForeignKey('broadcasts.id', ondelete='CASCADE'), nullable=False, index=True)
    subscriber_id = Column(BigInteger, ForeignKey('subscribers.id', ondelete='CASCADE'), nullable=False, index=True)
    
    status = Column(String(20), nullable=False, default='pending')  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BroadcastDelivery(broadcast_id={self.broadcast_id}, subscriber_id={self.subscriber_id}, status={self.status})>"


class ScheduledPost(Base):
    """Scheduled posts for later broadcast."""
    
    __tablename__ = 'scheduled_posts'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(BigInteger, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True)
    
    content_type = Column(String(20), nullable=False)
    content_text = Column(Text)
    media_file_id = Column(String(255))
    
    scheduled_time = Column(DateTime, nullable=False, index=True)
    timezone = Column(String(50), default='UTC')
    
    # Recurrence
    recurrence = Column(String(20), default='none')
    recurrence_end = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(20), default='pending')
    sent_at = Column(DateTime, nullable=True)
    
    button_menu_id = Column(BigInteger, ForeignKey('button_menus.id', ondelete='SET NULL'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bot = relationship('Bot', back_populates='scheduled_posts')
    button_menu = relationship('ButtonMenu')
    
    def __repr__(self):
        return f"<ScheduledPost(id={self.id}, bot_id={self.bot_id}, scheduled={self.scheduled_time})>"


class Payment(Base):
    """Payment and subscription records."""
    
    __tablename__ = 'payments'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    amount = Column(Integer, nullable=False)  # Amount in cents or stars
    currency = Column(String(10), default='XTR')  # Telegram Stars
    plan_type = Column(String(20))
    
    payment_provider = Column(String(50), default='telegram_stars')
    transaction_id = Column(String(255), unique=True)
    
    status = Column(String(20), default='pending')
    paid_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship('User', back_populates='payments')
    
    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"


class UserState(Base):
    """Store temporary user state for webhook-based bots (broadcast composition, etc.)."""
    
    __tablename__ = 'user_states'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(BigInteger, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True)
    user_telegram_id = Column(BigInteger, nullable=False, index=True)
    
    state_data = Column(JSON, default={})  # Stores broadcast_compose, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('bot_id', 'user_telegram_id', name='uq_bot_user_state'),
    )
    
    def __repr__(self):
        return f"<UserState(bot_id={self.bot_id}, user={self.user_telegram_id})>"


# Note: More models will be added in later phases (AutoPostSource, Webhook, ActivityLog, etc.)
