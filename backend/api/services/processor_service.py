"""
ProcessorService - Wrapper around MagicCardProcessor for API usage

This service wraps the existing MagicCardProcessor to enable:
- Async execution in thread pool
- Progress callbacks for WebSocket updates via tqdm interception
- Job state management
"""
import os
import sys
import uuid
import asyncio
import threading
import io
import re
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from deckdex.magic_card_processor import MagicCardProcessor
from deckdex.config import ProcessorConfig
from deckdex.config_loader import load_config
from loguru import logger


class JobCancelledException(Exception):
    """Raised inside the processor thread when cancellation is requested."""
    pass


@dataclass
class JobMetadata:
    """Metadata for a processing job"""
    job_id: str
    start_time: datetime
    config: ProcessorConfig
    job_type: str  # 'process' or 'update_prices'
    status: str  # 'pending', 'running', 'complete', 'error', 'cancelled'
    progress: Dict[str, Any]
    error: Optional[str] = None


class ProgressCapture:
    """
    Captures tqdm progress output by intercepting stderr/stdout writes.
    
    MagicCardProcessor uses tqdm which writes to stderr. We intercept those
    writes to extract current/total progress and emit WebSocket events.
    
    Also serves as the cancellation mechanism: when the cancel_event is set,
    the next write() call raises JobCancelledException, which propagates up
    through tqdm.update() → the processor loop → aborting the job.
    """
    
    def __init__(self, original_stream, callback, cancel_event: Optional[threading.Event] = None):
        self.original = original_stream
        self.callback = callback
        self.cancel_event = cancel_event
        self._buffer = ''
        # Match tqdm patterns like "  45%|███    | 450/1000 [00:30<00:35]"
        self._tqdm_pattern = re.compile(r'(\d+)%\|.*?\|\s*(\d+)/(\d+)')
    
    def write(self, text):
        # Check for cancellation on every write — this is the injection point
        # that aborts the processor from within its own thread
        if self.cancel_event and self.cancel_event.is_set():
            raise JobCancelledException("Job cancelled by user")
        
        self.original.write(text)
        self._buffer += text
        
        # Try to extract tqdm progress
        match = self._tqdm_pattern.search(self._buffer)
        if match:
            percentage = int(match.group(1))
            current = int(match.group(2))
            total = int(match.group(3))
            self.callback(current, total, float(percentage))
            self._buffer = ''
        
        # Also check for "Cards not found:" messages for error tracking
        if 'Cards not found:' in text or 'not found' in text.lower():
            # Don't clear buffer for these
            pass
        
        # Keep buffer manageable
        if len(self._buffer) > 4096:
            self._buffer = self._buffer[-1024:]
    
    def flush(self):
        if self.cancel_event and self.cancel_event.is_set():
            raise JobCancelledException("Job cancelled by user")
        self.original.flush()
    
    # Forward all other attributes to original stream
    def __getattr__(self, name):
        return getattr(self.original, name)


