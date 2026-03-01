"""
Process execution API routes
Endpoints for triggering and monitoring background processes
"""
import os
import uuid
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from pydantic import BaseModel
from loguru import logger

from ..services.processor_service import ProcessorService
from ..dependencies import clear_collection_cache, get_collection_repo, get_current_user_id, get_job_repo
from ..routes.stats import clear_stats_cache
from ..websockets.progress import manager as ws_manager
from ..main import limiter

router = APIRouter(prefix="/api", tags=["process"])

# In-memory job storage (MVP - will be lost on restart)
_active_jobs: Dict[str, ProcessorService] = {}
_job_results: Dict[str, dict] = {}
_job_types: Dict[str, str] = {}  # job_id -> job_type


class JobResponse(BaseModel):
    """Response model for job creation"""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Job status model"""
    job_id: str
    status: str
    progress: dict
    start_time: str
    job_type: str


class JobListItem(BaseModel):
    """Item in jobs list"""
    job_id: str
    status: str
    job_type: str
    progress: dict
    start_time: str


class ProcessRequest(BaseModel):
    """Body for POST /process"""
    limit: Optional[int] = None
    scope: Optional[str] = "all"  # "all" | "new_only"


@router.get("/jobs", response_model=List[JobListItem])
async def list_jobs(user_id: int = Depends(get_current_user_id)):
    """
    List all active and recently completed jobs.

    Returns list of jobs with their current status and progress.
    Includes in-memory jobs (process/price) and DB-persisted running jobs (imports).
    """
    jobs = []
    in_memory_ids: set = set()

    # Active jobs (in-memory)
    for job_id, service in _active_jobs.items():
        in_memory_ids.add(job_id)
        metadata = service.get_metadata()
        jobs.append(JobListItem(
            job_id=job_id,
            status=metadata.status,
            job_type=_job_types.get(job_id, 'unknown'),
            progress=metadata.progress,
            start_time=metadata.start_time.isoformat(),
        ))

    # Recently completed jobs (in-memory)
    for job_id, result in _job_results.items():
        in_memory_ids.add(job_id)
        if job_id not in _active_jobs:
            jobs.append(JobListItem(
                job_id=job_id,
                status=result.get('status', 'complete'),
                job_type=_job_types.get(job_id, 'unknown'),
                progress={'summary': result},
                start_time='',
            ))

    # Running/pending jobs from Postgres not yet in memory (e.g. import jobs after page refresh)
    job_repo = get_job_repo()
    if job_repo:
        try:
            db_jobs = job_repo.get_job_history(user_id, limit=20)
            for db_job in db_jobs:
                jid = str(db_job.get('id', ''))
                if jid and jid not in in_memory_ids and db_job.get('status') in ('running', 'pending'):
                    jobs.append(JobListItem(
                        job_id=jid,
                        status=db_job['status'],
                        job_type=db_job.get('type', 'unknown'),
                        progress={},
                        start_time=str(db_job.get('created_at') or ''),
                    ))
        except Exception:
            pass

    return jobs


@router.post("/process", response_model=JobResponse)
@limiter.limit("5/minute")
async def trigger_process(
    request: Request,
    background_tasks: BackgroundTasks,
    body: Optional[ProcessRequest] = None,
    user_id: int = Depends(get_current_user_id)
):
    """
    Trigger card processing job.
    Body: { "limit": optional number, "scope": "all" | "new_only" }.
    scope=new_only: only cards that have just the name (no type_line). scope=all: all cards.
    Only one full process job can run at a time; update_prices can run in parallel.
    """
    req = body or ProcessRequest()
    limit = req.limit
    scope = (req.scope or "all").strip().lower() if req.scope else "all"
    if scope not in ("all", "new_only"):
        scope = "all"
    logger.info(f"POST /api/process - limit={limit}, scope={scope}, user={user_id}")
    
    # Check if another job of the same type is already running
    for job_id, service in _active_jobs.items():
        if service.status == 'running' and _job_types.get(job_id) == 'process':
            logger.warning(f"Process job already running: {job_id}")
            raise HTTPException(
                status_code=409,
                detail=f"Another process (full) job is already running (job_id: {job_id})"
            )
    
    # Clean up old completed jobs
    _cleanup_old_jobs()
    
    # Build config with process_scope so processor runs only new/incomplete cards when requested
    from deckdex.config_loader import load_config
    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
    config.process_scope = scope
    
    # Create new processor service with config
    service = ProcessorService(config=config, job_repo=get_job_repo(), user_id=user_id)
    job_id = service.job_id
    _job_types[job_id] = 'process'
    
    # Set up WebSocket callback
    async def progress_callback(event):
        event_type = event.get('type')
        if event_type == 'progress':
            await ws_manager.send_progress(
                job_id,
                event.get('current', 0),
                event.get('total', 0),
                event.get('percentage', 0.0)
            )
        elif event_type == 'error':
            await ws_manager.send_error(
                job_id,
                event.get('card_name', ''),
                event.get('error_type', 'unknown'),
                event.get('message', '')
            )
        elif event_type == 'complete':
            await ws_manager.send_complete(
                job_id,
                event.get('status', 'unknown'),
                event.get('summary', {})
            )
    
    service.progress_callback = progress_callback
    _active_jobs[job_id] = service
    
    async def run_process():
        try:
            result = await service.process_cards_async(limit=limit)
            _job_results[job_id] = result
            if result.get('status') == 'success':
                clear_collection_cache()
                clear_stats_cache()
        except Exception as e:
            logger.error(f"Process job {job_id} failed: {e}")
            _job_results[job_id] = {'status': 'error', 'error': 'Job failed'}
        # Note: do NOT delete from _active_jobs here.
        # Let it remain so the frontend can poll final status.
        # It will be cleaned up on next job creation.
    
    background_tasks.add_task(run_process)
    
    logger.info(f"Created process job: {job_id}")
    return JobResponse(
        job_id=job_id,
        status='pending',
        message='Process job created and queued'
    )


@router.post("/prices/update", response_model=JobResponse)
@limiter.limit("5/minute")
async def trigger_price_update(request: Request, background_tasks: BackgroundTasks, user_id: int = Depends(get_current_user_id)):
    """
    Trigger price update job.
    Only one update_prices job at a time; full process can run in parallel.
    """
    logger.info("POST /api/prices/update")
    
    # Check if another update_prices job is already running
    for job_id, service in _active_jobs.items():
        if service.status == 'running' and _job_types.get(job_id) == 'update_prices':
            logger.warning(f"Price update job already running: {job_id}")
            raise HTTPException(
                status_code=409,
                detail=f"Another price update job is already running (job_id: {job_id})"
            )
    
    # Clean up old completed jobs
    _cleanup_old_jobs()
    
    # Create processor with update_prices mode
    from deckdex.config_loader import load_config
    config = load_config(profile="default")
    config.update_prices = True
    
    service = ProcessorService(config=config, job_repo=get_job_repo(), user_id=user_id)
    job_id = service.job_id
    _job_types[job_id] = 'update_prices'
    
    # Set up WebSocket callback
    async def progress_callback(event):
        event_type = event.get('type')
        if event_type == 'progress':
            await ws_manager.send_progress(
                job_id,
                event.get('current', 0),
                event.get('total', 0),
                event.get('percentage', 0.0)
            )
        elif event_type == 'error':
            await ws_manager.send_error(
                job_id,
                event.get('card_name', ''),
                event.get('error_type', 'unknown'),
                event.get('message', '')
            )
        elif event_type == 'complete':
            await ws_manager.send_complete(
                job_id,
                event.get('status', 'unknown'),
                event.get('summary', {})
            )
    
    service.progress_callback = progress_callback
    _active_jobs[job_id] = service
    
    async def run_update():
        try:
            result = await service.update_prices_async()
            _job_results[job_id] = result
            if result.get('status') == 'success':
                clear_collection_cache()
                clear_stats_cache()
        except Exception as e:
            logger.error(f"Price update job {job_id} failed: {e}")
            _job_results[job_id] = {'status': 'error', 'error': 'Job failed'}
    
    background_tasks.add_task(run_update)
    
    logger.info(f"Created price update job: {job_id}")
    return JobResponse(
        job_id=job_id,
        status='pending',
        message='Price update job created and queued'
    )


@router.post("/prices/update/{card_id}", response_model=JobResponse)
async def trigger_single_card_price_update(
    card_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
):
    """
    Trigger price update for a single card by id. Returns job_id; job uses same WebSocket progress
    as bulk update. Does not conflict with bulk POST /api/prices/update (no 409).
    """
    logger.info(f"POST /api/prices/update/{card_id} - user={user_id}")
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(status_code=501, detail="Collection repository not configured")
    card = repo.get_card_by_id(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Card with id {card_id} not found")
    _cleanup_old_jobs()
    from deckdex.config_loader import load_config
    config = load_config(profile="default")
    config.update_prices = True
    service = ProcessorService(config=config, job_repo=get_job_repo(), user_id=user_id)
    job_id = service.job_id
    _job_types[job_id] = "Update price"

    async def progress_callback(event):
        event_type = event.get("type")
        if event_type == "progress":
            await ws_manager.send_progress(
                job_id,
                event.get("current", 0),
                event.get("total", 0),
                event.get("percentage", 0.0),
            )
        elif event_type == "error":
            await ws_manager.send_error(
                job_id,
                event.get("card_name", ""),
                event.get("error_type", "unknown"),
                event.get("message", ""),
            )
        elif event_type == "complete":
            await ws_manager.send_complete(
                job_id,
                event.get("status", "unknown"),
                event.get("summary", {}),
            )

    service.progress_callback = progress_callback
    _active_jobs[job_id] = service

    async def run_update():
        try:
            result = await service.update_single_card_price_async(card_id)
            _job_results[job_id] = result
            if result.get("status") == "success":
                clear_collection_cache()
                clear_stats_cache()
        except Exception as e:
            logger.error(f"Single-card price update job {job_id} failed: {e}")
            _job_results[job_id] = {"status": "error", "error": "Job failed"}

    background_tasks.add_task(run_update)
    logger.info(f"Created single-card price update job: {job_id}")
    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Price update job created and queued",
    )


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, user_id: int = Depends(get_current_user_id)):
    """Get status of a specific job."""
    logger.debug(f"GET /api/jobs/{job_id} - user={user_id}")
    
    # Check active jobs
    if job_id in _active_jobs:
        service = _active_jobs[job_id]
        metadata = service.get_metadata()
        return JobStatus(
            job_id=job_id,
            status=metadata.status,
            progress=metadata.progress,
            start_time=metadata.start_time.isoformat(),
            job_type=_job_types.get(job_id, 'unknown')
        )
    
    # Check completed jobs
    if job_id in _job_results:
        result = _job_results[job_id]
        return JobStatus(
            job_id=job_id,
            status=result.get('status', 'complete'),
            progress={'summary': result},
            start_time='',
            job_type=_job_types.get(job_id, 'unknown')
        )
    
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, user_id: int = Depends(get_current_user_id)):
    """
    Cancel a running job.

    Sets the cancel flag and emits a WebSocket complete event.
    Note: the underlying processor thread may continue until it finishes
    its current operation, but the job will be marked as cancelled and
    no further progress events will be emitted.
    """
    logger.info(f"POST /api/jobs/{job_id}/cancel - user={user_id}")
    
    if job_id not in _active_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or already finished")
    
    service = _active_jobs[job_id]
    
    if service.status != 'running':
        raise HTTPException(status_code=409, detail=f"Job is not running (status: {service.status})")
    
    # Cancel the service and emit WebSocket event
    await service.cancel_async()
    
    # Store result
    _job_results[job_id] = {'status': 'cancelled', 'message': 'Job cancelled by user'}
    
    return {"job_id": job_id, "status": "cancelled", "message": "Job cancellation requested"}


@router.get("/jobs/history")
async def get_job_history(
    limit: int = 50,
    user_id: int = Depends(get_current_user_id),
):
    """Return persisted job history for the authenticated user (requires Postgres)."""
    job_repo = get_job_repo()
    if job_repo is None:
        return []
    return job_repo.get_job_history(user_id, limit=min(limit, 100))


def _cleanup_old_jobs():
    """Remove old completed jobs to prevent memory leaks."""
    completed_ids = [
        jid for jid, svc in _active_jobs.items()
        if svc.status in ('complete', 'error', 'cancelled')
    ]
    for jid in completed_ids:
        del _active_jobs[jid]
    
    # Keep only last 10 results
    if len(_job_results) > 10:
        old_keys = list(_job_results.keys())[:-10]
        for key in old_keys:
            del _job_results[key]
            _job_types.pop(key, None)
