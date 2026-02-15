# 🎥 Telegram Video Bot

Standalone video generation bot using Seedance AI. Upload photos + prompt = AI video.

## 🎯 Features

- Upload 1-4 photos of yourself
- Send text prompt
- Get AI-generated video
- Character consistency across videos
- 1080p cinematic quality

## 📱 Usage

Message `@Cortana738468373_bot`:

1. Send `/generate` to start
2. Upload 1-4 photos
3. Type your prompt (e.g., "Dancing in Tokyo streets")
4. Wait 2-3 minutes
5. Receive video!

## 🛠️ Setup

```bash
# Install dependencies
pip3 install python-telegram-bot aiohttp

# Run bot
./start.sh

# Or background mode
./start-bg.sh
```

## 📁 Structure

```
telegram-video-bot/
├── bot.py                 # Main bot
├── seedance.py           # Seedance API client
├── handlers/
│   ├── photo_handler.py  # Photo upload
│   ├── prompt_handler.py # Prompt collection
│   └── video_handler.py  # Video delivery
├── database.py           # SQLite jobs
├── templates.py          # Prompt templates
└── start.sh
```

## ⚙️ Configuration

Edit `.env`:
```
TELEGRAM_BOT_TOKEN=your_token
SEEDANCE_API_KEY=your_key  # After Feb 24
MOCK_MODE=true             # Set false for real videos
```

## 🎬 Prompt Templates

Built-in templates:
- "Dancing in [location]"
- "Presenting at tech conference"
- "Walking through futuristic city"
- "Fitness workout montage"

## ⏰ Important Date

**February 24, 2026** — Seedance API launches

After Feb 24:
1. Get Seedance API key from BytePlus
2. Set `MOCK_MODE=false`
3. Start generating real videos!

## 🎯 Integration

This is merged into **cortana-mega-bot** as `/video` command.

This standalone version useful for:
- Testing separately
- Custom modifications
- Backup bot

---
AI video generation made simple ⚡
