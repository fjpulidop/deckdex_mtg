## Why

Card names containing commas, apostrophes, or spaces (e.g., "Jace, the Mind Sculptor", "Urza's Tower") produce malformed Scryfall API URLs because `CardFetcher` does not URL-encode query parameters in three of its four search methods. This causes silent 404s on `GET /api/cards/{id}/image` with no diagnostic information in logs to explain why.

## What Changes

- **Bug fix**: Apply `quote_plus()` to card name and query parameters in `_exact_match_search`, `_fuzzy_match_search`, and `_search_query` in `deckdex/card_fetcher.py`. The import already exists; it is only used in `autocomplete`.
- **Diagnostic logging**: Add `logger.debug` calls at each step of `backend/api/services/card_image_service.py` so Docker logs show the complete resolution trace: card lookup, cache check, Scryfall settings check, API fetch, image download, and store write.
- **Test coverage**: Update existing URL-assertion tests in `tests/test_card_fetcher.py` (lines 83, 95) and add new tests verifying that names with commas, apostrophes, and spaces are properly encoded.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is a pure bug fix and observability improvement with no behavioral spec changes.

## Impact

- `deckdex/card_fetcher.py` — three method bodies changed (URL construction only)
- `backend/api/services/card_image_service.py` — logging additions only, no logic changes
- `tests/test_card_fetcher.py` — updated URL assertions + new parametrized URL-encoding tests

## Non-goals

- No changes to Scryfall API contracts or image storage flow
- No new API endpoints or response schema changes
- No frontend changes
- No database migrations
