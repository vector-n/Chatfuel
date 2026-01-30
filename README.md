# 🤖 ChatFuel Bot - Telegram Bot Manager

A powerful Telegram bot that helps users create and manage their own broadcast bots with custom buttons, forms, and automation.

## 🌟 Features

### Free Tier
- Create up to 3 bots
- Basic broadcasting (text, photo, video)
- Custom button builder (up to 3 menus)
- Simple forms (1 form, 5 questions)
- Subscriber tracking
- Bot settings & admin management

### Premium Tiers
- **Basic Pro ($4.99/mo)**: Scheduled posts, unlimited menus, enhanced analytics
- **Advanced Pro ($9.99/mo)**: Auto-posting, advanced forms, A/B testing
- **Business ($19.99/mo)**: Unlimited everything, webhooks, white label

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Telegram Bot Token (from @BotFather)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chatfuel-bot
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Set up database:
```bash
# Create database
createdb chatfuel_db

# Run migrations
alembic upgrade head
```

6. Run the bot:
```bash
python main.py
```

## 📁 Project Structure

```
chatfuel-bot/
├── main.py                 # Entry point
├── config/                 # Configuration
├── database/              # Database models & migrations
├── handlers/              # Command handlers
├── services/              # Business logic
├── utils/                 # Utilities & helpers
├── tasks/                 # Background tasks
└── tests/                 # Tests
```

## 🔧 Configuration

Edit `.env` file with your settings:
- `BOT_TOKEN`: Your Telegram bot token
- `DATABASE_URL`: PostgreSQL connection string
- `ENVIRONMENT`: development/production

## 📝 Development

### Running Tests
```bash
pytest
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🚢 Deployment

### Railway.app
1. Connect your GitHub repository
2. Add PostgreSQL plugin
3. Set environment variables
4. Deploy!

### Render.com
1. Create new Web Service
2. Connect repository
3. Add PostgreSQL database
4. Set environment variables
5. Deploy!

## 📚 Documentation

See `/docs` folder for detailed documentation on:
- API Reference
- Database Schema
- User Flows
- Feature Guides

## 🤝 Contributing

Contributions are welcome! Please read CONTRIBUTING.md first.

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- Documentation: [docs.chatfuel.com](https://docs.chatfuel.com)
- Issues: GitHub Issues
- Email: support@chatfuel.com

## 🙏 Acknowledgments

Built with:
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [APScheduler](https://apscheduler.readthedocs.io/)

---

Made with ❤️ by ChatFuel Team
