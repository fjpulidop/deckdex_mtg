"""Catalog service: search, autocomplete, images, and sync management."""

import asyncio
import os
import sys
import threading
import time
import uuid
from typing import Callable, Dict, Any, List, Optional, Tuple

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger

from deckdex.catalog.repository import CatalogRepository
from deckdex.catalog.sync_job import CatalogSyncJob
from deckdex.storage.image_store import ImageStore

# In-memory lock: only one sync at a time
_sync_lock = threading.Lock()
_active_sync_job: Optional[CatalogSyncJob] = None


def search(catalog_repo: CatalogRepository, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search catalog cards by name (case-insensitive contains)."""
    return catalog_repo.search_by_name(query, limit=limit)


def autocomplete(catalog_repo: CatalogRepository, query: str, limit: int = 20) -> List[str]:
    """Return matching card names for autocomplete."""
    return catalog_repo.autocomplete(query, limit=limit)


def get_card(catalog_repo: CatalogRepository, scryfall_id: str) -> Optional[Dict[str, Any]]:
    """Return a single catalog card by scryfall_id."""
    return catalog_repo.get_by_scryfall_id(scryfall_id)


def get_image(image_store: ImageStore, scryfall_id: str) -> Optional[Tuple[bytes, str]]:
    """Return (image_bytes, content_type) from ImageStore, or None."""
    return image_store.get(scryfall_id)


def get_sync_status(catalog_repo: CatalogRepository) -> Dict[str, Any]:
    """Return the current catalog sync state."""
    return catalog_repo.get_sync_state()


def start_sync(
    catalog_repo: CatalogRepository,
    image_store: ImageStore,
    job_repo,
    bulk_data_url: str,
    image_size: str,
    on_progress=None,
    on_progress_async: Optional[Callable] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    active_jobs: Optional[Dict] = None,
    job_results: Optional[Dict] = None,
) -> str:
    """Launch a background catalog sync job.

    Returns the job_id.  Raises RuntimeError if a sync is already running.

    Args:
        on_progress: Synchronous callback (phase, current, total).
        on_progress_async: Async callback for WebSocket events.
        loop: Event loop for bridging sync→async.
        active_jobs: Dict to register/unregister the job for WebSocket validation.
        job_results: Dict to store final result for WebSocket reconnects.
    """
    global _active_sync_job

    if not _sync_lock.acquire(blocking=False):
        raise RuntimeError("A catalog sync is already running")

    job_id = str(uuid.uuid4())

    # Record in jobs table
    if job_repo:
        try:
            from sqlalchemy import text
            engine = job_repo._engine()
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO jobs (id, type, status) VALUES (:id, 'catalog_sync', 'running')
                    """),
                    {"id": job_id},
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to record sync job in jobs table: {e}")

    # Bridge sync on_progress(phase, current, total) → async WebSocket events
    def _sync_progress(phase: str, current: int, total: int):
        if on_progress:
            on_progress(phase, current, total)
        if on_progress_async and loop:
            pct = (current / total * 100) if total else 0
            asyncio.run_coroutine_threadsafe(
                on_progress_async({
                    "type": "progress",
                    "job_id": job_id,
                    "current": current,
                    "total": total,
                    "percentage": round(pct, 2),
                    "phase": phase,
                }),
                loop,
            )

    def _emit_complete(status: str, summary: dict):
        if on_progress_async and loop:
            asyncio.run_coroutine_threadsafe(
                on_progress_async({
                    "type": "complete",
                    "job_id": job_id,
                    "status": status,
                    "summary": summary,
                }),
                loop,
            )

    def _run():
        global _active_sync_job
        start_time = time.time()
        result_summary = {}
        final_status = "completed"
        try:
            sync = CatalogSyncJob(
                catalog_repo=catalog_repo,
                image_store=image_store,
                bulk_data_url=bulk_data_url,
                image_size=image_size,
                on_progress=_sync_progress,
            )
            _active_sync_job = sync
            sync.run()

            duration = time.time() - start_time
            state = catalog_repo.get_sync_state()
            result_summary = {
                "total_cards": state.get("total_cards", 0),
                "total_images_downloaded": state.get("total_images_downloaded", 0),
                "duration_seconds": round(duration, 1),
            }
            if job_repo:
                try:
                    from sqlalchemy import text
                    import json
                    engine = job_repo._engine()
                    with engine.connect() as conn:
                        conn.execute(
                            text("""
                                UPDATE jobs SET status = 'completed', completed_at = NOW(),
                                result = :result WHERE id = :id
                            """),
                            {"id": job_id, "result": json.dumps(result_summary)},
                        )
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to update job record: {e}")

        except Exception as e:
            logger.error(f"Catalog sync job {job_id} failed: {e}")
            final_status = "error"
            result_summary = {"error": str(e)[:500]}
            if job_repo:
                try:
                    from sqlalchemy import text
                    import json
                    engine = job_repo._engine()
                    with engine.connect() as conn:
                        conn.execute(
                            text("""
                                UPDATE jobs SET status = 'failed', completed_at = NOW(),
                                result = :result WHERE id = :id
                            """),
                            {"id": job_id, "result": json.dumps(result_summary)},
                        )
                        conn.commit()
                except Exception:
                    pass
        finally:
            _active_sync_job = None
            _sync_lock.release()
            # Emit WebSocket complete event
            _emit_complete(final_status, result_summary)
            # Move from active to results for WebSocket reconnect support
            if active_jobs is not None and job_id in active_jobs:
                del active_jobs[job_id]
            if job_results is not None:
                job_results[job_id] = {"status": final_status, **result_summary}

    thread = threading.Thread(target=_run, name=f"catalog-sync-{job_id}", daemon=True)
    thread.start()
    return job_id
