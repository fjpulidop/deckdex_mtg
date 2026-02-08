# Web API Backend

FastAPI; collection data, process execution, job monitoring. **Endpoints:** GET /api/health (200 + service/version); CORS for localhost:5173. GET /api/cards (list; optional limit, offset, search, rarity, type, set_name, price_min, price_max); GET /api/cards/{id}/image (card image by id, on-demand Scryfall fetch and store); GET /api/cards/{card_name} (single). Parse prices: EU/US formats with/without thousands separators; skip invalid/N/A. GET /api/stats (total_cards, total_value, average_price, last_updated); same filter params as cards; 30s cache per filter key. POST /api/process (optional limit) → job_id, background run; POST /api/prices/update → job_id; POST /api/prices/update/{card_id} → job_id (single-card). 409 if bulk process already running. GET /api/jobs, GET /api/jobs/{id} (status, progress, errors, start_time; completed: summary). POST /api/jobs/{id}/cancel → 200 (or 404/409). POST /api/import/file — CSV/JSON to Postgres (DATABASE_URL); 400 invalid file, 501 no Postgres. GET /api/cards/suggest?q=, GET /api/cards/resolve?name= (Scryfall); GET /api/analytics/rarity, color-identity, cmc, sets (same filter params as stats).

Reuse SpreadsheetClient, CardFetcher, config_loader; ProcessorService. Errors: 400 invalid params, 503 Sheets quota (Retry-After), 500 + log. Log requests (method, path, status) INFO; errors ERROR.

### Requirements (compact)

- **Stats:** GET /api/stats → total_cards, total_value, average_price, last_updated. Optional query: search, rarity, type, set_name, price_min, price_max (same semantics as cards: name contains, exact match rarity/type/set_name, price range). Cache 30s per filter combination. Price parsing: EU/US with or without thousands; skip N/A and invalid.
- **Cards list:** GET /api/cards — filter then paginate (limit/offset); same filter semantics as stats so list and stats match. Order: newest first (created_at DESC) when store supports it. Card object MAY include created_at (ISO).
- **Card single:** GET /api/cards/{id} or name → 404 if not found. GET /api/cards/{id}/image → image bytes or 404; fetch/store from Scryfall when missing.
- **Suggest:** GET /api/cards/suggest?q= → JSON array of names (Scryfall); empty/short q → [] or 400.
- **Resolve:** GET /api/cards/resolve?name= → full card data for create; 404 if not found.
- **Single-card price update:** POST /api/prices/update/{card_id} → job_id; 404 if no card; not blocked by bulk update (409 only for concurrent bulk).
- **Analytics:** GET /api/analytics/rarity|color-identity|cmc|sets — same filter params as stats; JSON arrays for charts (e.g. { rarity, count }); KPIs via GET /api/stats with same params.
