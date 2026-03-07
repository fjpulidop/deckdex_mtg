# Design: Batch Card Add for Decks + Currency Fix

## Impact Analysis

| Layer | File | Change |
|---|---|---|
| Core | `deckdex/storage/deck_repository.py` | Add `add_cards_batch()` method |
| Backend | `backend/api/routes/decks.py` | Add `POST /api/decks/{id}/cards/batch` route + Pydantic models |
| Frontend API | `frontend/src/api/client.ts` | Add `addCardsToDeckBatch()` method; add `BatchAddResult` interface |
| Frontend UI | `frontend/src/components/DeckCardPickerModal.tsx` | Replace sequential loop with single batch call |
| Frontend UI | `frontend/src/components/DeckDetailModal.tsx` | Replace private duplicate `formatDeckCurrency` with shared `formatCurrency` from `analytics/constants.ts` |
| Tests | `tests/test_decks.py` | 4 new test functions for batch endpoint + 3 new functions for import endpoint |

No DB migrations are needed. `add_cards_batch` reuses the existing `deck_cards` table and the `ON CONFLICT` upsert logic already present in `add_card`.

---

## Detailed Design

### 1. Core: `DeckRepository.add_cards_batch()`

**File:** `deckdex/storage/deck_repository.py`

**Signature:**
```python
def add_cards_batch(
    self,
    deck_id: int,
    card_ids: List[int],
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
```

**Return type:** A summary dict:
```python
{
    "added": [<card_id>, ...],      # card_ids successfully added/upserted
    "not_found": [<card_id>, ...],  # card_ids absent from user's collection
}
```

**Algorithm:**

1. Early return for empty input: `if not card_ids: return {"added": [], "not_found": []}`.

2. Validate which `card_ids` exist in the user's collection via a single query:
   ```sql
   SELECT id FROM cards WHERE id = ANY(:ids) [AND user_id = :user_id]
   ```
   This uses the `ANY()` Postgres array operator already present in `find_card_ids_by_names`. Computes `valid_ids = set of returned IDs`, `not_found = [cid for cid in card_ids if cid not in valid_ids]`.

3. For each `card_id` in `valid_ids`, execute an `INSERT ... ON CONFLICT DO UPDATE` within **one connection/transaction**:
   ```sql
   INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander)
   VALUES (:deck_id, :card_id, 1, false)
   ON CONFLICT (deck_id, card_id) DO UPDATE
   SET quantity = deck_cards.quantity + 1
   ```
   Then `conn.commit()` once after all inserts. **Rationale:** One commit = atomic batch — all cards added or none (if the connection drops mid-loop). Iterating `valid_ids` (a Python `set`) naturally deduplicates duplicate `card_ids` in the request.

4. Return `{"added": sorted(list(valid_ids)), "not_found": not_found}`.

**Design decision — is_commander in batch:** Always `false`. Commander designation is handled separately via `PATCH /api/decks/{id}/cards/{card_id}`. Including `is_commander` in the batch payload would complicate the model without product value (the picker flow does not require it).

**Design decision — quantity on conflict:** Increment by 1, matching the existing single-card `add_card` behaviour (same `ON CONFLICT DO UPDATE` clause). This keeps the two code paths semantically consistent.

**Design decision — deck existence check at route layer:** The route calls `repo.get_by_id(deck_id, user_id)` before calling `add_cards_batch`, matching the pattern in `add_card_to_deck`. The repository method does not re-verify deck ownership; it trusts the route to do that gate check first.

---

### 2. Backend: `POST /api/decks/{id}/cards/batch`

**File:** `backend/api/routes/decks.py`

**New Pydantic models** (add to the existing models section):
```python
class BatchAddCardsBody(BaseModel):
    card_ids: List[int]

class BatchAddResult(BaseModel):
    added: List[int]
    not_found: List[int]
    deck: Dict[str, Any]
```

