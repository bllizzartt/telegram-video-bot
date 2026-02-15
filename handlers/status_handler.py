"""
Status handler for checking job status and progress.
"""

from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import CallbackContext

from database import Database


class StatusHandler:
    """Handles status queries and progress updates."""

    def __init__(self, db: Database):
        self.db = db

    async def handle_status(
        self, update: Update, context: CallbackContext
    ) -> None:
        """Handle /status command to show job status."""
        user_id = update.effective_user.id

        # Get session
        session = self.db.get_user_session(user_id)

        if not session or session.get("state") == "idle":
            await update.message.reply_text(
                "📊 *Your Status*\n\n"
                "No active generation. Use /generate to start creating videos!",
                parse_mode="Markdown",
            )
            return

        # Get last job
        last_job_id = session.get("last_job_id")
        if not last_job_id:
            await update.message.reply_text(
                "📊 *Your Status*\n\n"
                "Preparing to generate... Use /generate to start!",
                parse_mode="Markdown",
            )
            return

        # Get job details
        job = self.db.get_job(last_job_id)
        if not job:
            await update.message.reply_text(
                "📊 *Your Status*\n\n"
                "Job not found. Try /generate again.",
                parse_mode="Markdown",
            )
            return

        # Format status message
        status_emoji = self._get_status_emoji(job["status"])
        status_text = self._format_status(job)

        # Check if completed
        if job["status"] == "completed":
            # Reset to idle after showing completed status
            self.db.reset_user_generation_state(user_id)

            response = (
                f"✅ *Last Generation Complete!*\n\n"
                f"{status_text}\n\n"
                "Use /generate to create another video!"
            )
        elif job["status"] == "failed":
            # Reset on failure
            self.db.clear_user_session(user_id)

            response = (
                f"❌ *Last Generation Failed*\n\n"
                f"{status_text}\n\n"
                "Try /generate again with a different prompt or photos."
            )
        else:
            photos_count = len(__import__("json").loads(job.get("photos", "[]")))
            response = (
                f"📊 *Generation Status*\n\n"
                f"{status_emoji} {status_text}\n\n"
                f"📸 Photos: {photos_count}\n"
                f"📝 Prompt: {job['prompt'][:100]}...\n\n"
                "⏳ Please wait while your video is being generated..."
            )

        await update.message.reply_text(response, parse_mode="Markdown")

    async def handle_history(
        self, update: Update, context: CallbackContext
    ) -> None:
        """Handle /history command to show recent jobs."""
        user_id = update.effective_user.id
        jobs = self.db.get_user_jobs(user_id, limit=10)

        if not jobs:
            await update.message.reply_text(
                "📋 *Generation History*\n\n"
                "No previous generations. Use /generate to create your first video!",
                parse_mode="Markdown",
            )
            return

        # Format history
        lines = ["📋 *Your Recent Generations*\n"]
        for job in jobs:
            status_emoji = self._get_status_emoji(job["status"])
            date = datetime.fromisoformat(
                job["created_at"].replace("Z", "+00:00")
            ).strftime("%b %d, %H:%M")

            prompt_preview = job["prompt"][:30] + "..." if len(job["prompt"]) > 30 else job["prompt"]

            lines.append(
                f"{status_emoji} *Job #{job['id']}* - {date}\n"
                f"   📝 {prompt_preview}\n"
            )

        await update.message.reply_text(
            "\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True
        )

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for job status."""
        status_map = {
            "pending": "⏳",
            "generating": "🎬",
            "processing": "🔄",
            "completed": "✅",
            "failed": "❌",
        }
        return status_map.get(status, "❓")

    def _format_status(self, job: dict) -> str:
        """Format job status details."""
        lines = []

        status = job.get("status", "unknown")
        lines.append(f"*Status:* {status.title()}")

        if job.get("seedance_job_id"):
            lines.append(f"*Job ID:* `{job['seedance_job_id']}`")

        if job.get("error_message"):
            lines.append(f"*Error:* {job['error_message']}")

        created_at = job.get("created_at")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                lines.append(f"*Started:* {dt.strftime('%Y-%m-%d %H:%M')}")
            except ValueError:
                pass

        if job.get("completed_at"):
            try:
                dt = datetime.fromisoformat(
                    job["completed_at"].replace("Z", "+00:00")
                )
                lines.append(f"*Completed:* {dt.strftime('%Y-%m-%d %H:%M')}")
            except ValueError:
                pass

        return "\n".join(lines)

    def get_job_status(self, job_id: int) -> Optional[dict]:
        """Get status of a specific job."""
        return self.db.get_job(job_id)

    def format_progress_message(self, job: dict) -> str:
        """Format a progress update message."""
        status = job.get("status", "pending")
        progress = job.get("progress", 0)

        progress_bar = self._make_progress_bar(progress)

        if status == "generating":
            return (
                f"🎬 *Generating Your Video*\n\n"
                f"{progress_bar} {progress}%\n\n"
                "⏳ AI is working on your video. This typically takes 2-3 minutes..."
            )
        elif status == "processing":
            return (
                f"🔄 *Processing Your Video*\n\n"
                f"{progress_bar} {progress}%\n\n"
                "Almost done! Finalizing your video..."
            )
        else:
            return f"📊 Status: {status.title()} ({progress}%)"

    def _make_progress_bar(self, progress: int, width: int = 20) -> str:
        """Create a text progress bar."""
        filled = int(progress / 100 * width)
        empty = width - filled
        return "█" * filled + "░" * empty
