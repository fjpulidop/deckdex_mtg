## 1. Core Layer — Repository Method

- [x] 1.1 Add `get_type_line_data` abstract method to `CollectionRepository` in `deckdex/storage/repository.py`. Method signature: `def get_type_line_data(self, user_id: Optional[int], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`. Default implementation returns `[]`. Add a docstring explaining it returns rows of `{type_line: str | None, quantity: int}` for use by the analytics/type endpoint.

- [x] 1.2 Implement `get_type_line_data` in `PostgresCollectionRepository` in `deckdex/storage/repository.py`. Implementation: call `self._build_filter_clauses(filters, user_id)` to get `(where, params)`, then execute `SELECT type_line, quantity FROM cards {where}` via `self._get_engine()`. Return `[{"type_line": row[0], "quantity": int(row[1] or 1)} for row in rows]`. Import `sqlalchemy.text` at the top of the method (consistent with all other methods in the class).

## 2. Backend Layer — Route Architecture Fix

- [x] 2.1 Rewrite the Postgres branch of `analytics_type` in `backend/api/routes/analytics.py` (currently lines 494–533). Replace the entire `isinstance(_repo, PostgresCollectionRepository)` block with a call to `repo.get_type_line_data(user_id=user_id, filters=filters_dict)`. Apply `_extract_primary_type` to the returned rows in a Counter loop identical to the existing pattern. Remove the `from sqlalchemy import text`, `from ..dependencies import get_collection_repo as _get_repo`, and `from deckdex.storage.repository import PostgresCollectionRepository` imports that were only needed by the old implementation.

- [x] 2.2 Verify the updated `analytics_type` function: (a) it no longer imports SQLAlchemy, (b) it no longer accesses `_build_filter_clauses` or `_get_engine`, (c) it has a single repo branch (`if repo is not None: ... else: ...`) instead of the three-way `if repo / isinstance / else` structure, (d) the Sheets path (the `else` branch) is unchanged.

## 3. Tests — Analytics Color-Identity Endpoint

- [x] 3.1 Add `TestAnalyticsColorIdentity` class to `tests/test_api_extended.py`. Include the following tests using the established double-mock pattern (`patch("backend.api.routes.analytics.get_collection_repo", return_value=None)` and `patch("backend.api.routes.analytics.get_cached_collection", return_value=...)`):
  - `test_color_identity_returns_200`: call with empty collection, assert status 200.
  - `test_color_identity_response_shape`: call with `SAMPLE_CARDS`, assert response is a list where each item has `color_identity` (str) and `count` (int) keys.
  - `test_color_identity_aggregates_correctly`: use a fixture with 2 Red cards (color_identity="R") and 1 Blue card (color_identity="U"), assert the normalized Red entry has count 2 and the normalized Blue entry has count 1. Note: the `normalize_color_identity` function maps single letters to their canonical form; "R" normalizes to "R" (Monocolor Red).

- [x] 3.2 Clear `_analytics_cache` in `setUp` of `TestAnalyticsColorIdentity` to prevent cross-test cache pollution. Access via `import backend.api.routes.analytics as _analytics_mod; _analytics_mod._analytics_cache.clear()` in the `setUp` method.

## 4. Tests — Analytics CMC Endpoint

- [x] 4.1 Add `TestAnalyticsCmc` class to `tests/test_api_extended.py` with the following tests:
  - `test_cmc_returns_200`: empty collection, assert status 200.
  - `test_cmc_response_shape`: assert each item in the response list has `cmc` (str) and `count` (int) keys.
  - `test_cmc_null_maps_to_unknown`: fixture with one card having `cmc=None`, assert response contains an entry with `cmc="Unknown"`.
  - `test_cmc_seven_plus_bucket`: fixture with one card having `cmc=8`, assert response contains an entry with `cmc="7+"`.
  - `test_cmc_bucket_ordering`: fixture with cards at cmc=0, cmc=3, cmc=8, cmc=None. Assert result order is ["0", "3", "7+", "Unknown"] by extracting the `cmc` field from each item in order.

