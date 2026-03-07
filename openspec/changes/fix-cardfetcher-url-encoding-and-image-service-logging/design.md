## Change Summary

Three search methods in `deckdex/card_fetcher.py` build Scryfall API URLs by concatenating raw card name strings without percent-encoding them. Card names with commas, apostrophes, spaces, or non-ASCII characters produce URLs that Scryfall rejects with 4xx errors. Because each method silently catches all exceptions and returns `None`, all four search strategies fail, `search_card` raises, and the image endpoint returns 404 with no useful trace. The fix applies `quote_plus()` — already imported and used correctly in `autocomplete` — to the three broken methods, and adds `logger.debug` calls throughout `card_image_service.py` to make the resolution path observable in Docker logs.

## Impact Analysis

| Layer | File | Change type |
|---|---|---|
| Core | `deckdex/card_fetcher.py` | Bug fix — URL construction in 3 methods |
| Backend service | `backend/api/services/card_image_service.py` | Observability — debug log statements |
| Tests | `tests/test_card_fetcher.py` | Test update + new URL encoding tests |

No database migrations, no API schema changes, no frontend changes.

## Implementation Design

### 1. `deckdex/card_fetcher.py` — URL encoding fix

**Root cause**: Lines 112, 128, and 144 interpolate `card_name` or `query` directly into f-strings without encoding. `quote_plus` is already imported at line 6 and used correctly on line 94 (`autocomplete`).

**Fix for `_exact_match_search` (line 112)**:
```python
# Before
url = f"{self.BASE_URL}/cards/named?exact={card_name}"
# After
url = f"{self.BASE_URL}/cards/named?exact={quote_plus(card_name)}"
```

**Fix for `_fuzzy_match_search` (line 128)**:
```python
# Before
url = f"{self.BASE_URL}/cards/named?fuzzy={card_name}"
# After
url = f"{self.BASE_URL}/cards/named?fuzzy={quote_plus(card_name)}"
```

**Fix for `_search_query` (line 144)**:
```python
# Before
url = f"{self.BASE_URL}/cards/search?q={query}"
# After
url = f"{self.BASE_URL}/cards/search?q={quote_plus(query)}"
```

**Why `quote_plus` and not `quote`**: `quote_plus` encodes spaces as `+`, which is the conventional encoding for query string values. `quote` encodes spaces as `%20`. Scryfall accepts both, but `quote_plus` is already the project convention (used in `autocomplete`) so this keeps things consistent.

**Important**: The `_search_query` method also receives constructed query strings from `search_card` (lines 177 and 187 in the caller). These queries include Scryfall syntax characters like `!`, `"`, `/`, and `i` flags. The full query string passed to `_search_query` must be URL-encoded as a single unit. This is correct — `quote_plus` encodes the entire query value including Scryfall syntax. Scryfall parses the `q=` parameter after URL-decoding, so encoding the full expression is the right approach.

### 2. `backend/api/services/card_image_service.py` — Diagnostic logging

