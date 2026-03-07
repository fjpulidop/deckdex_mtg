## Context

Five analytics endpoints are live in `backend/api/routes/analytics.py`. The existing test file (`tests/test_api_extended.py`) covers only `/rarity` (3 tests) and `/sets` (3 tests) — all exercising the Sheets (in-memory) path via mock. The endpoints `/color-identity`, `/cmc`, and `/type` have zero tests, and `GET /api/cards/{id}/price-history` (defined in `backend/api/routes/cards.py`, backed by `deckdex/storage/repository.py`) has none.

The most critical issue is that `analytics_type` in `analytics.py` (lines 494–516) imports `sqlalchemy.text`, calls the private `_build_filter_clauses` and `_get_engine` methods on the repo instance, and executes raw SQL directly in the route. This violates the project's core convention: "All DB ops through `storage/repository.py`. No raw SQL elsewhere." It also breaks the layer boundary by coupling the route to SQLAlchemy internals.

All other analytics endpoints correctly delegate to `repo.get_cards_analytics(dimension=...)` which is a public method on `CollectionRepository`. The `analytics_type` endpoint exists as a special case because type aggregation requires Python-level logic (`_extract_primary_type`) that is difficult to replicate purely in SQL — a hybrid approach (SQL filtering + Python aggregation) is the right design, but the SQL part must live in the repository layer.

## Goals / Non-Goals

**Goals:**

- Move the raw SQL in `analytics_type` into a public `get_type_line_data` method on `CollectionRepository` / `PostgresCollectionRepository`.
- Add comprehensive tests for `/color-identity`, `/cmc`, `/type`, and `GET /api/cards/{id}/price-history` covering shape, aggregation, and key edge cases.
- All tests exercise the Sheets (in-memory) path using the same mock pattern already established in `test_api_extended.py`.

**Non-Goals:**

- Postgres integration tests (no live DB in CI).
- LRU/max-size eviction for `_analytics_cache`.
- Frontend changes.
- Any other analytics endpoint refactors.

## Decisions

### Decision 1: New public method `get_type_line_data` in the repository

**Why**: The type aggregation needs a lightweight SQL query that returns only `(type_line, quantity)` pairs for filtered cards — not full card dicts. This is genuinely a data-access concern, not a route concern. Adding a named method (`get_type_line_data`) is the minimal correct fix: the method signature is clean (`user_id`, `filters`) and it encapsulates the SQLAlchemy dependency entirely within `deckdex/storage/repository.py`.

**Alternative considered**: Extend `get_cards_analytics` to support a `"type_line"` dimension with a SQL-only approximation (REGEXP or CASE to extract primary type). Rejected because the extraction logic is non-trivial in SQL and already correctly implemented as `_extract_primary_type` in Python. Duplicating it in SQL creates a divergence risk.

**Alternative considered**: Move `_extract_primary_type` into `deckdex/` and have the repository return raw rows. Accepted as the correct long-term home but out of scope here — the function currently lives in the route file and works correctly there. The route will call the new repository method and then apply `_extract_primary_type` to the returned rows, exactly as it does today but without the private method access.

**Method signature** (Core layer — `deckdex/storage/repository.py`):

```python
def get_type_line_data(
    self,
    user_id: Optional[int],
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Return lightweight rows of (type_line, quantity) for filtered cards.

    Used by the analytics/type endpoint to perform Python-level primary-type
    extraction over a SQL-filtered result set.

    Default: returns []. Postgres subclass executes:
        SELECT type_line, quantity FROM cards {where}

    Returns:
        List of {'type_line': str | None, 'quantity': int}
    """
    return []
```

**Postgres implementation**: Calls `self._build_filter_clauses(filters, user_id)` (private but within the same class — this is acceptable, `_build_filter_clauses` is a private helper of `PostgresCollectionRepository`, not a cross-layer access) and executes `SELECT type_line, quantity FROM cards {where}`. Returns list of dicts.

**Updated route** (`backend/api/routes/analytics.py`): The `analytics_type` handler replaces the entire `isinstance(_repo, PostgresCollectionRepository)` block with:

```python
if repo is not None:
    rows = repo.get_type_line_data(user_id=user_id, filters=filters_dict)
    counter: Counter = Counter()
    for row in rows:
        primary = _extract_primary_type(row.get("type_line") or "")
        counter[primary] += int(row.get("quantity") or 1)
```

This is simpler, no SQLAlchemy imports in the route, and no `isinstance` check needed.

### Decision 2: Test structure follows existing `test_api_extended.py` patterns exactly

All new tests use `unittest.TestCase`, `TestClient(app)`, and the established double-mock pattern:

```python
with (
    patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
    patch("backend.api.routes.analytics.get_cached_collection", return_value=CARDS),
):
    response = client.get("/api/analytics/...")
```

Setting `get_collection_repo` to `None` forces the in-memory (Sheets) code path. This is the correct approach — it tests real aggregation logic without a database.

For the price-history endpoint (which is in `backend/api/routes/cards.py`), the approach differs because price-history is Postgres-only:
- **Happy path**: Mock `backend.api.routes.cards.get_collection_repo` to return a mock repo object whose `get_card_by_id` and `get_price_history` methods return controlled data.
- **Sheets path (501)**: Mock `get_collection_repo` to return `None` — the route correctly raises HTTP 501.
- **Not found (404)**: Mock repo where `get_card_by_id` returns `None`.

### Decision 3: Cache invalidation not touched

The `_analytics_cache` module-level dict has no max-size eviction. This is a known issue but explicitly out of scope for this change. Adding tests that exercise caching behavior is also out of scope — the cache is a module-level side effect that would require careful isolation (clearing between tests). The existing tests don't test caching and neither will these.

## Risks / Trade-offs

**Risk: Cache state bleeds across tests** → The `_analytics_cache` dict persists across test runs within a session. If a test fires the endpoint and populates the cache, the next test sees cached data from a different mock. Mitigation: Existing tests don't observe this problem because the cache key includes user_id and filter params. The new tests use the same user_id (1) and no filter params — if tests in one class share the same cache key they could collide. Mitigation: Clear the cache in setUp or use distinct filter params per test class. The `_analytics_cache` dict is accessible via `backend.api.routes.analytics._analytics_cache` and can be cleared in setUp.

**Risk: `get_type_line_data` default returns `[]`** → In Google Sheets mode (repo is None), the route takes the `else` branch and uses the existing in-memory collection loop. The new method is only called when `repo is not None` (Postgres mode). This is correct and consistent with how all other analytics endpoints handle the dual-backend split.

**Trade-off: Method returns raw dicts not typed tuples** → Returning `List[Dict[str, Any]]` is consistent with all other repository methods (e.g., `get_all_cards`, `get_cards_analytics`). Typed tuples would be more precise but inconsistent with established patterns.

## Migration Plan

No database migration required. No new tables or columns. The change is purely in Python code:

1. Add `get_type_line_data` to `CollectionRepository` ABC (default no-op).
2. Implement `get_type_line_data` in `PostgresCollectionRepository`.
3. Rewrite `analytics_type` in `analytics.py` to call the new method.
4. Add test classes in `tests/test_api_extended.py`.
5. Run `pytest tests/` to verify all tests pass.

Rollback: revert the route change if needed — no persistent state involved.

## Open Questions

None. All design decisions are resolved.
