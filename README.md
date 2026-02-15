# Telegram Video Bot - Seedance Integration

A Telegram bot for generating AI videos from photos using the Seedance (BytePlus) image-to-video API.

## Features

- 📸 **Photo Collection** - Accepts 1-4 reference photos per generation
- 🎬 **AI Video Generation** - Creates videos using Seedance's image-to-video technology
- 📝 **Prompt Templates** - Pre-built prompts for various video styles
- 📊 **Job Tracking** - SQLite database for tracking generations
- 🔄 **Status Updates** - Real-time progress updates during generation
- 🎯 **Mock Mode** - Testing without real API calls (enabled by default until Feb 24)

## Prerequisites

- Python 3.11+
- Telegram Bot Token (get from @BotFather)
- Seedance API Key (when available)

## Installation

### 1. Clone and Setup

```bash
cd /Users/cortana/.openclaw/workspace/projects/telegram-video-bot
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

### 4. Configure Environment

Copy the example environment file and edit:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
SEEDANCE_API_KEY=your_api_key_here
MOCK_MODE=true  # Set to false when API is ready
ADMIN_USER_ID=8148840480
```

## Usage

### Running Locally

```bash
python bot.py
```

### Running with Systemd (Production)

Copy the service file:

```bash
sudo cp telegram-video-bot.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/telegram-video-bot.service
```

Start and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start telegram-video-bot
sudo systemctl enable telegram-video-bot

# Check status
sudo systemctl status telegram-video-bot

# View logs
sudo journalctl -u telegram-video-bot -f
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and introduction |
| `/generate` | Start a new video generation flow |
| `/templates` | Show available prompt templates |
| `/status` | Check current generation status |
| `/history` | View recent generations |
| `/reset` | Cancel and reset current generation |

## Conversation Flow

```
User: /generate
Bot: Send me 1-4 photos of yourself
User: [uploads photos]
Bot: Photos saved! Now send me a prompt describing the video you want.
User: Dancing in Tokyo at night, cyberpunk style
Bot: Generating your video... This may take 2-3 minutes.
[2-3 minutes later]
Bot: Your video is ready! [video file]
```

## Mock Mode

Mock mode is enabled by default, allowing you to test the bot flow without actual API calls:

- Returns placeholder text files instead of real videos
- Simulates async generation (30 second wait)
- Useful for UI/UX testing

To disable mock mode when ready:

```env
MOCK_MODE=false
```

## Project Structure

```
telegram-video-bot/
├── bot.py              # Main entry point
├── config.py           # Configuration management
├── database.py         # SQLite job tracking
├── seedance.py         # Seedance API client
├── handlers/
│   ├── __init__.py
│   ├── photo_handler.py    # Photo uploads
│   ├── prompt_handler.py    # Prompt collection
│   ├── status_handler.py    # Status queries
│   └── video_handler.py     # Video delivery
├── templates.py        # Prompt templates
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## Database Schema

### Jobs Table
```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    chat_id INTEGER,
    photos TEXT,           -- JSON array of file paths
    prompt TEXT,
    status TEXT,           -- pending, generating, completed, failed
    seedance_job_id TEXT,
    video_path TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### User Sessions Table
```sql
CREATE TABLE user_sessions (
    user_id INTEGER PRIMARY KEY,
    state TEXT,            -- idle, awaiting_prompt, generating
    photos TEXT,
    current_prompt TEXT,
    last_job_id INTEGER,
    updated_at TIMESTAMP
);
```

## Troubleshooting

### Bot not responding

1. Check if bot is running:
   ```bash
   sudo systemctl status telegram-video-bot
   ```

2. Check logs:
   ```bash
   sudo journalctl -u telegram-video-bot -f
   ```

### Photos not uploading

- Ensure the `photos/` directory exists and is writable
- Check file size limits (Telegram max 10MB per photo)

### Video generation failing

- Verify API key in `.env`
- Check mock mode setting
- Review Seedance API status

## Updating the Bot

```bash
# Stop the service
sudo systemctl stop telegram-video-bot

# Pull updates
git pull

# Restart
sudo systemctl start telegram-video-bot
```

## Security Notes

- Never commit `.env` with real credentials
- The bot only stores photos temporarily during generation
- Photos are deleted from disk after video delivery
- User data is stored locally in SQLite (not shared)

## License

MIT License - See LICENSE file for details.