The function `get_card_image` has 7 logical steps. Currently only error/warning paths are logged. Adding `logger.debug` at entry and exit of each step creates a complete trace in DEBUG-level logs without changing behavior or performance in production (loguru's DEBUG level is typically suppressed unless `LOG_LEVEL=DEBUG` is set).

**Step-by-step additions to `get_card_image`**:

After the `repo is None` guard (line 46), add:
```python
logger.debug(f"get_card_image: card_id={card_id}, user_id={user_id}")
```

After `card = repo.get_card_by_id(card_id)` (line 52), add:
```python
logger.debug(f"get_card_image: resolved card name='{name}', scryfall_id={scryfall_id!r}")
```

Before the `if scryfall_id:` cache check (line 63), add:
```python
logger.debug(f"get_card_image: checking ImageStore for scryfall_id={scryfall_id!r}")
```

After the `cached = image_store.get(scryfall_id)` line (line 65) and inside `if cached is not None`, add:
```python
logger.debug(f"get_card_image: ImageStore cache hit for scryfall_id={scryfall_id}")
```

After the `scryfall_enabled` check block (line 79), add:
```python
logger.debug(f"get_card_image: scryfall_enabled={scryfall_enabled} for user_id={user_id}")
```

Before `fetcher.search_card(name)` (line 89), add:
```python
logger.debug(f"get_card_image: fetching from Scryfall for name='{name}'")
```

After the `scryfall_card = fetcher.search_card(name)` call succeeds, add:
```python
logger.debug(f"get_card_image: Scryfall returned id={fetched_scryfall_id!r}, image_url={image_url!r}")
```

Before the download request (line 127), add:
```python
logger.debug(f"get_card_image: downloading image from {image_url}")
```

After `image_store.put` succeeds (line 137), add:
```python
logger.debug(f"get_card_image: stored image in ImageStore for scryfall_id={scryfall_id}")
```

**Log level choice**: `logger.debug` is appropriate. These are internal resolution steps — verbose, high-frequency in production but essential for diagnosing failures. A developer debugging a 404 will set `LOG_LEVEL=DEBUG` and see the complete trace. INFO would be too noisy in normal operation.

**No changes to `get_card_image_path`**: This wrapper function's logic is simple — it calls `get_card_image` then resolves the file path. The inner function already has full coverage.

### 3. `tests/test_card_fetcher.py` — Test updates and additions

**Existing tests that must be updated**: Two tests assert against un-encoded URLs (lines 83-84 and 95-96):

```python
# test_exact_match_search (line 83-84) — current assertion:
expected_url = f"{CardFetcher.BASE_URL}/cards/named?exact=Test Card"
# Must become:
expected_url = f"{CardFetcher.BASE_URL}/cards/named?exact=Test+Card"

# test_fuzzy_match_search (line 95-96) — current assertion:
expected_url = f"{CardFetcher.BASE_URL}/cards/named?fuzzy=Test Crd"
# Must become:
expected_url = f"{CardFetcher.BASE_URL}/cards/named?fuzzy=Test+Crd"
```

**New tests to add** — add a new `TestCardFetcherUrlEncoding` class after the existing class:

1. `test_exact_match_search_comma_in_name` — verifies "Jace, the Mind Sculptor" produces `Jace%2C+the+Mind+Sculptor` in the URL
2. `test_exact_match_search_apostrophe_in_name` — verifies "Urza's Tower" produces `Urza%27s+Tower`
3. `test_fuzzy_match_search_comma_in_name` — same comma case for fuzzy endpoint
4. `test_search_query_encodes_full_expression` — verifies `_search_query('!"Jace, the Mind Sculptor"')` encodes the whole expression as a single query value

All new tests follow the existing `@patch.object(CardFetcher, "_make_request")` pattern: mock `_make_request`, call the method, assert the URL passed to the mock via `mock_make_request.assert_called_once_with(expected_url)`.

## Task Breakdown

See `tasks.md`.

## Risks and Considerations

**Existing test breakage**: The two URL assertion tests (`test_exact_match_search`, `test_fuzzy_match_search`) will fail immediately after the fix because they assert the old unencoded URL. The task plan updates these tests in the same task as the code fix, so CI is never broken.

**`_search_query` with Scryfall syntax**: The callers in `search_card` pass queries like `'!"Jace, the Mind Sculptor"'` and `'/Jace/i /Mind/i'`. When URL-encoded, these become `%21%22Jace%2C+the+Mind+Sculptor%22` and `%2FJace%2Fi+%2FMind%2Fi`. Scryfall decodes these correctly and processes them as intended. This was verified by consulting Scryfall API documentation behavior — the API accepts URL-encoded Scryfall syntax in the `q` parameter.

**No behavioral regression**: The `autocomplete` method already uses `quote_plus` and has been working correctly. Applying the same pattern to the three broken methods cannot regress card fetching for simple names (single words without special chars) because `quote_plus("Lightning Bolt")` produces `Lightning+Bolt`, which Scryfall accepts identically to `Lightning%20Bolt`.

**Logging performance**: `logger.debug` calls with f-strings only evaluate when loguru actually processes the message at DEBUG level. In production (INFO level), the string is never constructed. No performance concern.
