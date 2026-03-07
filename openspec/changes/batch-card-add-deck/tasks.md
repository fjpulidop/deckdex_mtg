# Tasks: Batch Card Add for Decks + Currency Fix

Tasks are ordered by dependency. Core changes first, then Backend, then Frontend, then Tests.

---

## Core

### Task 1: Add `add_cards_batch()` to `DeckRepository`

**File:** `deckdex/storage/deck_repository.py`

**What to do:**

Add a new method to the `DeckRepository` class after the existing `add_card` method:

```python
def add_cards_batch(
    self,
    deck_id: int,
    card_ids: List[int],
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Add multiple cards from the collection to a deck in one transaction.

    Cards not found in the user's collection are skipped and returned in not_found.
    Existing deck_cards entries have their quantity incremented by 1 (same as add_card).
    Returns {"added": [int, ...], "not_found": [int, ...]}.
    """
    from sqlalchemy import text

    if not card_ids:
        return {"added": [], "not_found": []}

    engine = self._get_engine()
    with engine.connect() as conn:
        # 1. Validate cards exist in user's collection (single query)
        card_where = "id = ANY(:ids)"
        card_params: Dict[str, Any] = {"ids": list(card_ids)}
        if user_id is not None:
            card_where += " AND user_id = :user_id"
            card_params["user_id"] = user_id

        rows = (
            conn.execute(
                text(f"SELECT id FROM cards WHERE {card_where}"),
                card_params,
            )
            .mappings()
            .fetchall()
        )
        valid_ids = {r["id"] for r in rows}
        not_found = [cid for cid in card_ids if cid not in valid_ids]

        # 2. Insert all valid cards in one transaction
        for cid in valid_ids:
            conn.execute(
                text("""
                    INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander)
                    VALUES (:deck_id, :card_id, 1, false)
                    ON CONFLICT (deck_id, card_id) DO UPDATE
                    SET quantity = deck_cards.quantity + 1
                """),
                {"deck_id": deck_id, "card_id": cid},
            )
        if valid_ids:
            conn.commit()

    return {"added": sorted(list(valid_ids)), "not_found": not_found}
```

**Notes:**
- Use `ANY(:ids)` (Postgres array binding) as already used in `find_card_ids_by_names`.
- `valid_ids` is a Python `set`, so duplicate `card_ids` in the request are implicitly deduplicated before the insert loop.
- Only call `conn.commit()` if there were inserts (guard with `if valid_ids:`).
- `is_commander` is always `false` — commander designation is handled separately via PATCH.

**Done when:**
- Method exists on `DeckRepository`.
- Calling it with an empty `card_ids` list returns `{"added": [], "not_found": []}` without touching the DB.
- Calling it with a mix of valid and invalid IDs returns only valid IDs in `added` and missing IDs in `not_found`.

**Dependencies:** None.

---

## Backend

### Task 2: Add `POST /api/decks/{id}/cards/batch` route

**File:** `backend/api/routes/decks.py`

**What to do:**

1. Add two new Pydantic models to the models section (after `DeckImportResponse`):

```python
class BatchAddCardsBody(BaseModel):
    card_ids: List[int]


class BatchAddResult(BaseModel):
    added: List[int]
    not_found: List[int]
    deck: Dict[str, Any]
```

2. Add the new route after `add_card_to_deck` (the `POST /{deck_id}/cards` handler) and before `patch_deck_card`:

```python
@router.post("/{deck_id}/cards/batch", status_code=200)
async def add_cards_to_deck_batch(
    deck_id: int,
    body: BatchAddCardsBody,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Add multiple collection cards to a deck in one request.

    Returns added/not_found id lists and the updated deck.
    Only returns 404 if the deck itself is missing; individual missing
    card IDs are reported in not_found (HTTP 200).
    """
    if not body.card_ids:
        deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
        if deck is None:
            raise HTTPException(status_code=404, detail="Deck not found")
        return {"added": [], "not_found": [], "deck": deck}

    if repo.get_by_id(deck_id, user_id=user_id) is None:
        raise HTTPException(status_code=404, detail="Deck not found")

    result = repo.add_cards_batch(deck_id, body.card_ids, user_id=user_id)
    deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
    return {"added": result["added"], "not_found": result["not_found"], "deck": deck}
```

**Notes:**
- The path `/cards/batch` is statically distinct from `/cards` and `/cards/{card_id}` — no FastAPI ordering conflict.
- Status code is `200`, not `201` — the response is a composite result, not a single newly-created resource.
- No `response_model=BatchAddResult` annotation to avoid Pydantic validation overhead on the nested `deck` dict (same pattern as other deck routes that return dicts directly).
- `require_deck_repo()` dependency automatically returns 501 when Postgres is not configured.

