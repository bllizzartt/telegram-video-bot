#!/bin/bash
# Telegram Video Bot - Background Startup

cd /Users/cortana/.openclaw/workspace/projects/telegram-video-bot

# Create .env if missing
if [ ! -f .env ]; then
    echo "Setting up environment..."
    cat > .env << EOF
TELEGRAM_BOT_TOKEN=8572628843:AAFFl71Dpj3DRyAYJrCRJ66sYBGKJV3y9PA
MOCK_MODE=true
ADMIN_USER_ID=8148840480
SEEDANCE_API_KEY=placeholder
SEEDANCE_API_URL=https://api.seedance.example.com/v1
EOF
    echo "✅ .env created"
fi

# Create virtual environment if missing
if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install
echo "Installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

# Start the bot in background
echo "🚀 Starting Telegram Video Bot..."
echo "Send photos to @Cortana738468373_bot"
nohup python bot.py > bot.log 2>&1 &
echo $! > bot.pid
echo "✅ Bot started! PID: $(cat bot.pid)"
echo "📋 Logs: tail -f /Users/cortana/.openclaw/workspace/projects/telegram-video-bot/bot.log"