**Route** (place after `add_card_to_deck` and before `patch_deck_card` to follow static-before-parameterized ordering — `/cards/batch` is a distinct static path that doesn't conflict with `/{card_id}`):
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
    Cards absent from the user's collection are reported in not_found
    (no 404 raised for individual missing cards — only for missing deck).
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

**Status code:** `200` — not `201`. The response is a composite result (added list + not_found list + full deck), not a single newly-created resource. `201` would be semantically wrong when some cards are already present (upserted) or none were added.

**Error semantics:**
- `404` only if the deck is not found or doesn't belong to the user.
- `200` even if `not_found` is non-empty — partial success is success; the caller decides how to handle skipped IDs.
- `501` handled automatically by `require_deck_repo()` when Postgres is not configured.
- Empty `card_ids`: returns `200` with current deck state, no DB writes.

---

### 3. Frontend API Client

**File:** `frontend/src/api/client.ts`

**New interface** (add near the existing deck types, e.g. after `DeckImportResponse`):
```typescript
export interface BatchAddResult {
  added: number[];
  not_found: number[];
  deck: DeckWithCards;
}
```

**New method** (add after `addCardToDeck`):
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

Pattern is identical to `addCardToDeck`, `importDeckText`, and other deck methods: `apiFetch` wrapper, structured error extraction, typed return. The existing `addCardToDeck` method is left untouched for backward compatibility.

---

### 4. Frontend: DeckCardPickerModal — replace N+1 with batch

**File:** `frontend/src/components/DeckCardPickerModal.tsx`

**Current `handleAdd` (lines 82–95) — the N+1 pattern:**
```typescript
const handleAdd = useCallback(async () => {
  if (selected.size === 0) return;
  setAddPending(true);
  try {
    for (const cardId of selected) {   // N sequential awaits
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

**Replacement — single batch call:**
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

**`not_found` handling:** Silently ignored, matching the `// could toast` pattern used throughout the deck modals. Cards shown in the picker are sourced from the user's own collection (`GET /api/cards`), so `not_found` will be empty in normal operation. If a toast system is added later, log `result.not_found` here.

**Import statement change:** The import of `api` is unchanged. No new imports needed — `addCardsToDeckBatch` is on the existing `api` object.

---

### 5. Frontend: DeckDetailModal — eliminate duplicate currency formatter

**File:** `frontend/src/components/DeckDetailModal.tsx`

**Investigation result:** The app has no user-configurable currency setting. `frontend/src/components/analytics/constants.ts` exports `formatCurrency(value: number): string` which uses `Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' })` — identical logic to `formatDeckCurrency` in `DeckDetailModal.tsx` (line 21–23), except the deck version adds `minimumFractionDigits: 2`. The rest of the app (analytics, stats) uses the shared constant.

**Fix:** Remove the private `formatDeckCurrency` function from `DeckDetailModal.tsx` and import `formatCurrency` from `analytics/constants.ts` instead. Update the one call site (line 313) to use `formatCurrency(totalDeckValue)`.

**Before:**
```typescript
// DeckDetailModal.tsx lines 21–23 (private duplicate)
function formatDeckCurrency(value: number): string {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', minimumFractionDigits: 2 }).format(value);
}
// ...
{formatDeckCurrency(totalDeckValue)}
```

**After:**
```typescript
// Add to imports at top of DeckDetailModal.tsx:
import { formatCurrency } from './analytics/constants';
// Remove the private formatDeckCurrency function entirely.
// Update call site:
{formatCurrency(totalDeckValue)}
```

**Design decision — why not add `minimumFractionDigits: 2` to shared function:** The shared `formatCurrency` in `analytics/constants.ts` produces the same output for non-trivial values. EUR with `es-ES` locale already displays 2 decimal places by default from `Intl.NumberFormat`. The `minimumFractionDigits: 2` in the deck version is redundant. Using the shared function unifies the display and reduces duplication.

**Design decision — no new settings API:** The app does not currently expose a user-configurable currency preference. Adding one would require backend schema changes, a settings endpoint, and UI — well beyond the scope of this fix. The correct action is consolidation around the existing hardcoded EUR standard, not inventing new API surface.

---

### Data Flow: Batch Add

```
User selects N cards in DeckCardPickerModal
  → clicks "Add to Deck"
  → handleAdd fires
  → api.addCardsToDeckBatch(deckId, [id1, id2, ..., idN])
      POST /api/decks/{deck_id}/cards/batch  { "card_ids": [id1, ..., idN] }
          require_deck_repo()   → 501 if no Postgres
          get_current_user_id() → user_id
          repo.get_by_id(deck_id, user_id) → 404 if deck missing
          repo.add_cards_batch(deck_id, card_ids, user_id)
              SELECT id FROM cards WHERE id = ANY(:ids) AND user_id = :user_id
              for cid in valid_ids:
                  INSERT INTO deck_cards ... ON CONFLICT DO UPDATE SET quantity = quantity + 1
              conn.commit()
              → { added: [...], not_found: [...] }
          repo.get_deck_with_cards(deck_id, user_id)
          → 200 { added, not_found, deck }
  → onAdded() closes picker, triggers deck data refetch in DeckDetailModal
```

---

## Risks and Edge Cases

**Empty card_ids:** Handled explicitly — 200 with current deck, no DB writes.

**All cards not in collection:** `added=[]`, `not_found=[all IDs]`, deck unchanged. `onAdded()` fires, deck refetches (no-op diff). Harmless.

**Deck not found:** 404 before any DB writes. Consistent with single-card endpoint.

**Duplicate card_ids in request:** `valid_ids` is a Python `set`, so duplicates are deduplicated before the insert loop. The `ON CONFLICT DO UPDATE` would handle them anyway, but deduplication avoids redundant DB round-trips.

**Large selections:** No explicit limit. For MTG deck sizes (60–100 cards) the `ANY(:ids)` query and bounded insert loop are well within Postgres capacity.

**Route ordering:** `/cards/batch` is a statically-distinct path from `/cards` (the single-add endpoint) and `/cards/{card_id}` (patch/delete). FastAPI matches paths correctly. No ordering fix needed.

**Concurrency with Google Sheets mode:** Not applicable. All deck endpoints require Postgres via `require_deck_repo()`.

**`formatCurrency` import path:** `DeckDetailModal.tsx` is in `frontend/src/components/`. The shared function is in `frontend/src/components/analytics/constants.ts`. The relative import path is `'./analytics/constants'`.
