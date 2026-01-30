# 🚀 ChatFuel Bot - Phase 1 Setup Guide

## ✅ What's Included in Phase 1

Phase 1 implements the **foundation** of ChatFuel Bot with these features:

### Core Features:
- ✅ User authentication and database storage
- ✅ `/start` command with interactive main menu
- ✅ `/addbot` - Create bots by providing BotFather token
- ✅ `/mybots` - List and manage created bots
- ✅ Bot deletion with confirmation
- ✅ Premium tier system (framework ready)
- ✅ Inline keyboard navigation
- ✅ `/help` command

### What Users Can Do:
1. Start the bot and see a welcome message
2. Create up to 3 bots (free tier limit)
3. View list of their bots
4. Select and manage individual bots
5. Delete bots with confirmation
6. See their subscription tier

---

## 📋 Prerequisites

Before you begin, make sure you have:

- **Python 3.11+** installed
- **PostgreSQL 15+** installed and running
- **Telegram Bot Token** from @BotFather
- **Git** (optional, for version control)

---

## 🔧 Installation Steps

### 1. Clone/Download the Project

```bash
cd chatfuel-bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

Create a new database for the bot:

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE chatfuel_db;

# Create user (optional)
CREATE USER chatfuel_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chatfuel_db TO chatfuel_user;

# Exit
\q
```

### 5. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
# REQUIRED - Get from @BotFather
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# REQUIRED - Your bot username
BOT_USERNAME=chatfuelRobot

# REQUIRED - Database connection
DATABASE_URL=postgresql://chatfuel_user:your_password@localhost:5432/chatfuel_db

# OPTIONAL - For encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your_fernet_key_here

# OPTIONAL - Admin user IDs (comma-separated)
ADMIN_USER_IDS=123456789,987654321

# Environment
ENVIRONMENT=development
```

### 6. Initialize Database

The database tables will be created automatically when you first run the bot:

```bash
python main.py
```

Alternatively, you can use Alembic for migrations:

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

---

## 🚀 Running the Bot

### Development Mode (Polling)

```bash
# Using the convenience script
./run.sh

# Or directly
python main.py
```

The bot will start in polling mode and you'll see:

```
🚀 Starting ChatFuel Bot...
Environment: development
Bot username: @chatfuelRobot
```

### Test the Bot

1. Open Telegram
2. Search for your bot (e.g., @chatfuelRobot)
3. Send `/start`
4. You should see the welcome message with inline keyboard menu

---

## 🧪 Testing Phase 1 Features

### Test 1: Start Command
1. Send `/start` to your bot
2. Verify you see the welcome message
3. Verify inline keyboard appears with options:
   - My Bots
   - New Post
   - Analytics
   - Settings
   - Premium
   - Help

### Test 2: Create a Bot
1. Click "My Bots" button
2. Click "Create New Bot"
3. Follow instructions to get a bot token from @BotFather:
   - Go to @BotFather
   - Send `/newbot`
   - Choose name and username
   - Copy the token
4. Send the token to ChatFuel bot
5. Verify success message appears
6. Verify bot appears in your bot list

### Test 3: Manage Bots
1. Click "My Bots"
2. Click on one of your bots
3. Verify bot information displays correctly
4. Test the management buttons (some will show "Coming soon")

### Test 4: Delete Bot
1. From bot management screen, click "Delete Bot"
2. Verify confirmation message appears
3. Click "Cancel" first to test cancellation
4. Click "Delete Bot" again
5. Click "Yes, Delete"
6. Verify bot is removed from database

### Test 5: Premium Limits
1. Try to create more than 3 bots (free tier limit)
2. Verify you get a limit reached message
3. Verify upgrade prompt appears

---

## 🗄️ Database Structure

Phase 1 creates these tables:

- `users` - ChatFuel bot users
- `bots` - User-created bots
- `bot_admins` - Bot administrators
- `subscribers` - Subscribers to created bots
- `button_menus` - Custom button menus
- `buttons` - Individual buttons
- `button_clicks` - Button analytics
- `forms` - Data collection forms
- `form_questions` - Form questions
- `form_responses` - Form submissions
- `form_answers` - Individual answers
- `broadcasts` - Broadcast messages
- `broadcast_stats` - Broadcast analytics
- `scheduled_posts` - Scheduled messages
- `payments` - Payment records

**Note:** Not all tables are actively used in Phase 1, but they're created for future phases.

---

## 🔍 Troubleshooting

### Bot Token Invalid
**Error:** "Invalid bot token"
**Solution:** 
- Double-check your token in `.env`
- Make sure there are no extra spaces
- Verify the token works by testing with @BotFather

### Database Connection Error
**Error:** "Could not connect to database"
**Solution:**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check your DATABASE_URL in `.env`
- Verify database exists: `psql -l`

### Module Not Found Errors
**Error:** "ModuleNotFoundError: No module named 'X'"
**Solution:**
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Bot Not Responding
**Solution:**
- Check bot logs for errors
- Verify bot token is correct
- Restart the bot: `Ctrl+C` then `python main.py`

---

## 📁 Project Structure

```
chatfuel-bot/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env                   # Configuration (create from .env.example)
├── alembic.ini            # Database migrations config
├── run.sh                 # Startup script
├──
├── config/
│   ├── settings.py        # App configuration
│   └── constants.py       # Constants and limits
│
├── database/
│   ├── models.py          # Database models
│   ├── session.py         # DB session management
│   └── migrations/        # Alembic migrations
│
├── handlers/
│   ├── start.py           # /start command
│   ├── bot_management.py  # Bot CRUD operations
│   ├── help.py            # Help command
│   └── broadcasting.py    # Placeholder for Phase 2
│
└── utils/
    ├── keyboards.py       # Inline keyboard builders
    ├── validators.py      # Input validation
    ├── formatters.py      # Message formatting
    ├── helpers.py         # Utility functions
    ├── permissions.py     # Permission checks
    └── decorators.py      # Handler decorators
```

---

## ✅ Phase 1 Checklist

- [x] Database models created
- [x] User authentication implemented
- [x] Start command with main menu
- [x] Bot creation flow (with @BotFather token)
- [x] Bot listing
- [x] Bot deletion with confirmation
- [x] Premium tier system (framework)
- [x] Inline keyboard navigation
- [x] Help command
- [x] Error handling
- [x] Input validation

---

## 🎯 Next Steps (Phase 2)

Phase 2 will implement:
- Broadcasting system (send messages to subscribers)
- Subscriber tracking
- Basic analytics
- Message preview before sending

---

## 🆘 Getting Help

If you encounter issues:

1. Check this setup guide
2. Review error messages carefully
3. Check the logs for detailed error information
4. Verify all environment variables are set correctly

---

## 🎉 Success!

If you can:
1. ✅ Start the bot
2. ✅ See the welcome message
3. ✅ Create a bot using a BotFather token
4. ✅ View your bots list
5. ✅ Delete a bot

**Congratulations! Phase 1 is working perfectly!** 🚀

You're ready to move on to Phase 2 once you're comfortable with the current functionality.
