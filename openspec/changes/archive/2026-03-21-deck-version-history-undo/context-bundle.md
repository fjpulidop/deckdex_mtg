# Context Bundle: Deck Version History & Undo

This file provides the exact code patterns, file paths, and reference snippets that the developer agent needs to implement this change without additional codebase exploration.

---

## Migration Pattern

**File:** `migrations/015_card_filter_indexes.sql` (most recent migration — use 016 for the new one)

**Pattern:**
```sql
-- DeckDex MTG: <description>
-- <what it does>

CREATE TABLE IF NOT EXISTS <name> (
    id  BIGSERIAL PRIMARY KEY,
    ...
);

CREATE INDEX IF NOT EXISTS idx_<name>_<columns> ON <name> (<columns>);
```

**Apply:**
```bash
psql "$DATABASE_URL" -f migrations/016_deck_snapshots.sql
```

**Key schema references (existing tables):**
- `decks.id` — BIGSERIAL PK (FK target for `deck_snapshots.deck_id`)
- `users.id` — BIGSERIAL PK (FK target for `deck_snapshots.created_by`)
- `deck_cards (deck_id, card_id)` — composite PK, `deck_id REFERENCES decks(id) ON DELETE CASCADE`

---

## `DeckRepository` Patterns

**File:** `deckdex/storage/deck_repository.py`

**Engine acquisition pattern (use in every method):**
```python
engine = self._get_engine()
with engine.connect() as conn:
    # ... execute statements ...
    conn.commit()
```

**RETURNING pattern:**
```python
result = conn.execute(
    text("INSERT INTO ... RETURNING id, name, created_at"),
    {"param": value},
)
row = result.mappings().fetchone()
return dict(row)  # or _row_to_deck(dict(row))
```

**Ownership guard pattern (used by all deck methods):**
```python
where_clause = "id = :id"
params = {"id": deck_id}
if user_id is not None:
    where_clause += " AND user_id = :user_id"
    params["user_id"] = user_id
row = conn.execute(text(f"SELECT ... FROM decks WHERE {where_clause}"), params).mappings().fetchone()
if not row:
    return None
```

**Timestamp serializer (already in the file):**
```python
def _serialize_ts(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
```

**JSONB note:** psycopg2 + SQLAlchemy return JSONB columns as Python `list`/`dict` automatically. When reading `snapshot_data` from a query result, check `isinstance(val, list)` before calling `json.loads()`. When inserting JSONB, pass `json.dumps(python_list)` as the parameter value.

**Existing `add_card` method (lines 198–225):** The card name lookup is the pattern to extend for snapshot change_summary:
```python
# Currently:
card_exists = conn.execute(text(f"SELECT 1 FROM cards WHERE {card_where}"), card_params).fetchone()
# Extend to:
card_row = conn.execute(
    text(f"SELECT id, name FROM cards WHERE {card_where}"), card_params
).mappings().fetchone()
card_exists = card_row is not None
card_name = card_row["name"] if card_row else "Unknown"
```

---

## Backend Route Patterns

**File:** `backend/api/routes/decks.py`

**`require_deck_repo` dependency** (lines 19–26): Returns 501 when Postgres not configured. All new endpoints must use `Depends(require_deck_repo)`.

**`get_current_user_id` dependency** (from `..dependencies`): Returns `int`. All new endpoints must use `Depends(get_current_user_id)`.

**`Query` parameter import:** Add `Query` to the FastAPI import line:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
```

**Existing route registration pattern in `backend/api/main.py` (line 190):**
```python
app.include_router(decks.router)
```
No change needed here — new endpoints on `router` are automatically included.

**Error handling conventions:**
- 404: `raise HTTPException(status_code=404, detail="Deck not found")`
- 409: `raise HTTPException(status_code=409, detail=str(exc))`
- 501: handled by `require_deck_repo` automatically
- ValidationError → HTTP 400 (handled globally by `validation_exception_handler` in `main.py`)

---

## Frontend Patterns

### API client (`frontend/src/api/client.ts`)

**apiFetch wrapper:** All new API calls use `apiFetch(url, init?)` — never raw `fetch`.

**Error handling pattern (copy exactly):**
```typescript
getDeckHistory: async (deckId: number, limit = 50): Promise<DeckHistoryResponse> => {
  const response = await apiFetch(`${API_BASE}/decks/${deckId}/history?limit=${limit}`);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
    if (response.status === 404) throw new Error('Deck not found');
    throw new Error((err as { detail?: string }).detail || 'Failed to fetch deck history');
  }
  return response.json();
},
```

**Where to insert new API methods:** After `importDeckText` (line 821–834), before the `// Insights` comment block.

**Where to insert new interfaces:** After `BatchAddResult` (lines 183–187), before `ProfileUpdateBody`.

### TanStack Query patterns

**Query (read):**
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['deck-history', deckId],
  queryFn: () => api.getDeckHistory(deckId),
});
```

**Cache invalidation after mutation:**
```typescript
queryClient.setQueryData(['deck', deckId], deck);  // immediate optimistic update
await queryClient.invalidateQueries({ queryKey: ['deck-history', deckId] });
await queryClient.invalidateQueries({ queryKey: ['decks'] });
```

**No `useMutation` needed for `RevertButton`:** The revert is triggered by a user click on a specific button; local `useState(false)` for pending state is simpler and avoids shared mutation state between rows. See `DeckDetailModal.tsx` lines 227–241 (`handleSetCommander`) for the same pattern.

### AccessibleModal pattern

**File:** `frontend/src/components/AccessibleModal.tsx`

```tsx
<AccessibleModal isOpen titleId="deck-history-modal-title" onClose={onClose} className="z-[60]">
  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl ...">
    <h2 id="deck-history-modal-title">...</h2>
    ...
  </div>