**Done when:**
- `POST /api/decks/1/cards/batch` with `{"card_ids": [10]}` returns 200 with `added`, `not_found`, `deck` keys.
- `POST /api/decks/999/cards/batch` returns 404.
- `POST /api/decks/1/cards/batch` with `{"card_ids": []}` returns 200 with current deck.
- The route appears in FastAPI's OpenAPI docs at `http://localhost:8000/docs`.

**Dependencies:** Task 1.

---

## Frontend

### Task 3: Add `BatchAddResult` interface and `addCardsToDeckBatch()` to API client

**File:** `frontend/src/api/client.ts`

**What to do:**

1. Add the `BatchAddResult` interface near the other deck interfaces (after `DeckImportResponse`):

```typescript
export interface BatchAddResult {
  added: number[];
  not_found: number[];
  deck: DeckWithCards;
}
```

2. Add `addCardsToDeckBatch` to the `api` object after the `addCardToDeck` method:

```typescript
addCardsToDeckBatch: async (
  deckId: number,
  cardIds: number[]
): Promise<BatchAddResult> => {
  const response = await apiFetch(`${API_BASE}/decks/${deckId}/cards/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ card_ids: cardIds }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    if (response.status === 404) throw new Error('Deck not found');
    if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
    throw new Error((err as { detail?: string }).detail || 'Failed to add cards');
  }
  return response.json();
},
```

**Notes:**
- Do not remove `addCardToDeck` — it stays for backward compat.
- The `BatchAddResult` interface must be exported so it can be imported by components if needed.
- Pattern is identical to other deck methods: `apiFetch` wrapper, `response.ok` check, structured error extraction.

**Done when:**
- TypeScript compiles without errors (`npm run build` passes).
- `api.addCardsToDeckBatch` is callable with `(deckId: number, cardIds: number[])`.
- `BatchAddResult` is exported from `client.ts`.

**Dependencies:** Task 2.

### Task 4: Replace N+1 loop in `DeckCardPickerModal` with batch call

**File:** `frontend/src/components/DeckCardPickerModal.tsx`

**What to do:**

Replace lines 82–95 (`handleAdd` callback) with a single batch call.

**Before:**
```typescript
const handleAdd = useCallback(async () => {
  if (selected.size === 0) return;
  setAddPending(true);
  try {
    for (const cardId of selected) {
      await api.addCardToDeck(deckId, cardId);
    }
    onAdded();
  } catch {
    // could toast
  } finally {
    setAddPending(false);
  }
}, [deckId, selected, onAdded]);
```

**After:**
```typescript
const handleAdd = useCallback(async () => {
  if (selected.size === 0) return;
  setAddPending(true);
  try {
    await api.addCardsToDeckBatch(deckId, Array.from(selected));
    onAdded();
  } catch {
    // could toast
  } finally {
    setAddPending(false);
  }
}, [deckId, selected, onAdded]);
```

**Notes:**
- No new imports needed — `api` is already imported from `'../api/client'`.
- `Array.from(selected)` converts the `Set<number>` to `number[]` for the payload.
- `not_found` from the response is not surfaced to the user (matches the existing `// could toast` pattern). Cards in the picker come from the user's own collection so `not_found` is empty in normal flow.
- `onAdded()` fires on success, which closes the picker and triggers `refetch()` in `DeckDetailModal`.

**Done when:**
- Selecting 3 cards and clicking "Add to Deck" produces exactly 1 network request (observable in browser DevTools Network tab).
- The picker closes and the deck updates after clicking "Add to Deck".
- TypeScript compiles without errors.

**Dependencies:** Task 3.

### Task 5: Replace duplicate `formatDeckCurrency` with shared `formatCurrency`

**File:** `frontend/src/components/DeckDetailModal.tsx`

**What to do:**

1. Add an import at the top of the file (with the other imports):
   ```typescript
   import { formatCurrency } from './analytics/constants';
   ```

2. Remove the private `formatDeckCurrency` function (lines 21–23):
   ```typescript
   // DELETE this entire function:
   function formatDeckCurrency(value: number): string {
     return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', minimumFractionDigits: 2 }).format(value);
   }
   ```

3. Update the single call site (line 313):
   ```typescript
   // Before:
   {formatDeckCurrency(totalDeckValue)}
   // After:
   {formatCurrency(totalDeckValue)}
   ```

**Notes:**
- `formatCurrency` is exported from `frontend/src/components/analytics/constants.ts`.
- Both functions produce identical output for EUR values — `Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' })` with the `es-ES` locale already outputs 2 decimal places by default.
- This is a pure refactor: no visible behavior change, just code consolidation.

