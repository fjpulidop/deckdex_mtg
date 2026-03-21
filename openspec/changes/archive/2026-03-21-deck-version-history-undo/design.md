# Technical Design: Deck Version History & Undo

## Overview

Each mutating deck operation writes a snapshot of the post-mutation deck state to `deck_snapshots`. The snapshot stores the full card list as JSONB so diffs can be computed without joining additional tables. History retrieval computes diffs on the fly by comparing adjacent snapshots. Revert replaces `deck_cards` with the snapshot state and records a new snapshot.

---

## Database Schema

### New table: `deck_snapshots`

```sql
CREATE TABLE IF NOT EXISTS deck_snapshots (
    id          BIGSERIAL PRIMARY KEY,
    deck_id     BIGINT NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    created_by  BIGINT NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    snapshot_data JSONB NOT NULL,
    change_summary TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_deck_snapshots_deck_id_created_at
    ON deck_snapshots (deck_id, created_at DESC);
```

**Column notes:**

- `snapshot_data`: Full array of `{card_id, name, quantity, is_commander}` objects at the time of the snapshot. Denormalizes `name` so diffs are self-contained even if a card is later deleted from the collection.
- `change_summary`: Human-readable one-line description of the operation that triggered this snapshot, e.g. `"Added 2x Lightning Bolt"`, `"Reverted to snapshot #42"`, `"Imported 15 cards"`. Generated at write time by the repository method.
- `created_by`: User who performed the action (user_id from JWT). Enables future per-user audit trail.
- `ON DELETE CASCADE`: Snapshots are subordinate to the deck; deleting a deck removes all its history.

**Why JSONB for snapshot_data and not a relational cards table:**
Storing a point-in-time snapshot relationally would require a `snapshot_cards` join table and make diff queries complex. JSONB lets us read the full snapshot in a single row scan and compute diffs in Python, which keeps the SQL simple and avoids schema explosion. Snapshot data is write-once (immutable after insert), so JSONB update anomalies are not a concern.

---

## Core Layer: `deckdex/storage/deck_repository.py`

### New private helper: `_take_snapshot`

```python
def _take_snapshot(
    self,
    conn,  # active SQLAlchemy connection
    deck_id: int,
    user_id: int,
    change_summary: str,
) -> int:
    """Insert a snapshot of the current deck_cards state. Returns snapshot id."""
```

This helper runs inside the same connection that performed the mutation, so it participates in the same transaction. It reads the current `deck_cards` joined with `cards` to capture `{card_id, name, quantity, is_commander}`, then inserts into `deck_snapshots`.

**Called after (not before) each mutation** so the snapshot reflects the post-operation state. This is the correct semantic: snapshot #1 = "deck after operation #1".

### Mutations that trigger snapshots

All existing `DeckRepository` methods that mutate `deck_cards` must call `_take_snapshot` at the end of their transaction, before `conn.commit()`:

| Method | `change_summary` template |
|--------|--------------------------|
| `add_card` | `"Added {quantity}x {card_name}"` |
| `remove_card` | `"Removed {card_name}"` |
| `add_cards_batch` | `"Added {n} card(s) in batch"` |
| `set_commander` | `"Set {card_name} as commander"` |
| `find_card_ids_by_names` (called from import route) | n/a — import is handled at route level; see below |

**Import special case:** The import route (`POST /api/decks/{id}/import`) calls `repo.add_card` in a loop. Snapshotting every individual add would produce noisy history. Instead, the import route calls a new repository method `add_cards_from_import(deck_id, cards_list, user_id, change_summary)` that wraps all additions in a single transaction and takes one snapshot at the end. The existing route in `decks.py` must be updated to call this new method.

### New repository methods

#### `get_history(deck_id, user_id, limit=50) -> List[Dict]`

Returns snapshots ordered newest-first. Computes diff by comparing each snapshot's `snapshot_data` against the previous snapshot (or empty state for the first). Returns:

```python
[
  {
    "id": int,
    "created_at": str,  # ISO
    "created_by": int,
    "change_summary": str,
    "diff": {
        "added": [{"card_id": int, "name": str, "quantity": int}],
        "removed": [{"card_id": int, "name": str, "quantity": int}],
        "quantity_changed": [{"card_id": int, "name": str, "old_quantity": int, "new_quantity": int}],
        "commander_changed": Optional[str],  # card name set as commander, if changed
    }
  },
  ...
]
```