</AccessibleModal>
```

**z-index stacking:** `DeckDetailModal` uses `z-50`. `DeckHistoryModal` must use `z-[60]` to stack on top.

### Conditional modal rendering pattern (from `DeckDetailModal.tsx`, lines 511–526)

```tsx
{historyOpen && (
  <DeckHistoryModal
    deckId={deckId}
    onClose={() => setHistoryOpen(false)}
    onReverted={() => {
      setHistoryOpen(false);
      refetch();
    }}
  />
)}
```

### Button style reference

**Gray secondary button** (matches Export/Import buttons in `DeckDetailModal.tsx` line 353–361):
```tsx
className="px-3 py-1.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium"
```

**Amber action button** (matches "Set as Commander" in `DeckDetailModal.tsx` line 454):
```tsx
className="px-2 py-0.5 text-xs rounded bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 hover:bg-amber-200 dark:hover:bg-amber-800/50 disabled:opacity-50"
```

### i18n pattern

**Plural keys** (follow existing pattern from `en.json` line 37–38):
```json
"diffAdded_one": "+{{count}} card",
"diffAdded_other": "+{{count}} cards"
```

**Usage in component:**
```typescript
t('deckHistory.diffAdded', { count: addedCount })
```

---

## Test Patterns

### pytest (backend/core)

**File to check first:** `tests/test_decks.py` — for existing deck test patterns.

**Key conventions:**
- All fixtures: `scope="function"` (never `scope="module"`)
- Mock `require_deck_repo` to return `MagicMock()` for HTTP-level tests
- For unit tests of `_compute_diff`: no mock needed — it is a pure function

**Import for pure function test:**
```python
from deckdex.storage.deck_repository import _compute_diff
```

### Vitest (frontend)

**Mock pattern for `api/client`:**
```typescript
vi.mock('../../api/client', () => ({
  api: {
    revertDeck: vi.fn(),
    getDeckHistory: vi.fn(),
  },
}));
```

**QueryClient wrapper for tests (established pattern):**
```typescript
function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function renderWithQuery(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={makeQueryClient()}>{ui}</QueryClientProvider>,
  );
}
```

**Existing test file to reference:** `frontend/src/components/__tests__/DeckDetailModal.test.tsx` — same structure, mocks, and render wrapper pattern to follow for `DeckHistory.test.tsx`.

---

## Key File Locations Summary

| File | Action |
|------|--------|
| `migrations/016_deck_snapshots.sql` | Create |
| `deckdex/storage/deck_repository.py` | Modify (add `_compute_diff`, `_take_snapshot`, `get_history`, `revert_to_snapshot`, `add_cards_from_import`; modify `add_card`, `remove_card`, `set_commander`, `add_cards_batch`) |
| `backend/api/routes/decks.py` | Modify (add Pydantic models, 2 new routes; modify `import_deck_text`) |
| `frontend/src/api/client.ts` | Modify (add 5 interfaces, 2 API methods) |
| `frontend/src/locales/en.json` | Modify (add `deckHistory` namespace + `deckDetail.history` key) |
| `frontend/src/locales/es.json` | Modify (add `deckHistory` namespace + `deckDetail.history` key) |
| `frontend/src/components/RevertButton.tsx` | Create |
| `frontend/src/components/DeckHistoryTimeline.tsx` | Create |
| `frontend/src/components/DeckHistoryModal.tsx` | Create |
| `frontend/src/components/DeckDetailModal.tsx` | Modify (import + state + button + modal render) |
| `tests/test_deck_snapshots.py` | Create |
| `frontend/src/components/__tests__/DeckHistory.test.tsx` | Create |

---

## Ambiguity Resolution

**Snapshot on create/delete/rename?**
Not required. `create` produces an empty deck (no cards to snapshot). `delete` cascades to `deck_snapshots` via FK. `update_name` (rename) is not a card mutation and does not need a snapshot. Only card-level mutations are snapshotted.

**What if `user_id` is None in snapshot calls?**
Skip snapshot creation silently. In practice, all deck routes require `get_current_user_id` so `user_id` is always an int at the route level. The guard is defensive.

**Snapshot on `set_commander` — is this useful?**
Yes. Setting a commander changes the deck's identity significantly for Commander format. Reverting to a pre-commander-change state is a valid use case.

**What is the "most recent" snapshot?**
The snapshot at `ORDER BY created_at DESC LIMIT 1`. The most recent snapshot always represents the current deck state. The "Current version" label appears on `snapshots[0]` in the timeline and its `RevertButton` is disabled (reverting to the current state is a no-op).

**FK violation on revert (card deleted from collection):**
Return HTTP 409 from the route. The `ValueError` raised by `revert_to_snapshot` carries the card name so the user can see which card is missing. The frontend `RevertButton` checks if the error message contains "no longer exists" and shows the `deckHistory.revertCardMissing` i18n key instead of the raw error.
