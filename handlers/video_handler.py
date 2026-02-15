"""
Video handler for video delivery and management.
"""

from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import CallbackContext

from database import Database


class VideoHandler:
    """Handles video delivery and file management."""

    def __init__(self, db: Database):
        self.db = db

    async def send_video(
        self,
        bot,
        chat_id: int,
        video_path: str,
        caption: str = "🎬 Your AI-generated video!",
    ) -> bool:
        """
        Send a video to a chat.

        Args:
            bot: Telegram bot instance
            chat_id: Target chat ID
            video_path: Path to the video file
            caption: Optional caption

        Returns:
            True if successful, False otherwise
        """
        try:
            video_file = Path(video_path)
            if not video_file.exists():
                await bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Video file not found. It may have been deleted or moved.",
                )
                return False

            # Check file size (Telegram limit is 50MB for bots)
            file_size = video_file.stat().st_size
            if file_size > 50 * 1024 * 1024:  # 50MB
                await bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Generated video is too large for Telegram (>50MB). "
                    "Please try again with a shorter video or different settings.",
                )
                return False

            # Send video
            with open(video_file, "rb") as video:
                await bot.send_video(
                    chat_id=chat_id,
                    video=video,
                    caption=caption,
                )

            return True

        except Exception as e:
            print(f"Error sending video: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Could not send video: {str(e)}",
            )
            return False

    async def send_video_by_job(
        self, update: Update, context: CallbackContext, job_id: int
    ) -> None:
        """Send a video based on job ID."""
        job = self.db.get_job(job_id)

        if not job:
            await update.message.reply_text("Job not found.")
            return

        video_path = job.get("video_path")
        if not video_path:
            await update.message.reply_text(
                "Video not available for this job."
            )
            return

        await self.send_video(
            context.bot,
            update.effective_chat.id,
            video_path,
            caption=f"🎬 Video from job #{job_id}",
        )

    async def send_video_by_url(
        self, bot, chat_id: int, video_url: str, caption: str = ""
    ) -> bool:
        """
        Send a video from a URL.

        Note: This may not work with all URLs due to Telegram's limitations.
        Downloading and sending locally is preferred.
        """
        try:
            await bot.send_video(
                chat_id=chat_id,
                video=video_url,
                caption=caption,
            )
            return True
        except Exception as e:
            print(f"Error sending video from URL: {e}")
            return False

    def delete_video(self, video_path: str) -> bool:
        """
        Delete a video file.

        Args:
            video_path: Path to the video file

        Returns:
            True if deleted, False otherwise
        """
        try:
            Path(video_path).unlink()
            return True
        except OSError:
            return False

    def cleanup_user_videos(self, user_id: int) -> int:
        """
        Clean up all videos for a user.

        Args:
            user_id: The user's ID

        Returns:
            Number of files deleted
        """
        deleted = 0
        jobs = self.db.get_user_jobs(user_id, limit=100)

        for job in jobs:
            video_path = job.get("video_path")
            if video_path and self.delete_video(video_path):
                deleted += 1

        return deleted

    def get_video_info(self, video_path: str) -> Optional[dict]:
        """
        Get information about a video file.

        Args:
            video_path: Path to the video file

        Returns:
            Dict with video info or None if file doesn't exist
        """
        try:
            path = Path(video_path)
            if not path.exists():
                return None

            stat = path.stat()
            return {
                "path": str(path),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "exists": True,
            }
        except Exception:
            return None
