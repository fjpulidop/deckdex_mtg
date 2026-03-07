"""
Tests for fix-job-persistence: JobRepository new methods, GET /api/jobs/{job_id} DB
fallback, route ordering, catalog_service refactor, and ProcessorService persist calls.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id, get_job_repo
from backend.api.main import app

# ---------------------------------------------------------------------------
# Task 9.1 — JobRepository.get_job
# ---------------------------------------------------------------------------


class TestJobRepositoryGetJob(unittest.TestCase):
    """Unit tests for JobRepository.get_job()."""

    def _make_repo(self, row=None):
        """Return a JobRepository whose engine returns a fake connection."""
        from deckdex.storage.job_repository import JobRepository

        repo = JobRepository.__new__(JobRepository)
        repo._url = "postgresql://fake"
        repo._eng = None

        mock_conn = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.fetchone.return_value = row
        mock_conn.execute.return_value.mappings.return_value = mock_mappings
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s, *a: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        repo._eng = mock_engine
        return repo

    def test_returns_dict_when_row_found(self):
        from datetime import datetime, timezone

        from deckdex.storage.job_repository import JobRepository

        repo = JobRepository.__new__(JobRepository)
        repo._url = ""
        repo._eng = None

        dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        row = {
            "id": "abc-123",
            "user_id": 1,
            "type": "process",
            "status": "complete",
            "created_at": dt,
            "completed_at": dt,
            "result": {"status": "success"},
        }
        row_mock = MagicMock()
        row_mock.__getitem__ = lambda self, key: row[key]

        mock_conn = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.fetchone.return_value = row_mock
        mock_conn.execute.return_value.mappings.return_value = mock_mappings
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s, *a: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        repo._eng = mock_engine

        result = repo.get_job("abc-123")

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["type"], "process")
        self.assertEqual(result["created_at"], dt.isoformat())

    def test_returns_none_when_row_not_found(self):
        from deckdex.storage.job_repository import JobRepository

        repo = JobRepository.__new__(JobRepository)
        repo._url = ""
        repo._eng = None

        mock_conn = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.fetchone.return_value = None
        mock_conn.execute.return_value.mappings.return_value = mock_mappings
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s, *a: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        repo._eng = mock_engine

        result = repo.get_job("nonexistent-id")
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# Task 9.2 — JobRepository.mark_orphans_as_error
# ---------------------------------------------------------------------------


class TestJobRepositoryMarkOrphans(unittest.TestCase):
    """Unit tests for JobRepository.mark_orphans_as_error()."""

    def test_returns_rowcount_and_commits(self):
        from deckdex.storage.job_repository import JobRepository

        repo = JobRepository.__new__(JobRepository)
        repo._url = ""
        repo._eng = None

        mock_result = MagicMock()
        mock_result.rowcount = 2

        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_result
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s, *a: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        repo._eng = mock_engine

        count = repo.mark_orphans_as_error()

        self.assertEqual(count, 2)
        mock_conn.commit.assert_called_once()

    def test_zero_when_no_running_jobs(self):
        from deckdex.storage.job_repository import JobRepository

        repo = JobRepository.__new__(JobRepository)
        repo._url = ""
        repo._eng = None

        mock_result = MagicMock()
        mock_result.rowcount = 0

        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_result
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s, *a: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        repo._eng = mock_engine

        count = repo.mark_orphans_as_error()
        self.assertEqual(count, 0)


# ---------------------------------------------------------------------------
# Tasks 9.3 & 9.4 — GET /api/jobs/{job_id} DB fallback and 404
# ---------------------------------------------------------------------------


class TestGetJobStatusDBFallback(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(get_current_user_id, None)

    @patch("backend.api.routes.process._active_jobs", {})
    @patch("backend.api.routes.process._job_results", {})
    @patch("backend.api.routes.process._job_types", {})
    @patch("backend.api.routes.process.get_job_repo")
    def test_returns_200_from_db_when_not_in_memory(self, mock_get_job_repo):
        """DB fallback path: job in Postgres but not in memory returns 200."""
        mock_repo = MagicMock()
        mock_repo.get_job.return_value = {
            "job_id": "test-uuid-1234",
            "user_id": 1,
            "type": "process",
            "status": "complete",
            "created_at": "2025-01-01T12:00:00",
            "completed_at": "2025-01-01T12:05:00",
            "result": {"status": "success"},
        }
        mock_get_job_repo.return_value = mock_repo

        response = self.client.get("/api/jobs/test-uuid-1234")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "complete")
        self.assertEqual(data["job_type"], "process")
        mock_repo.get_job.assert_called_once_with("test-uuid-1234")

    @patch("backend.api.routes.process._active_jobs", {})
    @patch("backend.api.routes.process._job_results", {})
    @patch("backend.api.routes.process._job_types", {})
    @patch("backend.api.routes.process.get_job_repo")
    def test_returns_404_when_not_in_memory_or_db(self, mock_get_job_repo):
        """Returns 404 when job absent from both in-memory and DB."""
        mock_repo = MagicMock()
        mock_repo.get_job.return_value = None
        mock_get_job_repo.return_value = mock_repo

        response = self.client.get("/api/jobs/nonexistent-job")

        self.assertEqual(response.status_code, 404)

    @patch("backend.api.routes.process._active_jobs", {})
    @patch("backend.api.routes.process._job_results", {})
    @patch("backend.api.routes.process._job_types", {})
    @patch("backend.api.routes.process.get_job_repo")
    def test_returns_404_when_no_db_configured(self, mock_get_job_repo):
        """Returns 404 when no DB is configured and job not in memory."""
        mock_get_job_repo.return_value = None

        response = self.client.get("/api/jobs/nonexistent-job")

        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# Task 9.5 — GET /api/jobs/history is reachable (not shadowed by /{job_id})
# ---------------------------------------------------------------------------


class TestJobHistoryRouteOrdering(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(get_current_user_id, None)
        app.dependency_overrides.pop(get_job_repo, None)

    def test_history_route_is_reachable(self):
        """/api/jobs/history returns 200 (not intercepted by /{job_id})."""
        mock_repo = MagicMock()
        mock_repo.get_job_history.return_value = []
        app.dependency_overrides[get_job_repo] = lambda: mock_repo

        response = self.client.get("/api/jobs/history")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_history_route_returns_list_without_db(self):
        """/api/jobs/history returns empty list when no DB configured."""
        app.dependency_overrides[get_job_repo] = lambda: None

        response = self.client.get("/api/jobs/history")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


# ---------------------------------------------------------------------------
# Task 9.6 — catalog_service.start_sync uses JobRepository API
# ---------------------------------------------------------------------------


class TestCatalogServiceJobPersistence(unittest.TestCase):
    """Verify catalog_service calls create_job/update_job_status, not _engine."""

    def setUp(self):
        import backend.api.services.catalog_service as cs

        # Ensure the global lock is released before each test
        if cs._sync_lock.locked():
            cs._sync_lock.release()

    def tearDown(self):
        import time

        import backend.api.services.catalog_service as cs

        # Give background thread time to finish and release the lock
        time.sleep(0.3)
        if cs._sync_lock.locked():
            cs._sync_lock.release()

    @patch("backend.api.services.catalog_service.CatalogSyncJob")
    def test_start_sync_success_uses_job_repo_api(self, MockSyncJob):
        import time

        from backend.api.services import catalog_service

        mock_sync = MagicMock()
        MockSyncJob.return_value = mock_sync

        mock_catalog_repo = MagicMock()
        mock_catalog_repo.get_sync_state.return_value = {
            "total_cards": 100,
            "total_images_downloaded": 50,
        }

        mock_image_store = MagicMock()
        mock_job_repo = MagicMock()

        job_id = catalog_service.start_sync(
            catalog_repo=mock_catalog_repo,
            image_store=mock_image_store,
            job_repo=mock_job_repo,
            bulk_data_url="https://example.com/bulk.json",
            image_size="normal",
        )

        # Give the background thread time to finish
        time.sleep(0.3)

        # create_job called on start (before thread)
        mock_job_repo.create_job.assert_called_once_with(user_id=None, job_type="catalog_sync", job_id=job_id)
        # update_job_status called with 'complete' on success
        mock_job_repo.update_job_status.assert_called_once()
        call_args = mock_job_repo.update_job_status.call_args
        self.assertEqual(call_args[0][1], "complete")
        # _engine should NOT be called
        mock_job_repo._engine.assert_not_called()

    @patch("backend.api.services.catalog_service.CatalogSyncJob")
    def test_start_sync_failure_writes_error_status(self, MockSyncJob):
        import time

        from backend.api.services import catalog_service

        mock_sync = MagicMock()
        mock_sync.run.side_effect = RuntimeError("sync failed")
        MockSyncJob.return_value = mock_sync

        mock_catalog_repo = MagicMock()
        mock_image_store = MagicMock()
        mock_job_repo = MagicMock()

        catalog_service.start_sync(
            catalog_repo=mock_catalog_repo,
            image_store=mock_image_store,
            job_repo=mock_job_repo,
            bulk_data_url="https://example.com/bulk.json",
            image_size="normal",
        )

        time.sleep(0.3)

        mock_job_repo.update_job_status.assert_called_once()
        call_args = mock_job_repo.update_job_status.call_args
        self.assertEqual(call_args[0][1], "error")
        mock_job_repo._engine.assert_not_called()

    @patch("backend.api.services.catalog_service.CatalogSyncJob")
    def test_start_sync_skips_job_repo_when_none(self, MockSyncJob):
        import time

        from backend.api.services import catalog_service

        mock_sync = MagicMock()
        MockSyncJob.return_value = mock_sync
        mock_catalog_repo = MagicMock()
        mock_catalog_repo.get_sync_state.return_value = {}
        mock_image_store = MagicMock()

        # No exception even when job_repo is None
        catalog_service.start_sync(
            catalog_repo=mock_catalog_repo,
            image_store=mock_image_store,
            job_repo=None,
            bulk_data_url="https://example.com/bulk.json",
            image_size="normal",
        )
        time.sleep(0.3)
        # No assertion needed — test passes if no exception raised


# ---------------------------------------------------------------------------
# Task 9.7 — ProcessorService.update_single_card_price_async persist calls
# ---------------------------------------------------------------------------


class TestProcessorServiceSingleCardPersist(unittest.IsolatedAsyncioTestCase):
    """Verify _persist_job_start and _persist_job_end are called in update_single_card_price_async."""

    def _make_service(self, job_id: str):
        from backend.api.services.processor_service import ProcessorService

        service = ProcessorService.__new__(ProcessorService)
        service.config = MagicMock()
        service.progress_callback = None
        service._job_repo = MagicMock()
        service._user_id = 1
        service.job_id = job_id
        service.start_time = __import__("datetime").datetime.now()
        service.status = "pending"
        service.progress_data = {"current": 0, "total": 0, "percentage": 0.0, "errors": []}
        service._loop = None
        service._cancel_flag = __import__("threading").Event()
        service._lock = __import__("threading").Lock()
        return service

    async def test_persist_called_on_success(self):
        from unittest.mock import patch

        service = self._make_service("test-job-success")

        with (
            patch.object(service, "_persist_job_start") as mock_start,
            patch.object(service, "_persist_job_end") as mock_end,
            patch("backend.api.services.processor_service.MagicCardProcessor") as MockProcessor,
        ):
            mock_proc_instance = MagicMock()
            mock_proc_instance.error_count = 0
            mock_proc_instance.not_found_cards = []
            mock_proc_instance.update_prices_for_card_ids.return_value = None
            MockProcessor.return_value = mock_proc_instance

            await service.update_single_card_price_async(42)

        mock_start.assert_called_once_with("update_price")
        mock_end.assert_called_once()
        end_args = mock_end.call_args[0]
        self.assertEqual(end_args[0], "complete")

    async def test_persist_called_on_thread_error(self):
        """When the inner thread raises, result has status='error' and persist_job_end is called with 'error'."""
        from unittest.mock import patch

        service = self._make_service("test-job-thread-error")

        with (
            patch.object(service, "_persist_job_start") as mock_start,
            patch.object(service, "_persist_job_end") as mock_end,
            patch("backend.api.services.processor_service.MagicCardProcessor") as MockProcessor,
        ):
            mock_proc_instance = MagicMock()
            mock_proc_instance.error_count = 1
            mock_proc_instance.not_found_cards = []
            mock_proc_instance.update_prices_for_card_ids.side_effect = ValueError("price fetch failed")
            MockProcessor.return_value = mock_proc_instance

            result = await service.update_single_card_price_async(42)

        # Inner exception is caught by run_update; result status is 'error'
        self.assertEqual(result["status"], "error")
        mock_start.assert_called_once_with("update_price")
        mock_end.assert_called_once()
        end_args = mock_end.call_args[0]
        self.assertEqual(end_args[0], "error")

    async def test_persist_called_on_outer_exception(self):
        """When run_in_executor itself raises (outer except), _persist_job_end is called with 'error'."""
        from unittest.mock import patch

        service = self._make_service("test-job-outer-error")

        with (
            patch.object(service, "_persist_job_start") as mock_start,
            patch.object(service, "_persist_job_end") as mock_end,
            patch.object(service, "_emit_progress", new_callable=AsyncMock),
            patch("asyncio.get_event_loop") as mock_get_loop,
        ):
            mock_loop = MagicMock()

            async def fake_run_in_executor(executor, fn):
                raise RuntimeError("executor broken")

            mock_loop.run_in_executor = fake_run_in_executor
            mock_get_loop.return_value = mock_loop

            with self.assertRaises(RuntimeError):
                await service.update_single_card_price_async(42)

        mock_start.assert_called_once_with("update_price")
        mock_end.assert_called_once()
        end_args = mock_end.call_args[0]
        self.assertEqual(end_args[0], "error")
