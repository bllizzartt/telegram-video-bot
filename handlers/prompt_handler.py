"""
Prompt handler for collecting and validating video generation prompts.
"""

import json
from pathlib import Path
from typing import List, Optional

from telegram import Update
from telegram.ext import CallbackContext

from config import get_config
from database import Database
from templates import format_templates_list, get_template_by_name


class PromptHandler:
    """Handles prompt collection and validation for video generation."""

    def __init__(self, db: Database, config=None):
        self.db = db
        self.config = config or get_config()
        self.min_prompt_length = 10
        self.max_prompt_length = 500

    async def handle_prompt(
        self, update: Update, context: CallbackContext
    ) -> None:
        """
        Handle text prompt from user.
        Validates and stores the prompt, then starts generation.
        """
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        prompt_text = update.message.text.strip()

        # Get current session
        session = self.db.get_user_session(user_id)

        if not session:
            await update.message.reply_text(
                "Please start a new generation with /generate first."
            )
            return

        # Check if we have photos
        photos = json.loads(session.get("photos", "[]"))
        if not photos:
            await update.message.reply_text(
                "I need photos first! Please send 1-4 reference photos using /generate."
            )
            return

        # Validate prompt
        validation_error = self._validate_prompt(prompt_text)
        if validation_error:
            await update.message.reply_text(f"❌ {validation_error}")
            return

        # Store the prompt
        self.db.update_user_state(
            user_id,
            state="generating",
            current_prompt=prompt_text,
        )

        # Create job in database
        job_id = self.db.create_job(
            user_id=user_id,
            chat_id=chat_id,
            photos=photos,
            prompt=prompt_text,
        )

        # Update session with job ID
        self.db.update_user_state(
            user_id,
            state="generating",
            last_job_id=job_id,
        )

        # Start generation in background
        await self._start_generation(update, context, job_id, photos, prompt_text)

    async def _start_generation(
        self,
        update: Update,
        context: CallbackContext,
        job_id: int,
        photos: List[str],
        prompt: str,
    ) -> None:
        """Start the video generation process."""
        from seedance import SeedanceClient, VideoGenerationRequest

        client = SeedanceClient(self.config)

        # Prepare request
        image_paths = [Path(p) for p in photos]
        request = VideoGenerationRequest(
            prompt=prompt,
            images=image_paths,
            resolution="1080p",
        )

        # Send initial status message
        status_message = await update.message.reply_text(
            "🎬 *Starting video generation...*\n\n"
            "⏳ Preparing your images and prompt...\n"
            "This may take 2-3 minutes.",
            parse_mode="Markdown",
        )

        # Update job status
        self.db.update_job_status(job_id, "generating")

        try:
            # Start generation
            response = await client.generate_video(request)

            if response.status.value == "completed":
                # Update job with success
                self.db.update_job_status(
                    job_id,
                    "completed",
                    seedance_job_id=response.job_id,
                    video_path=response.video_url,
                )

                # Send success message with video
                await status_message.edit_text(
                    "✅ *Video generated successfully!*\n\n"
                    "Your video is ready. Sending it now...",
                    parse_mode="Markdown",
                )

                # Send video
                await self._send_video(
                    context.bot, update.effective_chat.id, response.video_url
                )

                # Final confirmation
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🎉 *Done!* Your AI-generated video has been sent!\n\n"
                    "Use /generate to create another video, or /templates for ideas.",
                    parse_mode="Markdown",
                )

                # Reset user state
                self.db.reset_user_generation_state(update.effective_user.id)

            else:
                # Generation failed
                await status_message.edit_text(
                    f"❌ *Generation failed*\n\n{response.error_message}",
                    parse_mode="Markdown",
                )
                self.db.update_job_status(
                    job_id, "failed", error_message=response.error_message
                )
                self.db.clear_user_session(user_id)

        except Exception as e:
            error_msg = str(e)
            await status_message.edit_text(
                f"❌ *An error occurred*\n\n{error_msg}",
                parse_mode="Markdown",
            )
            self.db.update_job_status(job_id, "failed", error_message=error_msg)
            self.db.clear_user_session(update.effective_user.id)

    async def _send_video(
        self, bot, chat_id: int, video_path: str
    ) -> None:
        """Send the generated video to the user."""
        try:
            # Check if this is a mock file (mock mode)
            if video_path.endswith('.mock'):
                await bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "🎬 *Your video is ready!*\n\n"
                        "⚠️ *MOCK MODE* ⚠️\n"
                        "The bot is currently in test mode.\n\n"
                        "*To get real videos:*\n"
                        "1. Wait for Seedance API launch (Feb 24)\n"
                        "2. Set `MOCK_MODE=false` in .env\n"
                        "3. Add your Seedance API key\n\n"
                        "*Your prompt was received and would generate:*\n"
                        f"📄 {open(video_path).read()[:500]}..."
                    ),
                    parse_mode="Markdown",
                )
                return

            # Send actual video
            video_file = open(video_path, "rb")
            await bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption="🎬 Your AI-generated video!",
            )
            video_file.close()
        except Exception as e:
            await bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Video generated but couldn't send: {e}",
            )

    def _validate_prompt(self, prompt: str) -> Optional[str]:
        """Validate the user's prompt."""
        if not prompt:
            return "Please enter a prompt describing your video."

        if len(prompt) < self.min_prompt_length:
            return (
                f"Prompt is too short ({len(prompt)} chars). "
                f"Please describe your video in at least {self.min_prompt_length} characters."
            )

        if len(prompt) > self.max_prompt_length:
            return (
                f"Prompt is too long ({len(prompt)} chars). "
                f"Please keep it under {self.max_prompt_length} characters."
            )

        # Check for empty or meaningless prompts
        if prompt.strip() in ["a", "i", "me", "test"]:
            return "Please provide a more detailed prompt."

        return None

    async def ask_for_prompt(
        self, update: Update, context: CallbackContext
    ) -> None:
        """Send prompt request with template suggestions."""
        templates_text = format_templates_list()

        response = (
            "✅ Photos saved! Now send me a prompt describing the video you want.\n\n"
            f"{templates_text}\n\n"
            "Or just describe your own idea!"
        )

        await update.message.reply_text(response, parse_mode="Markdown")

    async def show_templates(
        self, update: Update, context: CallbackContext
    ) -> None:
        """Show all available prompt templates."""
        templates_text = format_templates_list()
        await update.message.reply_text(
            templates_text, parse_mode="Markdown", disable_web_page_preview=True
        )
