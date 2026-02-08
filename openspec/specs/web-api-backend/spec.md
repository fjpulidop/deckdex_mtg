# Web API Backend

FastAPI; collection data, process execution, job monitoring. **Endpoints:** GET /api/health (200 + service/version); CORS for localhost:5173. GET /api/cards (list; optional limit, offset, search); GET /api/cards/{card_name} (single). Parse prices: EU/US formats with/without thousands separators; skip invalid/N/A. GET /api/stats (total_cards, total_value, average_price, last_updated); 30s cache. POST /api/process (optional limit) → job_id, background run; POST /api/prices/update → job_id. 409 if process already running. GET /api/jobs, GET /api/jobs/{id} (status, progress, errors, start_time; completed: summary). POST /api/jobs/{id}/cancel → 200 with status cancelled (or 404/409).

Reuse SpreadsheetClient, CardFetcher, config_loader; wrap processor via ProcessorService. Errors: 400 invalid params, 503 Sheets quota (retry-after), 500 + log traceback. Log requests (endpoint, method, status) at INFO; errors at ERROR.
