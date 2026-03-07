# Tasks

## Task 1: Fix URL encoding in CardFetcher search methods

**File**: `deckdex/card_fetcher.py`

**Description**: Apply `quote_plus()` to the card name / query string in the three methods that currently build raw, unencoded Scryfall URLs. The `quote_plus` function is already imported at line 6 — no new imports needed.

**Changes**:
- Line 112: Change `f"{self.BASE_URL}/cards/named?exact={card_name}"` to `f"{self.BASE_URL}/cards/named?exact={quote_plus(card_name)}"`
- Line 128: Change `f"{self.BASE_URL}/cards/named?fuzzy={card_name}"` to `f"{self.BASE_URL}/cards/named?fuzzy={quote_plus(card_name)}"`
- Line 144: Change `f"{self.BASE_URL}/cards/search?q={query}"` to `f"{self.BASE_URL}/cards/search?q={quote_plus(query)}"`

**Acceptance criteria**:
- All three f-strings wrap their variable with `quote_plus(...)`
- No other code in `card_fetcher.py` is modified
- `autocomplete` (line 94) is left unchanged (it already uses `quote_plus`)

- [x] Done

---

## Task 2: Update existing URL assertion tests for new encoding

**File**: `tests/test_card_fetcher.py`

**Description**: Two existing tests assert against unencoded URLs. After Task 1 these assertions will fail. Update them to expect the percent-encoded form.

**Changes**:
- In `test_exact_match_search` (around line 83): Change `expected_url = f"{CardFetcher.BASE_URL}/cards/named?exact=Test Card"` to `expected_url = f"{CardFetcher.BASE_URL}/cards/named?exact=Test+Card"`
- In `test_fuzzy_match_search` (around line 95): Change `expected_url = f"{CardFetcher.BASE_URL}/cards/named?fuzzy=Test Crd"` to `expected_url = f"{CardFetcher.BASE_URL}/cards/named?fuzzy=Test+Crd"`

**Acceptance criteria**:
- `pytest tests/test_card_fetcher.py::TestCardFetcher::test_exact_match_search` passes
- `pytest tests/test_card_fetcher.py::TestCardFetcher::test_fuzzy_match_search` passes
- No other tests in the file are modified

**Depends on**: Task 1

- [x] Done

---

## Task 3: Add URL encoding tests for special-character card names

**File**: `tests/test_card_fetcher.py`

**Description**: Add a new test class `TestCardFetcherUrlEncoding` after the existing `TestCardFetcher` class. Each test mocks `_make_request`, calls a search method with a card name containing special characters, and asserts the URL passed to the mock is correctly encoded.

All tests use `scope="function"` (default for `setUp`-based `unittest.TestCase` — no explicit scope needed). Mock pattern: `@patch.object(CardFetcher, "_make_request")` with a `return_value` of a dummy dict.

**Tests to add**:

1. `test_exact_match_search_comma_in_name`
   - Input: `"Jace, the Mind Sculptor"`
   - Expected URL: `f"{CardFetcher.BASE_URL}/cards/named?exact=Jace%2C+the+Mind+Sculptor"`

2. `test_exact_match_search_apostrophe_in_name`
   - Input: `"Urza's Tower"`
   - Expected URL: `f"{CardFetcher.BASE_URL}/cards/named?exact=Urza%27s+Tower"`

3. `test_fuzzy_match_search_comma_in_name`
   - Input: `"Jace, the Mind Sculptor"`
   - Expected URL: `f"{CardFetcher.BASE_URL}/cards/named?fuzzy=Jace%2C+the+Mind+Sculptor"`

4. `test_search_query_encodes_full_expression`
   - Input: `'!"Jace, the Mind Sculptor"'` (the Scryfall exact-match syntax used by `search_card` strategy 3)
   - Expected URL: `f"{CardFetcher.BASE_URL}/cards/search?q=%21%22Jace%2C+the+Mind+Sculptor%22"`
   - Note: For this test, `_make_request` must return `{"data": [{"name": "Jace, the Mind Sculptor"}]}` so `_search_query` can extract `response["data"][0]` without returning `None`.

**Acceptance criteria**:
- All four new tests pass
- `pytest tests/test_card_fetcher.py` passes entirely (all existing + new tests)
- Tests follow `@patch.object(CardFetcher, "_make_request")` pattern consistent with rest of file
- No real HTTP calls are made

**Depends on**: Task 1, Task 2

- [x] Done

---

## Task 4: Add diagnostic logging to card_image_service.py

**File**: `backend/api/services/card_image_service.py`

**Description**: Add `logger.debug(...)` calls at each resolution step inside `get_card_image`. The `logger` object is already imported (line 19). No imports or logic changes needed — additions only.

**Additions** (add immediately after each described line):

1. After `if repo is None: raise FileNotFoundError(...)` guard (after line 46):
   ```python
   logger.debug(f"get_card_image: card_id={card_id}, user_id={user_id}")
   ```

2. After `scryfall_id = card.get("scryfall_id") or None` (after line 60):
   ```python
   logger.debug(f"get_card_image: resolved card name='{name}', scryfall_id={scryfall_id!r}")
   ```

3. Before `if scryfall_id:` (the first cache check, before line 63):
   ```python
   logger.debug(f"get_card_image: checking ImageStore cache, scryfall_id={scryfall_id!r}")
   ```

4. Inside `if cached is not None:` (before the `return cached` at line 67):
   ```python
   logger.debug(f"get_card_image: ImageStore cache hit, returning for scryfall_id={scryfall_id}")
   ```

5. After the `scryfall_enabled` assignment block (after line 77):
   ```python
   logger.debug(f"get_card_image: scryfall_enabled={scryfall_enabled} for user_id={user_id}")
   ```

6. Before `scryfall_card = fetcher.search_card(name)` (before line 89):
   ```python
   logger.debug(f"get_card_image: cache miss — fetching from Scryfall for name='{name}'")
   ```

7. After successful `fetcher.search_card` and after `image_url` is resolved (after line 103):
   ```python
   logger.debug(f"get_card_image: Scryfall fetch succeeded, fetched_scryfall_id={fetched_scryfall_id!r}, image_url={image_url!r}")
   ```

8. Before `resp = requests.get(image_url, ...)` (before line 127):
   ```python
   logger.debug(f"get_card_image: downloading image from Scryfall URL")
   ```

9. After `image_store.put(scryfall_id, data, content_type)` succeeds (inside the try, after line 137):
   ```python
   logger.debug(f"get_card_image: stored image in ImageStore for scryfall_id={scryfall_id}")
   ```

**Acceptance criteria**:
- `get_card_image` contains at least 9 `logger.debug` calls covering entry, card lookup, first cache check, cache hit, scryfall_enabled check, Scryfall fetch start, Scryfall fetch result, image download start, and image store write
- No existing `logger.warning` or `logger.error` calls are modified
- No logic changes — only `logger.debug(...)` lines added
- `pytest tests/` continues to pass (service tests, if any, are unaffected)

- [x] Done

---

## Task 5: Verify full test suite passes

**Description**: Run the complete test suite to confirm no regressions from the URL encoding fix or logging additions.

**Command**:
```
pytest tests/
```

**Acceptance criteria**:
- All tests pass with zero failures
- `tests/test_card_fetcher.py` shows all original tests plus the 4 new URL encoding tests passing
- No import errors or unexpected warnings

- [x] Done — 506 passed, 0 failures