Diff algorithm (pure Python, no SQL):
1. Fetch the `limit+1` most recent snapshots for the deck (extra entry gives context for the oldest diff).
2. For each snapshot i, compare `snapshot_data[i]` with `snapshot_data[i+1]` (or empty list for the last).
3. Build sets of `card_id → {quantity, is_commander}` for each side and compute set differences.

#### `revert_to_snapshot(deck_id, snapshot_id, user_id) -> Optional[Dict]`

1. Verify deck ownership.
2. Load snapshot row; verify it belongs to the same deck.
3. In a single transaction:
   a. `DELETE FROM deck_cards WHERE deck_id = :deck_id`
   b. `INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander)` for each entry in `snapshot_data`
   c. Call `_take_snapshot` with `change_summary = f"Reverted to snapshot #{snapshot_id}"`
4. Return the updated deck (via `get_deck_with_cards`).

**Important:** Step (b) inserts by `card_id`. If a card was deleted from the collection after the snapshot was taken, the INSERT will fail with a foreign key violation. The method should catch this and return a 409 response (card no longer in collection). The route handler converts this to HTTP 409 with a descriptive message.

---

## API Layer: `backend/api/routes/decks.py`

### New Pydantic models

```python
class SnapshotDiffCard(BaseModel):
    card_id: int
    name: str
    quantity: int

class SnapshotDiffQuantityChange(BaseModel):
    card_id: int
    name: str
    old_quantity: int
    new_quantity: int

class SnapshotDiff(BaseModel):
    added: List[SnapshotDiffCard]
    removed: List[SnapshotDiffCard]
    quantity_changed: List[SnapshotDiffQuantityChange]
    commander_changed: Optional[str] = None

class DeckSnapshot(BaseModel):
    id: int
    created_at: str
    created_by: int
    change_summary: str
    diff: SnapshotDiff

class DeckHistoryResponse(BaseModel):
    deck_id: int
    snapshots: List[DeckSnapshot]
```

### New endpoints

#### `GET /api/decks/{deck_id}/history`

```
GET /api/decks/{deck_id}/history?limit=50
Authorization: JWT cookie required
```

- Requires `get_current_user_id`
- Calls `repo.get_history(deck_id, user_id, limit=limit)`
- Returns `DeckHistoryResponse`
- 404 if deck not found or not owned by user
- 501 if Postgres not configured

**Query param:** `limit` (int, default 50, max 200). Validated via Pydantic `Query`.

#### `POST /api/decks/{deck_id}/revert/{snapshot_id}`

```
POST /api/decks/{deck_id}/revert/{snapshot_id}
Authorization: JWT cookie required
```

- Requires `get_current_user_id`
- Calls `repo.revert_to_snapshot(deck_id, snapshot_id, user_id)`
- Returns the full updated `DeckWithCards` (same shape as `GET /api/decks/{id}`)
- 404 if deck or snapshot not found / wrong owner
- 409 if a card in the snapshot no longer exists in the collection
- 501 if Postgres not configured

**Why POST not PATCH:** Revert is a named action that creates a new snapshot. POST on a sub-resource (`/revert/{id}`) follows the existing pattern of `/import`, `/cards/batch` etc. in this codebase.

### Modification to existing import route

Replace the card-by-card `repo.add_card` loop in `import_deck_text` with a call to the new `repo.add_cards_from_import(...)`. This collapses the snapshot granularity from N-per-import to 1-per-import.

---

## Frontend Layer

### `frontend/src/api/client.ts`

Add two new interfaces and two new `api` methods:

```typescript
export interface SnapshotDiffCard {
  card_id: number;
  name: string;
  quantity: number;
}

export interface SnapshotDiffQuantityChange {
  card_id: number;
  name: string;
  old_quantity: number;
  new_quantity: number;
}

export interface SnapshotDiff {
  added: SnapshotDiffCard[];
  removed: SnapshotDiffCard[];
  quantity_changed: SnapshotDiffQuantityChange[];
  commander_changed: string | null;
}

export interface DeckSnapshot {
  id: number;
  created_at: string;
  created_by: number;
  change_summary: string;
  diff: SnapshotDiff;
}

export interface DeckHistoryResponse {
  deck_id: number;
  snapshots: DeckSnapshot[];
}
```

```typescript
getDeckHistory: async (deckId: number, limit = 50): Promise<DeckHistoryResponse> => { ... }
revertDeck: async (deckId: number, snapshotId: number): Promise<DeckWithCards> => { ... }
```

### New component: `frontend/src/components/DeckHistoryModal.tsx`

A modal that wraps the timeline. Follows the `AccessibleModal` pattern established throughout the codebase.