**Done when:**
- `DeckDetailModal.tsx` no longer contains a private `formatDeckCurrency` function.
- The total value in the deck modal header still displays correctly (e.g. `€12,50`).
- TypeScript compiles without errors.

**Dependencies:** None (independent of Tasks 1–4).

---

## Tests

### Task 6: Add batch endpoint tests to `tests/test_decks.py`

**File:** `tests/test_decks.py`

**What to do:**

Add a new test section `# Batch card add` after the existing `# Card management` section. All tests use the existing `deck_client` fixture (module-scoped, mocked `DeckRepository` and auth).

Add these test functions:

```python
# ---------------------------------------------------------------------------
# Batch card add
# ---------------------------------------------------------------------------


def test_batch_add_cards_returns_200(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.add_cards_batch.return_value = {"added": [10, 20], "not_found": []}
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post("/api/decks/1/cards/batch", json={"card_ids": [10, 20]})

    assert response.status_code == 200
    data = response.json()
    assert data["added"] == [10, 20]
    assert data["not_found"] == []
    assert "cards" in data["deck"]


def test_batch_add_partial_not_found_returns_200(deck_client):
    """When some card_ids are not in the collection, returns 200 with not_found populated."""
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.add_cards_batch.return_value = {"added": [10], "not_found": [999]}
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post("/api/decks/1/cards/batch", json={"card_ids": [10, 999]})

    assert response.status_code == 200
    data = response.json()
    assert data["added"] == [10]
    assert data["not_found"] == [999]


def test_batch_add_deck_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = None

    response = client.post("/api/decks/999/cards/batch", json={"card_ids": [10]})

    assert response.status_code == 404


def test_batch_add_empty_card_ids_returns_current_deck(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post("/api/decks/1/cards/batch", json={"card_ids": []})

    assert response.status_code == 200
    data = response.json()
    assert data["added"] == []
    assert data["not_found"] == []
    assert "cards" in data["deck"]
    mock_repo.add_cards_batch.assert_not_called()
```

**Done when:**
- All 4 new tests pass: `pytest tests/test_decks.py -k "batch"`.
- All existing 19 tests continue to pass.

**Dependencies:** Task 2.

### Task 7: Add import endpoint tests to `tests/test_decks.py`

**File:** `tests/test_decks.py`

**What to do:**

Add a new section `# Import deck text` after the batch tests. Use the existing `deck_client` fixture.

```python
# ---------------------------------------------------------------------------
# Import deck text
# ---------------------------------------------------------------------------


def test_import_deck_matched_cards(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.find_card_ids_by_names.return_value = {"lightning bolt": 10}
    mock_repo.add_card.return_value = True
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post(
        "/api/decks/1/import",
        json={"text": "1 Lightning Bolt"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 1
    assert data["skipped_count"] == 0
    assert data["skipped"] == []
    assert "cards" in data["deck"]


def test_import_deck_unmatched_cards_skipped(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    # No matching card found
    mock_repo.find_card_ids_by_names.return_value = {}
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post(
        "/api/decks/1/import",
        json={"text": "1 Nonexistent Card"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 0
    assert data["skipped_count"] == 1
    assert data["skipped"][0]["name"] == "Nonexistent Card"
    assert data["skipped"][0]["reason"] == "not_in_collection"


def test_import_deck_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = None

    response = client.post(
        "/api/decks/999/import",
        json={"text": "1 Lightning Bolt"},
    )

    assert response.status_code == 404
```

**Notes:**
- `find_card_ids_by_names` is called with lowercased names and returns a `{name: id}` dict.
- `add_card` is called once per matched card inside the import route loop.
- These tests close the zero-coverage gap on `POST /api/decks/{id}/import`.

**Done when:**
- All 3 new tests pass: `pytest tests/test_decks.py -k "import"`.
- All existing 19 tests continue to pass.

**Dependencies:** None (tests the existing import route with no code changes).

---

## Verification Checklist

After all tasks are complete:

1. `pytest tests/test_decks.py` — all 26 tests (19 existing + 4 batch + 3 import) pass.
2. `pytest tests/test_deck_repository.py` — all 7 existing tests pass.
3. `pytest tests/` — full test suite passes with no regressions.
4. `npm run build` in `frontend/` — TypeScript compiles without errors.
5. Manual: open DeckCardPickerModal, select 5 cards, click "Add to Deck" → Network tab shows exactly 1 POST to `/api/decks/{id}/cards/batch`.
6. Manual: open DeckDetailModal → total value displays with EUR formatting (€XX,XX).
7. FastAPI docs at `http://localhost:8000/docs` show the new `POST /api/decks/{id}/cards/batch` endpoint.
