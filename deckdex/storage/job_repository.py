"""JobRepository: persist job state to Postgres jobs table."""

import json
from typing import Any, Dict, List, Optional

from loguru import logger


class JobRepository:
    """Persists job lifecycle state (create / update / history) to the jobs table."""

    def __init__(self, database_url: str, engine=None):
        if engine is None and (not database_url or not database_url.strip().startswith("postgresql")):
            raise ValueError("database_url must be a non-empty postgresql:// URL")
        self._url = database_url
        self._eng = engine

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
                        VALUES (CAST(:id AS uuid), :user_id, :type, 'running')
                        ON CONFLICT (id) DO NOTHING
                        RETURNING id
                    """),
                    {"id": job_id, "user_id": user_id, "type": job_type},
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
                    {"user_id": user_id, "type": job_type},
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
                        result = COALESCE(CAST(:result AS jsonb), result)
                    WHERE id = CAST(:id AS uuid)
                """),
                {
                    "id": job_id,
                    "status": status,
                    "result": json.dumps(result) if result is not None else None,
                },
            )
            conn.commit()
        logger.debug(f"Job {job_id} updated: status={status}")

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Return a single job row by UUID, or None if not found."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            row = (
                conn.execute(
                    text("""
                        SELECT id, user_id, type, status, created_at, completed_at, result
                        FROM jobs
                        WHERE id = CAST(:id AS uuid)
                    """),
                    {"id": job_id},
                )
                .mappings()
                .fetchone()
            )
        if row is None:
            return None
        return {
            "job_id": str(row["id"]),
            "user_id": row["user_id"],
            "type": row["type"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
            "result": row["result"],
        }

    def mark_orphans_as_error(self, message: str = "Server restarted while job was running") -> int:
        """Mark all running jobs as error. Returns count of affected rows."""
        from sqlalchemy import text

        engine = self._get_engine()
        result_payload = json.dumps({"error": message})
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    UPDATE jobs
                    SET status = 'error',
                        completed_at = NOW() AT TIME ZONE 'utc',
                        result = CAST(:result AS jsonb)
                    WHERE status = 'running'
                """),
                {"result": result_payload},
            )
            conn.commit()
        return result.rowcount

    def get_job_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent jobs for a user, ordered by created_at DESC."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            rows = (
                conn.execute(
                    text("""
                    SELECT id, type, status, created_at, completed_at, result
                    FROM jobs
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                    {"user_id": user_id, "limit": limit},
                )
                .mappings()
                .fetchall()
            )
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
