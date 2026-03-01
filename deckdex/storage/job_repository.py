"""JobRepository: persist job state to Postgres jobs table."""

import json
import os
from typing import Any, Dict, List, Optional

from loguru import logger


class JobRepository:
    """Persists job lifecycle state (create / update / history) to the jobs table."""

    def __init__(self, database_url: str):
        if not database_url or not database_url.strip().startswith("postgresql"):
            raise ValueError("database_url must be a non-empty postgresql:// URL")
        self._url = database_url
        self._eng = None

    def _get_engine(self):
        from sqlalchemy import create_engine
        if self._eng is None:
            self._eng = create_engine(self._url, pool_pre_ping=True)
        return self._eng

    def create_job(self, user_id: Optional[int], job_type: str, job_id: Optional[str] = None) -> str:
        """Insert a new job row with status='running'. Returns the job UUID."""
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            if job_id:
                result = conn.execute(
                    text("""
                        INSERT INTO jobs (id, user_id, type, status)
                        VALUES (:id::uuid, :user_id, :type, 'running')
                        ON CONFLICT (id) DO NOTHING
                        RETURNING id
                    """),
                    {"id": job_id, "user_id": user_id, "type": job_type}
                ).fetchone()
                conn.commit()
                return job_id
            else:
                result = conn.execute(
                    text("""
                        INSERT INTO jobs (user_id, type, status)
                        VALUES (:user_id, :type, 'running')
                        RETURNING id
                    """),
                    {"user_id": user_id, "type": job_type}
                ).fetchone()
                conn.commit()
                return str(result[0])

    def update_job_status(self, job_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Update job status and optionally set completed_at + result JSONB."""
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE jobs
                    SET status = :status,
                        completed_at = CASE WHEN :status IN ('complete', 'error', 'cancelled')
                                            THEN NOW() AT TIME ZONE 'utc'
                                            ELSE completed_at END,
                        result = COALESCE(:result::jsonb, result)
                    WHERE id = :id::uuid
                """),
                {
                    "id": job_id,
                    "status": status,
                    "result": json.dumps(result) if result is not None else None,
                }
            )
            conn.commit()
        logger.debug(f"Job {job_id} updated: status={status}")

    def get_job_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent jobs for a user, ordered by created_at DESC."""
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT id, type, status, created_at, completed_at, result
                    FROM jobs
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"user_id": user_id, "limit": limit}
            ).mappings().fetchall()
        return [
            {
                "job_id": str(r["id"]),
                "type": r["type"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None,
                "result": r["result"],
            }
            for r in rows
        ]
