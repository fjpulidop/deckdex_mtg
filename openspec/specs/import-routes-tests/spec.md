# Import Routes Tests

Automated pytest tests for all 5 import API endpoints in `backend/api/routes/import_routes.py`. No real DB, Scryfall, or filesystem access; all external dependencies are mocked.

## Requirements

### Endpoint: POST /api/import/file

- **Success (CSV)**: Upload valid CSV with Name column → 200, `{"imported": N}`
- **Success (JSON array)**: Upload valid JSON array of card objects → 200, `{"imported": N}`
- **No file**: POST with no file → 400
- **No Postgres**: When `get_collection_repo` returns None → 501
- **Empty CSV**: CSV with header only and no data rows → 400

### Endpoint: POST /api/import/preview

- **Success (text)**: POST with `text` form field containing MTGO-style text → 200, body has `detected_format`, `card_count`, `sample`
- **Success (file)**: POST with uploaded file → 200, body has `detected_format`, `card_count`, `sample`
- **No input**: POST with neither file nor text → 400
- **Empty text**: POST with blank/whitespace text and no file → 400

### Endpoint: POST /api/import/resolve

- **Success (text)**: POST with MTGO text → 200, `ResolveResponse` with `format`, `total`, `matched_count`, `unresolved_count`, `cards`
- **Success (file)**: POST with file → 200, valid `ResolveResponse`
- **No input**: POST with neither file nor text → 400
- **No cards parsed**: Parser returns empty list → 400

### Endpoint: POST /api/import/external

- **Success**: POST with text or file → 200, body has `job_id`, `card_count`, `format`, `mode`
- **No Postgres**: When `get_collection_repo` returns None → 501
- **No input**: POST with neither file nor text → 400

### Endpoint: POST /api/import/external/cards

- **Success**: POST JSON body with cards list → 200, body has `job_id`, `card_count`, `format`, `mode`
- **No Postgres**: When `get_collection_repo` returns None → 501
- **Empty cards list**: POST with `{"cards": []}` → 400

## Testing Conventions

- Use pytest functions (not `unittest.TestCase`)
- One `@pytest.fixture(scope="module")` for the shared `TestClient` with `get_current_user_id` overridden
- Use `unittest.mock.patch` (context manager) for module-level dependencies in `import_routes`
- Rate limiter must be disabled or bypassed in the test fixture
- Background tasks (async import) are verified by response shape only, not execution
