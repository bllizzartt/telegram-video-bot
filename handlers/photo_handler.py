"""
Photo handler for managing user-uploaded reference images.
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from telegram import Update
from telegram.ext import CallbackContext

from config import get_config
from database import Database


class PhotoHandler:
    """Handles photo upload and storage for video generation."""

    def __init__(self, db: Database, config=None):
        self.db = db
        self.config = config or get_config()
        self.photo_storage_path = Path("./photos")
        self.photo_storage_path.mkdir(parents=True, exist_ok=True)

    async def handle_photos(
        self, update: Update, context: CallbackContext
    ) -> None:
        """
        Handle photo uploads from users.
        Supports 1-4 photos per generation request.
        """
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Get current session
        session = self.db.get_user_session(user_id)
        current_photos = json.loads(session.get("photos", "[]")) if session else []

        # Check if we already have maximum photos
        if len(current_photos) >= self.config.max_photos:
            await update.message.reply_text(
                f"⚠️ You already have {len(current_photos)} photos. "
                "Please send your prompt first, or use /reset to start over."
            )
            return

        # Process incoming photos
        new_photos = []
        message = update.message

        # Handle single photo
        if message.photo:
            photo = message.photo[-1]  # Get highest resolution
            file_id = photo.file_id
            file_path = await self._save_photo(
                user_id, file_id, context, len(current_photos)
            )
            if file_path:
                new_photos.append(file_path)

        # Handle photo array (album)
        elif message.media_group_id:
            # For album uploads, we'd need to handle differently
            # This is a simplified version
            if message.photo:
                photo = message.photo[-1]
                file_id = photo.file_id
                file_path = await self._save_photo(
                    user_id, file_id, context, len(current_photos)
                )
                if file_path:
                    new_photos.append(file_path)

        # Handle document (if user sends as file)
        elif message.document and message.document.mime_type.startswith(
            "image/"
        ):
            file_id = message.document.file_id
            file_path = await self._save_photo(
                user_id, file_id, context, len(current_photos)
            )
            if file_path:
                new_photos.append(file_path)

        if not new_photos:
            await update.message.reply_text(
                "❌ Could not process the image. Please try again."
            )
            return

        # Update session with new photos
        all_photos = current_photos + new_photos

        # Update database
        if session:
            self.db.update_user_state(
                user_id,
                state="awaiting_prompt",
                photos=all_photos,
            )
        else:
            self.db.update_user_state(
                user_id,
                state="awaiting_prompt",
                photos=all_photos,
            )

        # Count remaining slots
        remaining = self.config.max_photos - len(all_photos)

        # Build response
        if remaining > 0:
            response = (
                f"✅ Photo saved! ({len(all_photos)}/{self.config.max_photos})\n\n"
                f"You can send {remaining} more photo(s), or send your prompt now."
            )
        else:
            response = (
                "✅ All photos received! 📸\n\n"
                "Now send me a prompt describing the video you want to create.\n\n"
                "Examples:\n"
                "• 'Dancing in a futuristic city at night'\n"
                "• 'Walking through Paris in the rain'\n"
                "• 'Presenting at a tech conference'\n\n"
                "Use /templates to see more ideas!"
            )

        await update.message.reply_text(response)

    async def _save_photo(
        self,
        user_id: int,
        file_id: str,
        context: CallbackContext,
        index: int,
    ) -> Optional[str]:
        """Save a photo to storage and return its path."""
        try:
            # Get file from Telegram
            bot = context.bot
            file = await bot.get_file(file_id)

            # Create unique filename
            timestamp = int(os.path.getctime(__file__))
            filename = f"{user_id}_{timestamp}_{index}.jpg"
            file_path = self.photo_storage_path / filename

            # Download file
            await file.download_to_drive(str(file_path))

            return str(file_path)

        except Exception as e:
            print(f"Error saving photo: {e}")
            return None

    def get_user_photos(self, user_id: int) -> List[str]:
        """Get list of photos for a user."""
        session = self.db.get_user_session(user_id)
        if session:
            return json.loads(session.get("photos", "[]"))
        return []

    def clear_user_photos(self, user_id: int) -> None:
        """Clear photos for a user from storage."""
        photos = self.get_user_photos(user_id)
        for photo_path in photos:
            try:
                Path(photo_path).unlink()
            except OSError:
                pass  # File might already be deleted

    async def ask_for_photos(
        self, update: Update, context: CallbackContext
    ) -> None:
        """Send the initial request for photos."""
        from templates import format_quick_templates

        welcome_text = (
            "📸 *Send me 1-4 photos of yourself*\n\n"
            "These photos will be used as reference for the AI video generation. "
            "For best results:\n"
            "• Use clear, well-lit photos\n"
            "• Include various angles if possible\n"
            "• Avoid heavy filters or edits\n\n"
            f"You can send {self.config.max_photos} photo(s) maximum."
        )

        await update.message.reply_text(welcome_text, parse_mode="Markdown")
