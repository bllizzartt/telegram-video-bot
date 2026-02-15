"""
Main Telegram Bot for AI Video Generation using Seedance.

This bot enables users to generate AI videos from their photos
using the Seedance (BytePlus) image-to-video API.

Features:
- Photo collection (1-4 reference images)
- Prompt-based video generation
- Job queue with SQLite tracking
- Real-time status updates
- Video delivery
- Mock mode for testing
"""

import asyncio
import logging
import os
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import get_config
from database import Database
from handlers.photo_handler import PhotoHandler
from handlers.prompt_handler import PromptHandler
from handlers.status_handler import StatusHandler
from handlers.video_handler import VideoHandler

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class TelegramVideoBot:
    """Main Telegram bot class for video generation."""

    def __init__(self):
        self.config = get_config()
        self.db = Database(Path("./jobs.db"))

        # Initialize handlers
        self.photo_handler = PhotoHandler(self.db, self.config)
        self.prompt_handler = PromptHandler(self.db, self.config)
        self.status_handler = StatusHandler(self.db)
        self.video_handler = VideoHandler(self.db)

        # Bot application
        self.app = None

    async def init_app(self) -> None:
        """Initialize the bot application."""
        self.app = (
            ApplicationBuilder()
            .token(self.config.telegram_bot_token)
            .concurrent_updates(True)
            .build()
        )

        # Register handlers
        self._register_handlers()

        # Create storage directories
        self._create_directories()

        logger.info("Bot initialized successfully")

    def _register_handlers(self) -> None:
        """Register all command and message handlers."""

        # Command handlers
        self.app.add_handler(
            CommandHandler("start", self.handle_start)
        )
        self.app.add_handler(
            CommandHandler("help", self.handle_help)
        )
        self.app.add_handler(
            CommandHandler("generate", self.handle_generate)
        )
        self.app.add_handler(
            CommandHandler("templates", self.handle_templates)
        )
        self.app.add_handler(
            CommandHandler("status", self.status_handler.handle_status)
        )
        self.app.add_handler(
            CommandHandler("history", self.status_handler.handle_history)
        )
        self.app.add_handler(
            CommandHandler("reset", self.handle_reset)
        )
        self.app.add_handler(
            CommandHandler("cancel", self.handle_cancel)
        )

        # Message handlers
        # Photos
        self.app.add_handler(
            MessageHandler(
                filters.PHOTO | filters.Document.IMAGE,
                self.photo_handler.handle_photos,
            )
        )

        # Text messages (prompts)
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.prompt_handler.handle_prompt,
            )
        )

        # Error handler
        self.app.add_error_handler(self.handle_error)

    def _create_directories(self) -> None:
        """Create necessary storage directories."""
        Path("./photos").mkdir(exist_ok=True)
        Path("./videos").mkdir(exist_ok=True)

    async def handle_start(self, update: Update, context: ContextTypes) -> None:
        """Handle /start command."""
        user = update.effective_user

        welcome_text = (
            f"👋 Hello, {user.mention_html()}!\n\n"
            "I'm *Seedance Bot*, and I can generate AI videos from your photos! 🎬\n\n"
            "Here's what I can do:\n"
            "• Send me 1-4 photos of yourself\n"
            "• Describe the video you want\n"
            "• I'll create an AI-generated video!\n\n"
            "*Commands:*\n"
            "• /generate - Start a new video generation\n"
            "• /templates - See prompt ideas\n"
            "• /status - Check current generation\n"
            "• /history - See your previous generations\n"
            "• /help - Show this help message\n\n"
            "🔒 *Privacy:* Your photos are used only for video generation and are not stored beyond the process."
        )

        await update.message.reply_html(welcome_text)

        # Reset any existing session
        self.db.reset_user_generation_state(user.id)

    async def handle_help(self, update: Update, context: ContextTypes) -> None:
        """Handle /help command."""
        help_text = (
            "📚 *Seedance Bot Help*\n\n"
            "*Getting Started:*\n"
            "1. Use /generate to start\n"
            "2. Send 1-4 photos of yourself\n"
            "3. Describe your video with a prompt\n"
            "4. Wait 2-3 minutes for generation\n\n"
            "*Tips for Best Results:*\n"
            "• Use clear, well-lit photos\n"
            "• Include your full body if you want full-body motion\n"
            "• Be specific in your prompt (location, mood, actions)\n\n"
            "*Commands:*\n"
            "• /generate - Start over\n"
            "• /templates - Browse prompt ideas\n"
            "• /status - Check progress\n"
            "• /history - View past generations\n"
            "• /reset - Cancel current generation\n\n"
            "*Privacy:* Photos are temporary and deleted after video generation."
        )

        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_generate(
        self, update: Update, context: ContextTypes
    ) -> None:
        """Handle /generate command - start new generation flow."""
        user_id = update.effective_user.id

        # Reset any existing session
        self.db.reset_user_generation_state(user_id)

        # Request photos
        await self.photo_handler.ask_for_photos(update, context)

    async def handle_templates(
        self, update: Update, context: ContextTypes
    ) -> None:
        """Handle /templates command - show prompt templates."""
        await self.prompt_handler.show_templates(update, context)

    async def handle_reset(self, update: Update, context: ContextTypes) -> None:
        """Handle /reset command - cancel current generation."""
        user_id = update.effective_user.id

        # Clear photos from storage
        self.photo_handler.clear_user_photos(user_id)

        # Reset session in database
        self.db.reset_user_generation_state(user_id)

        await update.message.reply_text(
            "🔄 *Generation cancelled and cleared.*\n\n"
            "Use /generate to start fresh!",
            parse_mode="Markdown",
        )

    async def handle_cancel(self, update: Update, context: ContextTypes) -> None:
        """Handle /cancel command - alias for /reset."""
        await self.handle_reset(update, context)

    async def handle_error(
        self, update: Update, context: ContextTypes
    ) -> None:
        """Handle errors."""
        logger.error(
            f"Exception while handling update {update.update_id}: {context.error}"
        )

        # Notify user
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ An error occurred. Please try again or use /reset."
            )

    async def run(self) -> None:
        """Run the bot."""
        await self.init_app()

        logger.info("Starting bot...")
        await self.app.initialize()
        await self.app.start()

        # Run until interrupted
        try:
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
            logger.info("Bot is running!")

            # Keep the bot running
            await asyncio.Event().wait()

        except asyncio.CancelledError:
            logger.info("Shutting down...")
        finally:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()


async def main():
    """Main entry point."""
    bot = TelegramVideoBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
