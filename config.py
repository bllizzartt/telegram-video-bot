"""
Configuration module for Telegram Video Bot.
Loads settings from .env file with environment variable override support.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""

    # Telegram
    telegram_bot_token: str
    admin_user_id: int

    # Seedance API
    seedance_api_key: str
    seedance_api_url: str
    mock_mode: bool = True

    # Storage
    video_storage_path: Path = Path("./videos")

    # Limits
    max_photos: int = 4
    generation_timeout: int = 300  # seconds
    status_update_interval: int = 30  # seconds

    @classmethod
    def load(cls, env_path: Optional[Path] = None) -> "Config":
        """Load configuration from .env file."""
        if env_path is None:
            env_path = Path(__file__).parent / ".env"

        # Load .env file if it exists
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())

        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            admin_user_id=int(os.getenv("ADMIN_USER_ID", "0")),
            seedance_api_key=os.getenv("SEEDANCE_API_KEY", ""),
            seedance_api_url=os.getenv(
                "SEEDANCE_API_URL", "https://api.seedance.example.com/v1"
            ),
            mock_mode=os.getenv("MOCK_MODE", "true").lower() == "true",
            video_storage_path=Path(os.getenv("VIDEO_STORAGE_PATH", "./videos")),
            max_photos=int(os.getenv("MAX_PHOTOS", "4")),
            generation_timeout=int(os.getenv("GENERATION_TIMEOUT", "300")),
            status_update_interval=int(os.getenv("STATUS_UPDATE_INTERVAL", "30")),
        )


def get_config() -> Config:
    """Get the bot configuration."""
    return Config.load()
