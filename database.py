"""
Database module for Telegram Video Bot.
Handles SQLite job tracking and state management.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional


class Database:
    """SQLite database manager for job tracking."""

    def __init__(self, db_path: Path = Path("./jobs.db")):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    photos TEXT,
                    prompt TEXT,
                    status TEXT DEFAULT 'pending',
                    seedance_job_id TEXT,
                    video_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id INTEGER PRIMARY KEY,
                    state TEXT DEFAULT 'idle',
                    photos TEXT,
                    current_prompt TEXT,
                    last_job_id INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Create indexes for faster queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)"
            )
            conn.commit()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # Job Management

    def create_job(
        self,
        user_id: int,
        chat_id: int,
        photos: List[str],
        prompt: str,
    ) -> int:
        """Create a new job and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO jobs (user_id, chat_id, photos, prompt, status)
                VALUES (?, ?, ?, ?, 'pending')
                """,
                (user_id, chat_id, json.dumps(photos), prompt),
            )
            job_id = cursor.lastrowid

            # Update user session
            conn.execute(
                """
                INSERT OR REPLACE INTO user_sessions
                (user_id, state, photos, current_prompt, last_job_id, updated_at)
                VALUES (?, 'generating', ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, json.dumps(photos), prompt, job_id),
            )

            return job_id

    def get_job(self, job_id: int) -> Optional[dict]:
        """Get job details by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE id = ?", (job_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_jobs(
        self, user_id: int, limit: int = 10
    ) -> List[dict]:
        """Get recent jobs for a user."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM jobs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def update_job_status(
        self,
        job_id: int,
        status: str,
        seedance_job_id: Optional[str] = None,
        video_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update job status."""
        with self._get_connection() as conn:
            if status == "completed":
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = ?,
                        seedance_job_id = ?,
                        video_path = ?,
                        completed_at = CURRENT_TIMESTAMP,
                        error_message = ?
                    WHERE id = ?
                    """,
                    (status, seedance_job_id, video_path, error_message, job_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = ?,
                        seedance_job_id = ?,
                        error_message = ?
                    WHERE id = ?
                    """,
                    (status, seedance_job_id, error_message, job_id),
                )

    def get_pending_jobs(self) -> List[dict]:
        """Get all pending jobs for processing."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = 'pending'"
            ).fetchall()
            return [dict(row) for row in rows]

    # Session Management

    def get_user_session(self, user_id: int) -> Optional[dict]:
        """Get user's current session state."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM user_sessions WHERE user_id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_user_state(
        self, user_id: int, state: str, **kwargs
    ) -> None:
        """Update user's session state."""
        with self._get_connection() as conn:
            session = conn.execute(
                "SELECT * FROM user_sessions WHERE user_id = ?", (user_id,)
            ).fetchone()

            if session:
                # Update existing session
                updates = ["state = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [state]

                if "photos" in kwargs:
                    updates.append("photos = ?")
                    params.append(json.dumps(kwargs["photos"]))

                if "current_prompt" in kwargs:
                    updates.append("current_prompt = ?")
                    params.append(kwargs["current_prompt"])

                if "last_job_id" in kwargs:
                    updates.append("last_job_id = ?")
                    params.append(kwargs["last_job_id"])

                params.append(user_id)
                conn.execute(
                    f"""
                    UPDATE user_sessions
                    SET {', '.join(updates)}
                    WHERE user_id = ?
                    """,
                    params,
                )
            else:
                # Create new session
                photos = json.dumps(kwargs.get("photos", []))
                prompt = kwargs.get("current_prompt", "")
                job_id = kwargs.get("last_job_id")
                conn.execute(
                    """
                    INSERT INTO user_sessions
                    (user_id, state, photos, current_prompt, last_job_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user_id, state, photos, prompt, job_id),
                )

    def clear_user_session(self, user_id: int) -> None:
        """Clear user's session state."""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM user_sessions WHERE user_id = ?", (user_id,)
            )

    def reset_user_generation_state(self, user_id: int) -> None:
        """Reset user state after successful generation."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE user_sessions
                SET state = 'idle',
                    photos = '[]',
                    current_prompt = '',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (user_id,),
            )