Props:
```typescript
interface DeckHistoryModalProps {
  deckId: number;
  onClose: () => void;
  onReverted: () => void;  // called after successful revert to refresh deck view
}
```

Internals:
- Uses `useQuery({ queryKey: ['deck-history', deckId], queryFn: () => api.getDeckHistory(deckId) })`
- Renders `DeckHistoryTimeline` passing the snapshot list
- Uses `useMutation` for revert, invalidates `['deck', deckId]` and `['deck-history', deckId]` on success, then calls `onReverted()`
- Shows loading state and error state inline (not a separate component)

### New component: `frontend/src/components/DeckHistoryTimeline.tsx`

Renders the ordered list of snapshots. Each row is a `SnapshotRow` (inline sub-component or extracted if it grows complex).

Each row displays:
- Relative timestamp (e.g., "2 hours ago") using `Intl.RelativeTimeFormat` — no external date library dependency
- `change_summary` text
- Diff summary inline: "+ 2 cards, - 1 card" in muted text
- `RevertButton` (disabled for the most recent snapshot since it would be a no-op)

### New component: `frontend/src/components/RevertButton.tsx`

A small stateful button handling the revert mutation. Receives:
```typescript
interface RevertButtonProps {
  deckId: number;
  snapshotId: number;
  onReverted: () => void;
  disabled?: boolean;
}
```

Uses `useMutation` for the revert call. Shows loading text while pending. Shows error toast inline (or sets error state) on failure.

**Why a separate component for `RevertButton`:** Each row needs independent loading/error state. Extracting the button isolates mutation state per row, avoiding lifting state to the parent timeline.

### Modification to `frontend/src/components/DeckDetailModal.tsx`

Add a "History" button to the action bar in the modal header (alongside the existing Export, Import, Add card, Delete buttons):

```tsx
<button
  type="button"
  onClick={() => setHistoryOpen(true)}
  className="px-3 py-1.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium"
>
  {t('deckDetail.history')}
</button>
```

Add state: `const [historyOpen, setHistoryOpen] = useState(false)`

Render conditionally at the bottom of the component (same pattern as `pickerOpen`, `importOpen`):
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

---

## Integration Points

### Snapshot trigger locations

All snapshot writes go through `DeckRepository` methods, not route handlers. This ensures:
- No snapshot is missed regardless of which route triggers the mutation
- Snapshot logic is unit-testable independently of HTTP layer
- A future CLI operation that calls `DeckRepository` directly also produces snapshots

### Transaction integrity

`_take_snapshot` runs inside the caller's open connection before `conn.commit()`. If the snapshot INSERT fails (e.g., disk full), the whole transaction rolls back and the mutation is not committed. This is the correct behavior: we never want a mutation without a corresponding snapshot.

### Query key design

| Data | TanStack Query key |
|------|--------------------|
| Deck detail | `['deck', deckId]` |
| Deck history | `['deck-history', deckId]` |
| Deck list | `['decks']` |

After a revert, invalidate `['deck', deckId]` and `['deck-history', deckId]`. The deck list does not need invalidation (revert does not change the deck name or card count in a way that affects the grid — though it does change card count; optionally invalidate `['decks']` as well for correctness).

---

## Diff Algorithm Detail

```python
def _compute_diff(
    before: List[Dict],  # snapshot_data from older snapshot (or [])
    after: List[Dict],   # snapshot_data from newer snapshot
) -> Dict:
    before_map = {e["card_id"]: e for e in before}
    after_map = {e["card_id"]: e for e in after}

    added = []
    removed = []
    quantity_changed = []
    commander_before = next((e["name"] for e in before if e["is_commander"]), None)
    commander_after = next((e["name"] for e in after if e["is_commander"]), None)

    for card_id, entry in after_map.items():
        if card_id not in before_map:
            added.append({"card_id": card_id, "name": entry["name"], "quantity": entry["quantity"]})
        elif entry["quantity"] != before_map[card_id]["quantity"]:
            quantity_changed.append({
                "card_id": card_id,
                "name": entry["name"],
                "old_quantity": before_map[card_id]["quantity"],
                "new_quantity": entry["quantity"],
            })

    for card_id, entry in before_map.items():
        if card_id not in after_map:
            removed.append({"card_id": card_id, "name": entry["name"], "quantity": entry["quantity"]})

    return {
        "added": added,
        "removed": removed,
        "quantity_changed": quantity_changed,
        "commander_changed": commander_after if commander_after != commander_before else None,
    }
```

This runs in O(n) where n is the number of distinct cards in a deck (practical max ~100 for Commander). No performance concern.