class ProcessorService:
    """
    Wrapper service around MagicCardProcessor for API usage.
    
    Provides async execution with progress callbacks without modifying
    the core processor logic. Intercepts tqdm output to emit progress events.
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None, progress_callback: Optional[Callable] = None, job_repo=None, user_id: Optional[int] = None):
        self.config = config or load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
        self.progress_callback = progress_callback
        self._job_repo = job_repo  # Optional[JobRepository]
        self._user_id = user_id
        self._lock = threading.Lock()
        self._cancel_flag = threading.Event()

        # Job metadata
        self.job_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.status = 'pending'
        self.progress_data = {
            'current': 0,
            'total': 0,
            'percentage': 0.0,
            'errors': []
        }

        # Event loop reference for cross-thread callback
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        logger.info(f"ProcessorService initialized with job_id={self.job_id}")
    
    def get_metadata(self) -> JobMetadata:
        """Get current job metadata"""
        with self._lock:
            return JobMetadata(
                job_id=self.job_id,
                start_time=self.start_time,
                config=self.config,
                job_type='unknown',
                status=self.status,
                progress=self.progress_data.copy()
            )
    
    def _persist_job_start(self, job_type: str) -> None:
        """Write job row to Postgres (no-op when job_repo is None)."""
        if self._job_repo is not None:
            try:
                self._job_repo.create_job(self._user_id, job_type, job_id=self.job_id)
            except Exception as e:
                logger.warning(f"Failed to persist job start: {e}")

    def _persist_job_end(self, status: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Update job row in Postgres (no-op when job_repo is None)."""
        if self._job_repo is not None:
            try:
                self._job_repo.update_job_status(self.job_id, status, result=result)
            except Exception as e:
                logger.warning(f"Failed to persist job end: {e}")

    async def _emit_progress(self, event_type: str, data: Dict[str, Any]):
        """Emit progress event to callback if provided."""
        if self.progress_callback:
            try:
                await self.progress_callback({
                    'type': event_type,
                    'job_id': self.job_id,
                    'timestamp': datetime.now().isoformat(),
                    **data
                })
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def _on_tqdm_progress(self, current: int, total: int, percentage: float):
        """Called from tqdm capture thread when progress updates."""
        # Skip if cancelled
        if self._cancel_flag.is_set():
            return
        
        with self._lock:
            self.progress_data['current'] = current
            self.progress_data['total'] = total
            self.progress_data['percentage'] = percentage
        
        # Schedule async callback on the event loop
        if self._loop and self.progress_callback:
            asyncio.run_coroutine_threadsafe(
                self._emit_progress('progress', {
                    'current': current,
                    'total': total,
                    'percentage': percentage,
                }),
                self._loop
            )
    
    def _add_error(self, card_name: str, error_message: str):
        """Add error to progress data thread-safely."""
        with self._lock:
            self.progress_data['errors'].append({
                'card_name': card_name,
                'message': error_message,
                'timestamp': datetime.now().isoformat()
            })
    
    async def process_cards_async(self, limit: Optional[int] = None):
        """Process cards asynchronously with real-time progress tracking."""
        logger.info(f"Starting async card processing (job_id={self.job_id}, limit={limit})")
        self._persist_job_start('process')

        # Capture event loop for cross-thread progress callbacks
        self._loop = asyncio.get_event_loop()

        with self._lock:
            self.status = 'running'
        
        try:
            processor = MagicCardProcessor(self.config)
            executor = ThreadPoolExecutor(max_workers=1)
            
            def run_processor():
                """Run processor in thread with tqdm interception and cancellation support."""
                original_stderr = sys.stderr
                original_stdout = sys.stdout
                capture_err = ProgressCapture(original_stderr, self._on_tqdm_progress, self._cancel_flag)
                capture_out = ProgressCapture(original_stdout, self._on_tqdm_progress, self._cancel_flag)
                
                try:
                    sys.stderr = capture_err
                    sys.stdout = capture_out
                    processor.process_card_data()
                    return {
                        'status': 'success',
                        'error_count': processor.error_count,
                        'not_found_cards': processor.not_found_cards[:20],
                    }
                except JobCancelledException:
                    logger.info(f"Process cards job cancelled (job_id={self.job_id})")
                    return {
                        'status': 'cancelled',
                        'message': 'Job cancelled by user',
                        'error_count': getattr(processor, 'error_count', 0),
                        'not_found_cards': getattr(processor, 'not_found_cards', [])[:20],
                    }
                except Exception as e:
                    logger.error(f"Processor error: {e}")
                    return {'status': 'error', 'error': str(e)}
                finally:
                    sys.stderr = original_stderr
                    sys.stdout = original_stdout
            
            result = await self._loop.run_in_executor(executor, run_processor)
            
            with self._lock:
                if result.get('status') == 'cancelled':
                    self.status = 'cancelled'
                elif result.get('status') == 'success':
                    self.status = 'complete'
                else:
                    self.status = 'error'
            
            self._persist_job_end(self.status, result)
            # Only emit complete if not already emitted by cancel_async
            if not self._cancel_flag.is_set():
                await self._emit_progress('complete', {
                    'status': self.status,
                    'summary': result
                })

            logger.info(f"Card processing finished (job_id={self.job_id}, status={self.status})")
            return result

        except Exception as e:
            logger.error(f"Error in process_cards_async: {e}")
            with self._lock:
                self.status = 'error'
            self._persist_job_end('error', {'status': 'error', 'error': str(e)})
            await self._emit_progress('complete', {
                'status': 'error',
                'summary': {'status': 'error', 'error': str(e)}
            })
            raise


    async def update_prices_async(self):
        """Update prices asynchronously with real-time progress tracking."""
        logger.info(f"Starting async price update (job_id={self.job_id})")
        self._persist_job_start('update_prices')

        # Capture event loop for cross-thread progress callbacks
        self._loop = asyncio.get_event_loop()

        with self._lock:
            self.status = 'running'
        
        try:
            processor = MagicCardProcessor(self.config)
            executor = ThreadPoolExecutor(max_workers=1)
            
            def run_update():
                """Run price update in thread with tqdm interception and cancellation support."""
                original_stderr = sys.stderr
                original_stdout = sys.stdout
                capture_err = ProgressCapture(original_stderr, self._on_tqdm_progress, self._cancel_flag)
                capture_out = ProgressCapture(original_stdout, self._on_tqdm_progress, self._cancel_flag)
                
                try:
                    sys.stderr = capture_err
                    sys.stdout = capture_out
                    processor.process_card_data()
                    return {
                        'status': 'success',
                        'error_count': processor.error_count,
                        'not_found_cards': processor.not_found_cards[:20],
                    }
                except JobCancelledException:
                    logger.info(f"Price update job cancelled (job_id={self.job_id})")
                    return {
                        'status': 'cancelled',
                        'message': 'Job cancelled by user',
                        'error_count': getattr(processor, 'error_count', 0),
                        'not_found_cards': getattr(processor, 'not_found_cards', [])[:20],
                    }
                except Exception as e:
                    logger.error(f"Price update error: {e}")
                    return {'status': 'error', 'error': str(e)}
                finally:
                    sys.stderr = original_stderr
                    sys.stdout = original_stdout
            
            result = await self._loop.run_in_executor(executor, run_update)
            
            with self._lock:
                if result.get('status') == 'cancelled':
                    self.status = 'cancelled'
                elif result.get('status') == 'success':
                    self.status = 'complete'
                else:
                    self.status = 'error'
            
            self._persist_job_end(self.status, result)
            # Only emit complete if not already emitted by cancel_async
            if not self._cancel_flag.is_set():
                await self._emit_progress('complete', {
                    'status': self.status,
                    'summary': result
                })

            logger.info(f"Price update finished (job_id={self.job_id}, status={self.status})")
            return result

        except Exception as e:
            logger.error(f"Error in update_prices_async: {e}")
            with self._lock:
                self.status = 'error'
            self._persist_job_end('error', {'status': 'error', 'error': str(e)})
            await self._emit_progress('complete', {
                'status': 'error',
                'summary': {'status': 'error', 'error': str(e)}
            })
            raise

    async def update_single_card_price_async(self, card_id: int):
        """Update price for one card asynchronously with same progress/WebSocket pattern as bulk update."""
        logger.info(f"Starting async single-card price update (job_id={self.job_id}, card_id={card_id})")
        self._loop = asyncio.get_event_loop()
        with self._lock:
            self.status = 'running'
        try:
            processor = MagicCardProcessor(self.config)
            executor = ThreadPoolExecutor(max_workers=1)

            def run_update():
                original_stderr = sys.stderr
                original_stdout = sys.stdout
                capture_err = ProgressCapture(original_stderr, self._on_tqdm_progress, self._cancel_flag)
                capture_out = ProgressCapture(original_stdout, self._on_tqdm_progress, self._cancel_flag)
                try:
                    sys.stderr = capture_err
                    sys.stdout = capture_out
                    processor.update_prices_for_card_ids([card_id])
                    return {
                        'status': 'success',
                        'error_count': processor.error_count,
                        'not_found_cards': processor.not_found_cards[:20],
                    }
                except JobCancelledException:
                    logger.info(f"Single-card price update job cancelled (job_id={self.job_id})")
                    return {
                        'status': 'cancelled',
                        'message': 'Job cancelled by user',
                        'error_count': getattr(processor, 'error_count', 0),
                        'not_found_cards': getattr(processor, 'not_found_cards', [])[:20],
                    }
                except Exception as e:
                    logger.error(f"Single-card price update error: {e}")
                    return {'status': 'error', 'error': str(e)}
                finally:
                    sys.stderr = original_stderr
                    sys.stdout = original_stdout

            result = await self._loop.run_in_executor(executor, run_update)
            with self._lock:
                if result.get('status') == 'cancelled':
                    self.status = 'cancelled'
                elif result.get('status') == 'success':
                    self.status = 'complete'
                else:
                    self.status = 'error'
            if not self._cancel_flag.is_set():
                await self._emit_progress('complete', {'status': self.status, 'summary': result})
            logger.info(f"Single-card price update finished (job_id={self.job_id}, status={self.status})")
            return result
        except Exception as e:
            logger.error(f"Error in update_single_card_price_async: {e}")
            with self._lock:
                self.status = 'error'
            await self._emit_progress('complete', {
                'status': 'error',
                'summary': {'status': 'error', 'error': str(e)}
            })
            raise

    def cancel(self):
        """Request cancellation of current process (sync, no WebSocket event)."""
        logger.info(f"Cancellation requested for job_id={self.job_id}")
        self._cancel_flag.set()
        with self._lock:
            self.status = 'cancelled'
    
    async def cancel_async(self):
        """
        Request cancellation and emit WebSocket complete event.
        
        The underlying processor thread may continue running until its
        current operation finishes, but the job is marked cancelled and
        no further progress events will be emitted to WebSocket clients.
        """
        logger.info(f"Async cancellation requested for job_id={self.job_id}")
        self._cancel_flag.set()
        with self._lock:
            self.status = 'cancelled'
        
        await self._emit_progress('complete', {
            'status': 'cancelled',
            'summary': {'status': 'cancelled', 'message': 'Job cancelled by user'}
        })
