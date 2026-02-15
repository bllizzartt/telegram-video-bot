"""
Seedance API Client for AI Video Generation.
Handles BytePlus API integration with mock mode for testing.
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from config import get_config


class JobStatus(Enum):
    """Video generation job status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VideoGenerationRequest:
    """Request for video generation."""

    prompt: str
    images: List[Path]
    resolution: str = "1080p"
    duration: Optional[int] = None  # seconds
    seed: Optional[int] = None


@dataclass
class VideoGenerationResponse:
    """Response from video generation API."""

    job_id: str
    status: JobStatus
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    progress: Optional[int] = None  # 0-100


class SeedanceClient:
    """Client for Seedance (BytePlus) API."""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.api_url = self.config.seedance_api_url
        self.api_key = self.config.seedance_api_key
        self.mock_mode = self.config.mock_mode
        self.video_storage_path = self.config.video_storage_path

        # Ensure storage directory exists
        self.video_storage_path.mkdir(parents=True, exist_ok=True)

    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResponse:
        """
        Generate a video from images using the Seedance API.

        Args:
            request: Video generation request with prompt and images

        Returns:
            VideoGenerationResponse with job ID and status
        """
        if self.mock_mode:
            return await self._mock_generate(request)

        return await self._real_generate(request)

    async def _mock_generate(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResponse:
        """
        Mock video generation for testing.
        Simulates API behavior without actual video generation.
        """
        import uuid

        job_id = f"mock_{uuid.uuid4().hex[:16]}"

        # Simulate async processing
        async def mock_process():
            # Simulate processing time (30 seconds)
            await asyncio.sleep(30)
            return VideoGenerationResponse(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                video_url=None,
                progress=100,
            )

        # In mock mode, we return a placeholder video
        # For testing, we'll create a dummy file
        await asyncio.sleep(1)  # Quick response for mock

        # Create a placeholder "video" file (use .mock extension to indicate mock mode)
        placeholder_path = self.video_storage_path / f"{job_id}.mock"
        placeholder_path.write_text(
            f"""MOCK VIDEO PLACEHOLDER
====================
Job ID: {job_id}
Prompt: {request.prompt}
Images: {len(request.images)}
Status: ready (mock mode)

To enable real video generation:
1. Set MOCK_MODE=false in .env
2. Add your Seedance API key
3. Wait until Feb 24 for API access

This placeholder represents where the generated video would be stored.
"""
        )

        return VideoGenerationResponse(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            video_url=str(placeholder_path),
            progress=100,
        )

    async def _real_generate(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResponse:
        """
        Real video generation via BytePlus API.
        Implements the actual Seedance API integration.
        """
        async with aiohttp.ClientSession() as session:
            # Prepare images for upload
            image_files = []
            for img_path in request.images:
                if img_path.exists():
                    image_files.append(
                        ("images", open(img_path, "rb"))
                    )

            # Build request payload
            payload = {
                "prompt": request.prompt,
                "resolution": request.resolution,
                "character_consistency": len(request.images) > 1,
            }

            if request.duration:
                payload["duration"] = request.duration

            if request.seed is not None:
                payload["seed"] = request.seed

            # Submit generation job
            async with session.post(
                f"{self.api_url}/generate",
                data={**payload, "images": image_files},
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    return VideoGenerationResponse(
                        job_id="",
                        status=JobStatus.FAILED,
                        error_message=f"API error: {error}",
                    )

                result = await response.json()
                job_id = result.get("job_id")

            # Poll for completion
            max_attempts = 60  # 5 minutes max
            attempt = 0

            while attempt < max_attempts:
                async with session.get(
                    f"{self.api_url}/jobs/{job_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                ) as status_response:
                    if status_response.status == 200:
                        status_data = await status_response.json()
                        status = JobStatus(status_data.get("status", "pending"))
                        progress = status_data.get("progress", 0)

                        if status == JobStatus.COMPLETED:
                            video_url = status_data.get("video_url")

                            # Download video
                            async with session.get(
                                video_url
                            ) as video_response:
                                if video_response.status == 200:
                                    video_path = (
                                        self.video_storage_path
                                        / f"{job_id}.mp4"
                                    )
                                    with open(video_path, "wb") as f:
                                        async for chunk in (
                                            video_response.content.iter_chunked(
                                                8192
                                            )
                                        ):
                                            f.write(chunk)

                                    return VideoGenerationResponse(
                                        job_id=job_id,
                                        status=status,
                                        video_url=str(video_path),
                                        progress=progress,
                                    )

                                return VideoGenerationResponse(
                                    job_id=job_id,
                                    status=status,
                                    error_message="Failed to download video",
                                )

                        elif status == JobStatus.FAILED:
                            return VideoGenerationResponse(
                                job_id=job_id,
                                status=status,
                                error_message=status_data.get(
                                    "error", "Unknown error"
                                ),
                            )

                    await asyncio.sleep(5)
                    attempt += 1

            return VideoGenerationResponse(
                job_id=job_id,
                status=JobStatus.FAILED,
                error_message="Timeout waiting for generation",
            )

    async def get_job_status(
        self, job_id: str
    ) -> VideoGenerationResponse:
        """Get the status of a generation job."""
        if self.mock_mode:
            return VideoGenerationResponse(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                progress=100,
            )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/jobs/{job_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as response:
                if response.status != 200:
                    return VideoGenerationResponse(
                        job_id=job_id,
                        status=JobStatus.FAILED,
                        error_message=f"API error: {response.status}",
                    )

                data = await response.json()
                return VideoGenerationResponse(
                    job_id=job_id,
                    status=JobStatus(data.get("status", "pending")),
                    progress=data.get("progress", 0),
                    video_url=data.get("video_url"),
                    error_message=data.get("error"),
                )

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or processing job."""
        if self.mock_mode:
            return True

        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.api_url}/jobs/{job_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as response:
                return response.status == 200


# Convenience function
async def generate_video(
    prompt: str,
    images: List[Path],
    resolution: str = "1080p",
) -> VideoGenerationResponse:
    """Generate a video from images."""
    client = SeedanceClient()
    request = VideoGenerationRequest(
        prompt=prompt,
        images=images,
        resolution=resolution,
    )
    return await client.generate_video(request)
