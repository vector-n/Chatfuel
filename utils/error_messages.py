"""Enhanced error messages for better user experience."""

from config.constants import EMOJI

# Error messages with helpful context
ERROR_MESSAGES = {
    # Bot token validation errors
    'invalid_token_format': f"""{EMOJI['error']} **Invalid Bot Token**

The token format is incorrect. A valid bot token looks like:
`123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567`

**How to get your bot token:**
1. Open @BotFather on Telegram
2. Send /mybots
3. Select your bot
4. Click "API Token"
5. Copy the entire token and send it to me

Please try again with the correct token.""",

    'token_api_error': f"""{EMOJI['error']} **Token Validation Failed**

I couldn't verify your bot token with Telegram.

**Possible reasons:**
• The token might be incorrect
• The bot might have been deleted in @BotFather
• Telegram API might be temporarily unavailable

**What to do:**
1. Check if the bot still exists in @BotFather
2. Generate a new token if needed (⚠️ this will invalidate the old one)
3. Try again in a few minutes

Need help? Send /help""",

    'bot_already_exists': f"""{EMOJI['warning']} **Bot Already Registered**

This bot is already registered in ChatFuel!

**Options:**
• Use a different bot
• If this is your bot, you can manage it from "My Bots"
• Create a new bot in @BotFather

Want to create a new bot? Send /addbot""",

    # Limit errors
    'bot_limit_reached': f"""{EMOJI['warning']} **Bot Limit Reached**

You've reached your maximum number of bots on the Free plan.

**Your current plan:**
• Bots: {{current}}/{{limit}}
• Tier: Free

**To add more bots:**
• Upgrade to Basic Pro (10 bots) - $4.99/mo
• Upgrade to Advanced Pro (20 bots) - $9.99/mo
• Upgrade to Business (unlimited) - $19.99/mo

View upgrade options: /premium
Delete a bot to make space: /mybots""",

    # Database errors
    'database_error': f"""{EMOJI['error']} **Something Went Wrong**

I encountered an error while saving your data.

This is usually temporary. Please try again in a moment.

If the problem persists:
1. Try /start to refresh
2. Check your internet connection
3. Contact support if issue continues

Error ID: {{error_id}}""",

    # Network errors
    'network_error': f"""{EMOJI['error']} **Connection Problem**

I couldn't connect to Telegram's servers.

**What to try:**
• Wait a few seconds and try again
• Check if Telegram is working (send a message to any chat)
• Try again later if Telegram is having issues

This is usually temporary and resolves quickly.""",

    # Generic errors
    'unknown_error': f"""{EMOJI['error']} **Unexpected Error**

Something unexpected happened. Don't worry, your data is safe!

**What to do:**
1. Try the action again
2. If it fails again, send /start to refresh
3. Contact support if problem persists

This has been logged and we'll investigate.""",

    # Success messages
    'bot_created_success': f"""{EMOJI['success']} **Bot Created Successfully!**

Your bot is ready and waiting for subscribers!

**Next steps:**
1. Share your bot link with users
2. Create button menus for easy navigation
3. Set up forms to collect data
4. Send your first broadcast

Start with: /mybots""",

    'bot_deleted_success': f"""{EMOJI['success']} **Bot Deleted**

The bot and all its data have been removed.

**What was deleted:**
• Bot configuration
• Subscriber list
• Button menus
• Forms and responses
• All broadcasts

This action cannot be undone.

Create a new bot: /addbot""",

    # Helpful tips
    'first_time_help': f"""👋 **Welcome to ChatFuel!**

I see you're new here! Let me help you get started.

**What is ChatFuel?**
ChatFuel helps you create and manage Telegram bots without coding.

**Quick Start (3 steps):**
1. Create a bot in @BotFather (takes 1 minute)
2. Add it to ChatFuel with /addbot
3. Start broadcasting to your subscribers!

**What you can do:**
{EMOJI['robot']} Create multiple bots
{EMOJI['menu']} Build custom menus
{EMOJI['form']} Collect data with forms
{EMOJI['broadcast']} Send messages to all subscribers
{EMOJI['analytics']} Track your bot's performance

Ready? Let's create your first bot!
Use: /addbot""",

    'no_bots_yet': f"""{EMOJI['robot']} **No Bots Yet**

You haven't created any bots yet. Let's create your first one!

**Step 1:** Go to @BotFather on Telegram

**Step 2:** Send this command:
`/newbot`

**Step 3:** Follow BotFather's instructions to:
• Choose a name for your bot
• Choose a username (must end with 'bot')

**Step 4:** Copy the token BotFather gives you

**Step 5:** Come back here and click the button below!

Ready to create your first bot?""",

    # Feature coming soon
    'feature_coming_soon': f"""{EMOJI['clock']} **Coming Soon!**

This feature is currently in development and will be available soon.

**What's coming:**
• {{feature_name}}

Want to be notified when it's ready?
We'll announce all new features in our updates channel.

Stay tuned! 🚀""",
}


def get_error_message(error_key: str, **kwargs) -> str:
    """
    Get formatted error message with optional parameters.
    
    Args:
        error_key: Key from ERROR_MESSAGES dict
        **kwargs: Variables to format in the message
        
    Returns:
        Formatted error message
    """
    message = ERROR_MESSAGES.get(error_key, ERROR_MESSAGES['unknown_error'])
    
    try:
        return message.format(**kwargs)
    except KeyError:
        return message


def get_validation_error(field: str, issue: str) -> str:
    """
    Get validation error message for specific field.
    
    Args:
        field: Field name (e.g., 'bot_token', 'email')
        issue: Issue description (e.g., 'too_short', 'invalid_format')
        
    Returns:
        Formatted error message
    """
    field_errors = {
        'bot_token': {
            'too_short': "Bot token is too short. It should be at least 40 characters.",
            'invalid_format': "Bot token format is invalid. Check that you copied the entire token.",
            'missing': "Please provide your bot token from @BotFather.",
        },
        'bot_name': {
            'too_long': "Bot name is too long. Maximum 64 characters allowed.",
            'invalid_chars': "Bot name contains invalid characters.",
        },
        'description': {
            'too_long': "Description is too long. Maximum 512 characters allowed.",
        }
    }
    
    error = field_errors.get(field, {}).get(issue, "Invalid input.")
    return f"{EMOJI['error']} **Validation Error**\n\n{error}"


def get_helpful_tip() -> str:
    """
    Get a random helpful tip for users.
    
    Returns:
        Helpful tip message
    """
    import random
    
    tips = [
        f"""💡 **Tip: Share Your Bot**

Get your bot link from @BotFather and share it on:
• Social media
• Your website  
• Email signature
• WhatsApp/Telegram groups

More subscribers = more impact!""",

        f"""💡 **Tip: Keep Subscribers Engaged**

Don't spam! Here's what works:
• Post 1-3 times per week
• Share valuable content
• Ask questions to get responses
• Use polls and quizzes

Quality over quantity!""",

        f"""💡 **Tip: Use Button Menus**

Button menus make your bot easier to use:
• Users don't need to type commands
• Looks more professional
• Reduces errors
• Increases engagement

Create one with /buttons (coming soon!)""",

        f"""💡 **Tip: Test Before Broadcasting**

Before sending to all subscribers:
• Send test message to yourself
• Check spelling and formatting
• Make sure links work
• Test on mobile and desktop

Better safe than sorry!""",

        f"""💡 **Tip: Backup Your Data**

Keep your bot tokens safe:
• Save them in a password manager
• Never share them publicly
• Generate new token if compromised
• Keep a backup list of your bots

Security first!""",
    ]
    
    return random.choice(tips)
