"""Help and tutorials handlers."""

from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.constants import EMOJI


async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help menu with topics."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        is_callback = True
    else:
        message = update.message
        is_callback = False
    
    text = f"""{EMOJI['help']} **Help & Support**

**Quick Start**
New to ChatFuel? Start here!

**Commands**
All available bot commands

**Tutorials**
Step-by-step guides

**FAQ**
Frequently asked questions

**Contact**
Get in touch with support
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🚀 Quick Start", callback_data='help_quickstart'),
            InlineKeyboardButton("📝 Commands", callback_data='help_commands'),
        ],
        [
            InlineKeyboardButton("📚 Tutorials", callback_data='help_tutorials'),
            InlineKeyboardButton("❓ FAQ", callback_data='help_faq'),
        ],
        [
            InlineKeyboardButton("📧 Contact Support", callback_data='help_contact'),
        ],
        [
            InlineKeyboardButton(f"{EMOJI['back']} Back to Menu", callback_data='back_to_main'),
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_callback:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def show_help_quickstart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show quick start guide."""
    query = update.callback_query
    await query.answer()
    
    text = f"""🚀 **Quick Start Guide**

**Step 1: Create a Bot**
1. Open @BotFather on Telegram
2. Send `/newbot`
3. Choose a name (e.g., "My Awesome Bot")
4. Choose a username (must end with 'bot')
5. Copy the token BotFather gives you

**Step 2: Add to ChatFuel**
1. Send `/addbot` to me
2. Paste your bot token
3. Done! Your bot is ready

**Step 3: Share Your Bot**
1. Go to /mybots
2. Click on your bot
3. Share the link @your\_bot\_username

**What's Next?**
• Create button menus (coming soon)
• Build forms to collect data (coming soon)
• Send broadcasts to subscribers (coming soon)

Need more help? Check the tutorials!
"""
    
    keyboard = [
        [InlineKeyboardButton("📚 View Tutorials", callback_data='help_tutorials')],
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Help", callback_data='main_help')],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_help_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all available commands."""
    query = update.callback_query
    await query.answer()
    
    text = f"""📝 **Available Commands**

**Bot Management**
{EMOJI['robot']} `/start` - Show main menu
{EMOJI['add']} `/addbot` - Create a new bot
{EMOJI['robot']} `/mybots` - List your bots

**Help & Info**
{EMOJI['help']} `/help` - Show this help menu

**Settings** *(Coming Soon)*
⚙️ `/settings` - Bot settings
👤 `/admins` - Manage admins
🌐 `/language` - Change language

**Premium** *(Coming Soon)*
{EMOJI['premium']} `/premium` - View premium plans
{EMOJI['star']} `/myplan` - Your current plan

**Broadcasting** *(Phase 2)*
{EMOJI['broadcast']} `/newpost` - Create broadcast
{EMOJI['subscribers']} `/subscribers` - View subscribers

**Advanced** *(Future Phases)*
{EMOJI['menu']} `/buttons` - Button menu builder
{EMOJI['form']} `/forms` - Form builder
{EMOJI['analytics']} `/analytics` - View analytics
{EMOJI['calendar']} `/schedule` - Schedule posts

You can also use the inline keyboard buttons instead of typing commands!
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Help", callback_data='main_help')],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_help_tutorials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show tutorials menu."""
    query = update.callback_query
    await query.answer()
    
    text = f"""📚 **Tutorials**

Choose a topic to learn more:

**For Beginners**
• How to create your first bot
• Understanding bot tokens
• Sharing your bot with users

**Bot Management**
• Adding multiple bots
• Managing bot admins
• Deleting bots safely

**Coming Soon**
• Creating button menus
• Building forms
• Sending broadcasts
• Scheduling posts
• Using analytics

More tutorials will be added as new features are released!
"""
    
    keyboard = [
        [InlineKeyboardButton("🤖 First Bot Tutorial", callback_data='tutorial_first_bot')],
        [InlineKeyboardButton("🔑 Understanding Tokens", callback_data='tutorial_tokens')],
        [InlineKeyboardButton("👥 Sharing Your Bot", callback_data='tutorial_sharing')],
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Help", callback_data='main_help')],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_help_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show frequently asked questions."""
    query = update.callback_query
    await query.answer()
    
    text = f"""❓ **Frequently Asked Questions**

**Q: Is ChatFuel free?**
A: Yes! The free plan includes 3 bots with basic features. Premium plans unlock more bots and advanced features.

**Q: How many subscribers can I have?**
A: Unlimited! There's no limit on how many users can subscribe to your bots.

**Q: Can I delete a bot?**
A: Yes, go to /mybots, select the bot, and click Delete. Warning: This cannot be undone!

**Q: What happens to my subscribers if I delete a bot?**
A: They lose access to the bot. All data is permanently deleted.

**Q: Can multiple people manage one bot?**
A: Yes! Add admins to your bot (coming in future update).

**Q: Is my data safe?**
A: Yes! We encrypt bot tokens and follow security best practices.

**Q: Can I export my data?**
A: Yes! Premium plans include data export features (coming soon).

**Q: What if I forget my bot token?**
A: Get it from @BotFather anytime: /mybots → Select bot → API Token

**Q: Can I change my bot's username?**
A: Bot usernames cannot be changed after creation. You'd need to create a new bot.

**Q: Do you support group bots?**
A: Currently only for channel broadcasting. Group features coming soon!

Have more questions? Contact support!
"""
    
    keyboard = [
        [InlineKeyboardButton("📧 Contact Support", callback_data='help_contact')],
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Help", callback_data='main_help')],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_help_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show contact information."""
    query = update.callback_query
    await query.answer()
    
    text = f"""📧 **Contact Support**

**Need Help?**

**For Bug Reports:**
Use the 👎 thumbs down button below any message to report issues.

**For General Support:**
Email: support@chatfuel.example.com
Response time: Within 24 hours

**For Feature Requests:**
We'd love to hear your ideas!
Email: feedback@chatfuel.example.com

**For Premium Support:**
Premium members get priority support with faster response times.

**Community:**
Join our Telegram channel for updates: @ChatFuelUpdates

**GitHub:**
Found a bug? Report it on GitHub:
github.com/your-username/chatfuel

**Before Contacting:**
• Check the FAQ
• Try /start to refresh
• Make sure you're using the latest version

We're here to help! 💙
"""
    
    keyboard = [
        [InlineKeyboardButton("❓ Check FAQ First", callback_data='help_faq')],
        [InlineKeyboardButton(f"{EMOJI['back']} Back to Help", callback_data='main_help')],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# Tutorial detail pages
async def show_tutorial_first_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tutorial: Creating your first bot."""
    query = update.callback_query
    await query.answer()
    
    text = f"""🤖 **Tutorial: Your First Bot**

**Part 1: Create the Bot (2 minutes)**

1. Open Telegram and search for @BotFather
2. Send `/newbot` to BotFather
3. BotFather asks: "Choose a name"
   → Type: My First Bot
4. BotFather asks: "Choose a username"
   → Type: myfirstbot123\_bot
   (Must end with 'bot', must be unique)
5. BotFather gives you a token like:
   `1234567890:ABCdefGHIjklMNOpqr`
   → Copy this entire token!

**Part 2: Add to ChatFuel (1 minute)**

1. Come back to this chat
2. Send `/addbot`
3. Paste your token
4. Done! 🎉

**Part 3: Test Your Bot (30 seconds)**

1. Click the link BotFather gave you
2. Send /start to your bot
3. Your bot is now live!

**Next Steps:**
• Share your bot link
• Wait for subscribers
• Send your first broadcast (Phase 2)

**Tip:** Keep your bot token secret! It's like a password.

Ready to try? Send /addbot now!
"""
    
    keyboard = [
        [InlineKeyboardButton("🚀 Create Bot Now", callback_data='bot_create_new')],
        [InlineKeyboardButton("📚 More Tutorials", callback_data='help_tutorials')],
        [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data='main_help')],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_tutorial_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tutorial: Understanding bot tokens."""
    query = update.callback_query
    await query.answer()
    
    text = f"""🔑 **Understanding Bot Tokens**

**What is a Bot Token?**

A bot token is like a password that lets you control your bot. It looks like:
`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-1234567`

**Token Structure:**
• Numbers before colon: Bot ID
• After colon: Secret authentication key
• Total length: Usually 45+ characters

**Security Rules:**

1. **Never share your token publicly**
   ❌ Don't post on social media
   ❌ Don't commit to GitHub
   ❌ Don't send to strangers

2. **Store it safely**
   ✅ Use a password manager
   ✅ Keep a backup copy
   ✅ Save in secure notes

3. **What if it leaks?**
   → Go to @BotFather immediately
   → Send /mybots
   → Select your bot
   → Click "Revoke Token"
   → Get new token
   → Update in ChatFuel

**Finding Your Token:**

If you lost it:
1. Go to @BotFather
2. Send /mybots
3. Select your bot
4. Click "API Token"
5. Copy the token

**Important:**
• One token per bot
• Tokens don't expire (unless revoked)
• ChatFuel encrypts tokens in database
• You can regenerate tokens anytime

Keep your tokens safe! 🔐
"""
    
    keyboard = [
        [InlineKeyboardButton("📚 More Tutorials", callback_data='help_tutorials')],
        [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data='main_help')],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_tutorial_sharing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tutorial: Sharing your bot."""
    query = update.callback_query
    await query.answer()
    
    text = f"""👥 **Tutorial: Sharing Your Bot**

**Getting Your Bot Link:**

Your bot link is: `t.me/your_bot_username`

Example: If username is `@mycoolbot`, link is:
`t.me/mycoolbot`

**Best Places to Share:**

**1. Social Media**
• Twitter/X
• Facebook
• Instagram bio
• LinkedIn

**2. Your Website**
• Add a button
• Put in navigation
• Footer link

**3. Email**
• Email signature
• Newsletter
• Welcome emails

**4. Messaging Apps**
• WhatsApp status
• Telegram groups (ask permission first!)
• Discord server

**5. Offline**
• Business cards
• Flyers
• QR codes

**Tips for Success:**

✅ **Do:**
• Explain what your bot does
• Show the value/benefit
• Make it easy to click
• Use call-to-action ("Try it now!")

❌ **Don't:**
• Spam groups
• Send unsolicited messages
• Make false promises
• Be pushy

**Example Messages:**

"Check out my new bot! 🤖
Get daily motivation at t.me/motivationbot
Try it now!"

"Need quick recipes? 🍳
My bot has 1000+ ideas!
→ t.me/recipebot"

**Track Your Success:**
• Use /subscribers to see growth
• Ask users how they found you
• Try different messages

Ready to share? Go to /mybots and click your bot to get the link!
"""
    
    keyboard = [
        [InlineKeyboardButton("🤖 Go to My Bots", callback_data='main_mybots')],
        [InlineKeyboardButton("📚 More Tutorials", callback_data='help_tutorials')],
        [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data='main_help')],
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
