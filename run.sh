#!/bin/bash

# ChatFuel Bot Startup Script

echo "🤖 ChatFuel Bot - Starting..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found! Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Start the bot
echo "🚀 Starting bot..."
python main.py