- [x] 4.2 Clear `_analytics_cache` in `setUp` of `TestAnalyticsCmc` (same pattern as task 3.2).

## 5. Tests — Analytics Type Endpoint

- [x] 5.1 Define type-specific test fixture cards at module level in `tests/test_api_extended.py`:
  ```python
  TYPE_CARDS = [
      {"name": "Goblin Guide", "type": "Creature — Goblin Scout", "rarity": "rare", "set_name": "ZEN", "price": "5"},
      {"name": "Sol Ring", "type": "Artifact", "rarity": "uncommon", "set_name": "C21", "price": "2"},
      {"name": "Swords to Plowshares", "type": "Instant", "rarity": "uncommon", "set_name": "EMA", "price": "3"},
      {"name": "Unknown Card", "type": "", "rarity": "common", "set_name": "M10", "price": "0.1"},
      {"name": "Golem Artisan", "type": "Artifact Creature — Golem", "rarity": "uncommon", "set_name": "SOM", "price": "1"},
  ]
  ```

- [x] 5.2 Add `TestAnalyticsType` class to `tests/test_api_extended.py` with the following tests:
  - `test_type_returns_200`: empty collection, assert status 200.
  - `test_type_response_shape`: call with `TYPE_CARDS`, assert response is a list where each item has `type_line` (str) and `count` (int) keys.
  - `test_type_creature_extraction`: call with `TYPE_CARDS`, find the entry with `type_line="Creature"`, assert its count is 2 (Goblin Guide + Golem Artisan both map to Creature via priority).
  - `test_type_other_for_empty_type`: call with `TYPE_CARDS`, find the entry with `type_line="Other"`, assert count is 1 (Unknown Card).
  - `test_type_priority_creature_over_artifact`: call with a single card having `type="Artifact Creature — Golem"`, assert only one bucket exists in response and it is `type_line="Creature"`.

- [x] 5.3 Clear `_analytics_cache` in `setUp` of `TestAnalyticsType` (same pattern as task 3.2).

## 6. Tests — Price History Endpoint

- [x] 6.1 Add `TestCardPriceHistory` class to `tests/test_api_extended.py`. The price-history tests mock at the `backend.api.routes.cards` module level. Include:
  - `test_price_history_501_without_postgres`: mock `backend.api.routes.cards.get_collection_repo` to return `None`, call `GET /api/cards/1/price-history`, assert status 501.
  - `test_price_history_404_card_not_found`: mock `get_collection_repo` to return a `MagicMock` whose `get_card_by_id` returns `None`, call `GET /api/cards/99/price-history`, assert status 404.
  - `test_price_history_200_with_data`: mock `get_collection_repo` to return a `MagicMock` where `get_card_by_id` returns `{"id": 1, "name": "Lightning Bolt"}` and `get_price_history` returns `[{"recorded_at": "2024-01-01T00:00:00", "price": 0.5, "source": "scryfall", "currency": "eur"}]`. Call `GET /api/cards/1/price-history`. Assert status 200, response has keys `card_id`, `currency`, `points`, and `points` is a list with one item having `recorded_at`, `price`, `source`, `currency`.
  - `test_price_history_200_empty_history`: same mock setup but `get_price_history` returns `[]`. Assert status 200 and `points` is an empty list (card exists but no history yet — not an error).

## 7. Verification

- [x] 7.1 Run `pytest tests/test_api_extended.py -v` from repo root. Confirm all new test classes appear and all tests pass (green). The test count should increase from 7 to at least 25.

- [x] 7.2 Run `pytest tests/ -v` from repo root. Confirm no existing tests are broken by the repository change (the new `get_type_line_data` method is additive — no existing method signatures changed).

- [x] 7.3 Verify there are no SQLAlchemy or `deckdex.storage.repository` imports remaining in `backend/api/routes/analytics.py` that were added for the old `analytics_type` implementation. Use `grep -n "sqlalchemy\|PostgresCollectionRepository\|_build_filter_clauses\|_get_engine" backend/api/routes/analytics.py` — should return no matches.
