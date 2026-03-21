# Tasks: Deck Version History & Undo

Ordered, atomic tasks. Dependencies are noted per task. Execute in the order shown.

---

## Task 1 — Database migration: `deck_snapshots` table

**Layer:** [backend]
**Depends on:** nothing

**Files:**
- Create: `migrations/016_deck_snapshots.sql`

**Description:**

Create the migration file with the following content:

```sql
-- DeckDex MTG: deck_snapshots table for version history and undo
-- Stores full deck card state after each mutating operation.
-- snapshot_data is a JSONB array of {card_id, name, quantity, is_commander}.

CREATE TABLE IF NOT EXISTS deck_snapshots (
    id            BIGSERIAL PRIMARY KEY,
    deck_id       BIGINT NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    created_by    BIGINT NOT NULL REFERENCES users(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    snapshot_data JSONB NOT NULL,
    change_summary TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_deck_snapshots_deck_id_created_at
    ON deck_snapshots (deck_id, created_at DESC);
```

Apply the migration to verify syntax:
```bash
psql "$DATABASE_URL" -f migrations/016_deck_snapshots.sql
```

**Acceptance criteria:**
- [ ] File `migrations/016_deck_snapshots.sql` exists
- [ ] Table `deck_snapshots` created with correct columns and types
- [ ] Index `idx_deck_snapshots_deck_id_created_at` created
- [ ] Migration is idempotent (`IF NOT EXISTS` on both table and index)
- [ ] Running the migration a second time produces no error

---

## Task 2 — Core: `_take_snapshot` helper and `_compute_diff` function in `DeckRepository`

**Layer:** [core]
**Depends on:** Task 1 (table must exist for integration tests)

**Files:**
- Modify: `deckdex/storage/deck_repository.py`

**Description:**

Add the following to `deck_repository.py`:

**1. Import addition at top:**
```python
import json
```

**2. Module-level diff function (outside the class):**

```python
def _compute_diff(
    before: List[Dict[str, Any]],
    after: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute card-level diff between two snapshot_data lists.

    Args:
        before: snapshot_data from the older snapshot, or [] for the initial state.
        after: snapshot_data from the newer snapshot.

    Returns:
        Dict with keys: added, removed, quantity_changed, commander_changed.
    """
    before_map: Dict[int, Dict[str, Any]] = {e["card_id"]: e for e in before}
    after_map: Dict[int, Dict[str, Any]] = {e["card_id"]: e for e in after}

    added: List[Dict[str, Any]] = []
    removed: List[Dict[str, Any]] = []
    quantity_changed: List[Dict[str, Any]] = []

    commander_before: Optional[str] = next(
        (e["name"] for e in before if e.get("is_commander")), None
    )
    commander_after: Optional[str] = next(
        (e["name"] for e in after if e.get("is_commander")), None
    )

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

**3. Private `_take_snapshot` method on `DeckRepository`:**

```python
def _take_snapshot(
    self,
    conn: Any,
    deck_id: int,
    user_id: int,
    change_summary: str,
) -> int:
    """Capture the current deck_cards state as a snapshot.

    Must be called inside an open connection BEFORE conn.commit().
    Returns the new snapshot id.
    """
    from sqlalchemy import text

    rows = (
        conn.execute(
            text("""
                SELECT dc.card_id, c.name, dc.quantity, dc.is_commander
                FROM deck_cards dc
                JOIN cards c ON c.id = dc.card_id
                WHERE dc.deck_id = :deck_id
                ORDER BY dc.card_id
            """),
            {"deck_id": deck_id},
        )
        .mappings()
        .fetchall()
    )
    snapshot_data = [
        {
            "card_id": r["card_id"],
            "name": r["name"],
            "quantity": r["quantity"],
            "is_commander": bool(r["is_commander"]),
        }
        for r in rows
    ]
    result = conn.execute(
        text("""
            INSERT INTO deck_snapshots (deck_id, created_by, snapshot_data, change_summary)
            VALUES (:deck_id, :created_by, :snapshot_data, :change_summary)
            RETURNING id
        """),
        {
            "deck_id": deck_id,
            "created_by": user_id,
            "snapshot_data": json.dumps(snapshot_data),
            "change_summary": change_summary,
        },
    )
    row = result.mappings().fetchone()
    return row["id"]
```

**Acceptance criteria:**
- [ ] `_compute_diff` is a module-level function (not a method) in `deck_repository.py`
- [ ] `_take_snapshot` is a private method on `DeckRepository`
- [ ] `_take_snapshot` reads current `deck_cards` joined with `cards` for card names
- [ ] `_take_snapshot` inserts a row into `deck_snapshots` and returns the new `id`
- [ ] `_compute_diff` handles empty `before` list (first snapshot)
- [ ] `_compute_diff` detects commander changes correctly

---

## Task 3 — Core: wire snapshots into existing `DeckRepository` mutations

**Layer:** [core]
**Depends on:** Task 2

**Files:**
- Modify: `deckdex/storage/deck_repository.py`

**Description:**

Modify four existing `DeckRepository` methods to call `self._take_snapshot(conn, deck_id, user_id, ...)` inside the same transaction, before `conn.commit()`. The `user_id` parameter must be passed through — all four methods already accept `user_id: Optional[int]`. When `user_id` is None, skip snapshot creation (backward compatibility for any non-authenticated path, though in practice the API always provides `user_id`).

**`add_card` — change summary: `"Added {quantity}x {card_name}"`**

Read the card name before the upsert (or derive it from the lookup query that already runs). Add the snapshot call before `conn.commit()`. The card name can be obtained by adding `SELECT name FROM cards WHERE id = :card_id` or reusing the `card_exists` check by fetching `name` alongside `1`.

Change the existing check query:
```python
# Before:
card_exists = conn.execute(text(f"SELECT 1 FROM cards WHERE {card_where}"), card_params).fetchone()
# After:
card_row = conn.execute(
    text(f"SELECT id, name FROM cards WHERE {card_where}"), card_params
).mappings().fetchone()
card_exists = card_row is not None
card_name = card_row["name"] if card_row else "Unknown"
```

Then after the upsert, before `conn.commit()`:
```python
if user_id is not None:
    self._take_snapshot(
        conn, deck_id, user_id,
        f"Added {quantity}x {card_name}"
    )
conn.commit()
```

**`remove_card` — change summary: `"Removed {card_name}"`**

Fetch card name before delete using `SELECT name FROM cards WHERE id = :card_id`. Add snapshot call before `conn.commit()`:
```python
card_name_row = conn.execute(
    text("SELECT name FROM cards WHERE id = :card_id"), {"card_id": card_id}
).mappings().fetchone()
card_name = card_name_row["name"] if card_name_row else f"card {card_id}"
# ... existing DELETE ...
if user_id is not None:
    self._take_snapshot(conn, deck_id, user_id, f"Removed {card_name}")
conn.commit()
```

**`set_commander` — change summary: `"Set {card_name} as commander"`**

Fetch card name after confirming the card is in the deck. Add snapshot before `conn.commit()`:
```python
card_name_row = conn.execute(
    text("SELECT name FROM cards WHERE id = :card_id"), {"card_id": card_id}
).mappings().fetchone()
card_name = card_name_row["name"] if card_name_row else f"card {card_id}"
# ... existing UPDATE statements ...
if user_id is not None:
    self._take_snapshot(conn, deck_id, user_id, f"Set {card_name} as commander")
conn.commit()
```

**`add_cards_batch` — change summary: `"Added {n} card(s) in batch"`**

After all INSERT statements, before `conn.commit()` at the end:
```python
if valid_ids and user_id is not None:
    self._take_snapshot(
        conn, deck_id, user_id,
        f"Added {len(valid_ids)} card(s) in batch"
    )
if valid_ids:
    conn.commit()
```

**Note on `add_cards_batch` transaction structure:** The current code uses `conn.commit()` only when `valid_ids` is non-empty. The snapshot should follow the same condition.

**Acceptance criteria:**
- [ ] `add_card` writes a snapshot after a successful add
- [ ] `remove_card` writes a snapshot after a successful remove
- [ ] `set_commander` writes a snapshot after setting the commander
- [ ] `add_cards_batch` writes one snapshot after all batch inserts
- [ ] No snapshot is written when `user_id` is None
- [ ] Snapshot is always written inside the same connection/transaction as the mutation
- [ ] `conn.commit()` always follows `_take_snapshot`, never precedes it

---

## Task 4 — Core: new `add_cards_from_import` method on `DeckRepository`

**Layer:** [core]
**Depends on:** Task 3

**Files:**
- Modify: `deckdex/storage/deck_repository.py`

**Description:**

The import route currently calls `repo.add_card` in a loop (one card at a time, each with its own commit). This produces N snapshots for an N-card import. Replace with a single-transaction method that produces one snapshot.

Add the following method to `DeckRepository`:

```python
def add_cards_from_import(
    self,
    deck_id: int,
    cards: List[Dict[str, Any]],
    user_id: Optional[int] = None,
    imported_count: int = 0,
) -> None:
    """Add cards from a parsed deck import in a single transaction.

    Args:
        deck_id: Target deck id.
        cards: List of dicts with keys: card_id (int), quantity (int), is_commander (bool).
               All card_ids must already be validated to exist in the user's collection.
        user_id: Authenticated user id. Required for snapshot creation.
        imported_count: Number of cards imported (used in change_summary).
    """
    from sqlalchemy import text

    if not cards:
        return

    engine = self._get_engine()
    with engine.connect() as conn:
        for card in cards:
            conn.execute(
                text("""
                    INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander)
                    VALUES (:deck_id, :card_id, :quantity, :is_commander)
                    ON CONFLICT (deck_id, card_id) DO UPDATE
                    SET quantity = deck_cards.quantity + EXCLUDED.quantity,
                        is_commander = EXCLUDED.is_commander
                """),
                {
                    "deck_id": deck_id,
                    "card_id": card["card_id"],
                    "quantity": card["quantity"],
                    "is_commander": card["is_commander"],
                },
            )
        if user_id is not None:
            self._take_snapshot(
                conn, deck_id, user_id,
                f"Imported {imported_count} card(s)"
            )
        conn.commit()
```

**Acceptance criteria:**
- [ ] Method `add_cards_from_import` added to `DeckRepository`
- [ ] All inserts happen in one transaction (single `conn.commit()`)
- [ ] One snapshot is created after all inserts
- [ ] Method is safe to call with an empty `cards` list (no-op)

---

## Task 5 — Backend: update import route to use `add_cards_from_import`

**Layer:** [backend]
**Depends on:** Task 4

**Files:**
- Modify: `backend/api/routes/decks.py`

**Description:**

In `import_deck_text`, replace the per-card `repo.add_card` loop with a call to `repo.add_cards_from_import`. The name resolution logic remains unchanged.

Find the loop (approximately lines 240–262):
```python
for card in parsed_cards:
    lower_name = card["name"].lower()
    card_id = name_to_id.get(lower_name)
    if card_id is None:
        skipped.append(...)
        continue
    repo.add_card(deck_id, card_id, ...)
    imported_count += 1
```

Replace with:
```python
cards_to_import = []
for card in parsed_cards:
    lower_name = card["name"].lower()
    card_id = name_to_id.get(lower_name)
    if card_id is None:
        skipped.append(
            DeckImportSkippedCard(
                name=card["name"],
                quantity=card["quantity"],
                reason="not_in_collection",
            )
        )
        continue
    cards_to_import.append({
        "card_id": card_id,
        "quantity": card["quantity"],
        "is_commander": card["is_commander"],
    })
    imported_count += 1

repo.add_cards_from_import(
    deck_id,
    cards_to_import,
    user_id=user_id,
    imported_count=imported_count,
)
```

**Acceptance criteria:**
- [ ] Import route no longer calls `repo.add_card` in a loop
- [ ] Import route calls `repo.add_cards_from_import` once
- [ ] `imported_count` is still computed correctly (count of matched cards)
- [ ] `skipped` list is still built correctly
- [ ] Response shape is unchanged (`DeckImportResponse`)
- [ ] Manual test: import a deck list and verify only one snapshot appears in history

---

## Task 6 — Core: `get_history` method on `DeckRepository`

**Layer:** [core]
**Depends on:** Task 2

**Files:**
- Modify: `deckdex/storage/deck_repository.py`

**Description:**

Add the following method to `DeckRepository`:

```python
def get_history(
    self,
    deck_id: int,
    user_id: Optional[int] = None,
    limit: int = 50,
) -> Optional[List[Dict[str, Any]]]:
    """Return paginated snapshot history for a deck, newest-first.

    Returns None if the deck does not exist or does not belong to user_id.
    Each entry includes a computed diff against the previous snapshot.
    """
    from sqlalchemy import text

    engine = self._get_engine()
    with engine.connect() as conn:
        # Verify deck ownership
        where = "id = :deck_id"
        params: Dict[str, Any] = {"deck_id": deck_id}
        if user_id is not None:
            where += " AND user_id = :user_id"
            params["user_id"] = user_id
        deck_exists = conn.execute(
            text(f"SELECT 1 FROM decks WHERE {where}"), params
        ).fetchone()
        if not deck_exists:
            return None

        # Fetch limit+1 to have context for diff of the oldest entry
        clamped_limit = min(max(1, limit), 200)
        rows = (
            conn.execute(
                text("""
                    SELECT id, created_at, created_by, snapshot_data, change_summary
                    FROM deck_snapshots
                    WHERE deck_id = :deck_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"deck_id": deck_id, "limit": clamped_limit + 1},
            )
            .mappings()
            .fetchall()
        )

    snapshots = [dict(r) for r in rows]

    # Compute diffs: each snapshot diffs against the one after it (older)
    # snapshots[0] is newest, snapshots[-1] is oldest
    result = []
    for i, snap in enumerate(snapshots[:clamped_limit]):
        older_data: List[Dict[str, Any]] = []
        if i + 1 < len(snapshots):
            raw = snapshots[i + 1]["snapshot_data"]
            older_data = raw if isinstance(raw, list) else json.loads(raw)
        current_data: List[Dict[str, Any]] = snap["snapshot_data"]
        if not isinstance(current_data, list):
            current_data = json.loads(current_data)

        diff = _compute_diff(before=older_data, after=current_data)
        result.append({
            "id": snap["id"],
            "created_at": _serialize_ts(snap["created_at"]),
            "created_by": snap["created_by"],
            "change_summary": snap["change_summary"],
            "diff": diff,
        })

    return result
```

**Note on JSONB deserialization:** SQLAlchemy with psycopg2 returns JSONB columns as Python objects (list/dict) directly. The `isinstance(raw, list)` guard handles this without an extra `json.loads` call in the normal path.

**Acceptance criteria:**
- [ ] Method returns `None` when deck does not exist or belongs to different user
- [ ] Method returns newest-first list of up to `limit` snapshots
- [ ] `limit` is clamped to [1, 200] internally
- [ ] Each snapshot includes a correctly computed `diff`
- [ ] The first snapshot (when there is no older one) has an empty `before` producing all cards in `added`
- [ ] JSONB is deserialized correctly whether returned as dict/list or as string

---

## Task 7 — Core: `revert_to_snapshot` method on `DeckRepository`

**Layer:** [core]
**Depends on:** Task 2

**Files:**
- Modify: `deckdex/storage/deck_repository.py`

**Description:**

Add the following method to `DeckRepository`:

```python
def revert_to_snapshot(
    self,
    deck_id: int,
    snapshot_id: int,
    user_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Revert deck_cards to the state captured in snapshot_id.

    Returns:
        The updated DeckWithCards dict on success.
        None if deck or snapshot not found / wrong owner.

    Raises:
        ValueError: If a card in the snapshot no longer exists in the collection.
                    Route handler should convert to HTTP 409.
    """
    from sqlalchemy import text

    engine = self._get_engine()
    with engine.connect() as conn:
        # 1. Verify deck ownership
        where = "id = :deck_id"
        params: Dict[str, Any] = {"deck_id": deck_id}
        if user_id is not None:
            where += " AND user_id = :user_id"
            params["user_id"] = user_id
        deck_exists = conn.execute(
            text(f"SELECT 1 FROM decks WHERE {where}"), params
        ).fetchone()
        if not deck_exists:
            return None

        # 2. Load snapshot
        snap_row = conn.execute(
            text("""
                SELECT id, snapshot_data
                FROM deck_snapshots
                WHERE id = :snapshot_id AND deck_id = :deck_id
            """),
            {"snapshot_id": snapshot_id, "deck_id": deck_id},
        ).mappings().fetchone()
        if not snap_row:
            return None

        snapshot_data: List[Dict[str, Any]] = snap_row["snapshot_data"]
        if not isinstance(snapshot_data, list):
            snapshot_data = json.loads(snapshot_data)

        # 3. Clear current deck_cards
        conn.execute(
            text("DELETE FROM deck_cards WHERE deck_id = :deck_id"),
            {"deck_id": deck_id},
        )

        # 4. Re-insert from snapshot
        for entry in snapshot_data:
            try:
                conn.execute(
                    text("""
                        INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander)
                        VALUES (:deck_id, :card_id, :quantity, :is_commander)
                    """),
                    {
                        "deck_id": deck_id,
                        "card_id": entry["card_id"],
                        "quantity": entry["quantity"],
                        "is_commander": entry["is_commander"],
                    },
                )
            except Exception as exc:
                # FK violation: card no longer in collection
                raise ValueError(
                    f"Card '{entry['name']}' (id={entry['card_id']}) no longer exists in collection"
                ) from exc

        # 5. Take snapshot of reverted state
        if user_id is not None:
            self._take_snapshot(
                conn, deck_id, user_id,
                f"Reverted to snapshot #{snapshot_id}"
            )

        conn.commit()

    # Return updated deck
    return self.get_deck_with_cards(deck_id, user_id=user_id)
```

**Acceptance criteria:**
- [ ] Returns `None` when deck not found or wrong owner
- [ ] Returns `None` when snapshot not found or belongs to a different deck
- [ ] Deletes all existing `deck_cards` before re-inserting
- [ ] Re-inserts all cards from snapshot
- [ ] Creates a new snapshot recording the revert
- [ ] Raises `ValueError` if a card no longer exists in the collection (FK violation)
- [ ] Returns the updated `DeckWithCards` on success

---

## Task 8 — Backend: new Pydantic models and history/revert endpoints

**Layer:** [backend]
**Depends on:** Tasks 6, 7

**Files:**
- Modify: `backend/api/routes/decks.py`

**Description:**

**1. Add Pydantic models** (after the existing model definitions, before the routes section):

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

Also add `Query` to the FastAPI imports:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
```

**2. Add new endpoints** (after the existing `import_deck_text` endpoint):

```python
@router.get("/{deck_id}/history", response_model=DeckHistoryResponse)
async def get_deck_history(
    deck_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Return the snapshot history for a deck, newest-first. Each entry includes a computed diff."""
    history = repo.get_history(deck_id, user_id=user_id, limit=limit)
    if history is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return DeckHistoryResponse(deck_id=deck_id, snapshots=history)


@router.post("/{deck_id}/revert/{snapshot_id}")
async def revert_deck_to_snapshot(
    deck_id: int,
    snapshot_id: int,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Revert a deck to the state captured in snapshot_id. Creates a new snapshot recording the revert."""
    try:
        deck = repo.revert_to_snapshot(deck_id, snapshot_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck or snapshot not found")
    return deck
```

**Acceptance criteria:**
- [ ] `DeckHistoryResponse`, `DeckSnapshot`, `SnapshotDiff`, `SnapshotDiffCard`, `SnapshotDiffQuantityChange` Pydantic models defined
- [ ] `GET /api/decks/{deck_id}/history` returns 200 with `DeckHistoryResponse`
- [ ] `GET /api/decks/{deck_id}/history` returns 404 when deck not found
- [ ] `GET /api/decks/{deck_id}/history?limit=N` respects limit (validated 1–200)
- [ ] `POST /api/decks/{deck_id}/revert/{snapshot_id}` returns 200 with full deck on success
- [ ] `POST /api/decks/{deck_id}/revert/{snapshot_id}` returns 404 when deck/snapshot not found
- [ ] `POST /api/decks/{deck_id}/revert/{snapshot_id}` returns 409 when a card no longer exists
- [ ] Both endpoints return 501 when Postgres not configured (via `require_deck_repo`)
- [ ] Both endpoints require authentication (via `get_current_user_id`)

---

## Task 9 — Frontend: types and API client functions

**Layer:** [frontend]
**Depends on:** Task 8

**Files:**
- Modify: `frontend/src/api/client.ts`

**Description:**

**1. Add interfaces** (after the existing deck-related interfaces, after `BatchAddResult`):

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

**2. Add API methods** to the `api` object (after `importDeckText`):

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

revertDeck: async (deckId: number, snapshotId: number): Promise<DeckWithCards> => {
  const response = await apiFetch(`${API_BASE}/decks/${deckId}/revert/${snapshotId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
    if (response.status === 404) throw new Error('Deck or snapshot not found');
    if (response.status === 409) throw new Error((err as { detail?: string }).detail || 'A card in this snapshot no longer exists in your collection');
    throw new Error((err as { detail?: string }).detail || 'Failed to revert deck');
  }
  return response.json();
},
```

**Acceptance criteria:**
- [ ] All five new interfaces exported from `client.ts`
- [ ] `getDeckHistory` calls `GET /api/decks/{deckId}/history?limit={limit}`
- [ ] `revertDeck` calls `POST /api/decks/{deckId}/revert/{snapshotId}`
- [ ] Both functions handle 404, 409, 501 error cases with descriptive messages
- [ ] TypeScript strict mode: no `any`, all types explicit
- [ ] i18n keys not needed in `client.ts` (error messages are developer-facing; UI strings go in components)

---

## Task 10 — Frontend: i18n keys

**Layer:** [frontend]
**Depends on:** nothing (can be done in parallel with Tasks 9–12)

**Files:**
- Modify: `frontend/src/locales/en.json`
- Modify: `frontend/src/locales/es.json`

**Description:**

Add a `deckHistory` namespace to both locale files.

**`en.json`** — add after the `deckImport` block:

```json
"deckHistory": {
  "title": "Deck History",
  "history": "History",
  "loading": "Loading history…",
  "empty": "No history yet. Start editing your deck to record changes.",
  "revert": "Revert to this version",
  "reverting": "Reverting…",
  "revertSuccess": "Deck reverted successfully",
  "revertError": "Failed to revert deck",
  "revertCardMissing": "Cannot revert: a card in this snapshot no longer exists in your collection",
  "diffAdded_one": "+{{count}} card",
  "diffAdded_other": "+{{count}} cards",
  "diffRemoved_one": "-{{count}} card",
  "diffRemoved_other": "-{{count}} cards",
  "noChanges": "Initial state",
  "currentVersion": "Current version",
  "close": "Close"
}
```

**`es.json`** — add after the `deckImport` block (translate):

```json
"deckHistory": {
  "title": "Historial del mazo",
  "history": "Historial",
  "loading": "Cargando historial…",
  "empty": "Sin historial aún. Empieza a editar tu mazo para registrar cambios.",
  "revert": "Revertir a esta versión",
  "reverting": "Revirtiendo…",
  "revertSuccess": "Mazo revertido con éxito",
  "revertError": "Error al revertir el mazo",
  "revertCardMissing": "No se puede revertir: una carta de esta versión ya no existe en tu colección",
  "diffAdded_one": "+{{count}} carta",
  "diffAdded_other": "+{{count}} cartas",
  "diffRemoved_one": "-{{count}} carta",
  "diffRemoved_other": "-{{count}} cartas",
  "noChanges": "Estado inicial",
  "currentVersion": "Versión actual",
  "close": "Cerrar"
}
```

**Also add to `deckDetail` namespace** in both files (the button label):

In `en.json` `deckDetail` block, add:
```json
"history": "History"
```

In `es.json` `deckDetail` block, add:
```json
"history": "Historial"
```

**Acceptance criteria:**
- [ ] `deckHistory` namespace present in both `en.json` and `es.json`
- [ ] `deckDetail.history` key present in both locale files
- [ ] All keys are present in both files (no missing translation)
- [ ] Plural forms (`_one`, `_other`) follow i18next convention already used in the codebase (see `filters.showing_one`)

---

## Task 11 — Frontend: `RevertButton` component

**Layer:** [frontend]
**Depends on:** Tasks 9, 10

**Files:**
- Create: `frontend/src/components/RevertButton.tsx`

**Description:**

```tsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

interface RevertButtonProps {
  deckId: number;
  snapshotId: number;
  onReverted: () => void;
  disabled?: boolean;
}

export function RevertButton({ deckId, snapshotId, onReverted, disabled = false }: RevertButtonProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRevert = async () => {
    setError(null);
    setPending(true);
    try {
      const deck = await api.revertDeck(deckId, snapshotId);
      // Update deck detail cache immediately with the reverted state
      queryClient.setQueryData(['deck', deckId], deck);
      // Invalidate history so the new revert snapshot appears
      await queryClient.invalidateQueries({ queryKey: ['deck-history', deckId] });
      // Invalidate deck list for updated card count
      await queryClient.invalidateQueries({ queryKey: ['decks'] });
      onReverted();
    } catch (e) {
      const msg = e instanceof Error ? e.message : t('deckHistory.revertError');
      setError(msg.includes('no longer exists') ? t('deckHistory.revertCardMissing') : msg);
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={handleRevert}
        disabled={disabled || pending}
        className="px-2 py-1 text-xs rounded bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 hover:bg-amber-200 dark:hover:bg-amber-800/50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {pending ? t('deckHistory.reverting') : t('deckHistory.revert')}
      </button>
      {error && (
        <p role="alert" className="text-xs text-red-600 dark:text-red-400 max-w-[180px] text-right">
          {error}
        </p>
      )}
    </div>
  );
}
```

**Acceptance criteria:**
- [ ] `RevertButton` component created at `frontend/src/components/RevertButton.tsx`
- [ ] Shows loading text while mutation is in flight
- [ ] Shows error message on failure (inline, not console)
- [ ] Calls `onReverted()` on success
- [ ] Updates `['deck', deckId]` cache immediately with returned deck data (optimistic UX)
- [ ] Invalidates `['deck-history', deckId]` and `['decks']` after revert
- [ ] `disabled` prop disables the button (used for the most recent snapshot)

---

## Task 12 — Frontend: `DeckHistoryTimeline` component

**Layer:** [frontend]
**Depends on:** Tasks 10, 11

**Files:**
- Create: `frontend/src/components/DeckHistoryTimeline.tsx`

**Description:**

```tsx
import { useTranslation } from 'react-i18next';
import type { DeckSnapshot } from '../api/client';
import { RevertButton } from './RevertButton';

interface DeckHistoryTimelineProps {
  deckId: number;
  snapshots: DeckSnapshot[];
  onReverted: () => void;
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
  if (diffDays > 0) return rtf.format(-diffDays, 'day');
  if (diffHours > 0) return rtf.format(-diffHours, 'hour');
  if (diffMins > 0) return rtf.format(-diffMins, 'minute');
  return rtf.format(0, 'second');
}

function DiffSummary({ snapshot }: { snapshot: DeckSnapshot }) {
  const { t } = useTranslation();
  const { diff } = snapshot;
  const addedCount = diff.added.reduce((s, c) => s + c.quantity, 0);
  const removedCount = diff.removed.reduce((s, c) => s + c.quantity, 0);

  const parts: string[] = [];
  if (addedCount > 0) parts.push(t('deckHistory.diffAdded', { count: addedCount }));
  if (removedCount > 0) parts.push(t('deckHistory.diffRemoved', { count: removedCount }));
  if (parts.length === 0 && diff.quantity_changed.length === 0 && diff.commander_changed == null) {
    return <span className="text-xs text-gray-400 dark:text-gray-500">{t('deckHistory.noChanges')}</span>;
  }
  return <span className="text-xs text-gray-500 dark:text-gray-400">{parts.join(', ')}</span>;
}

export function DeckHistoryTimeline({ deckId, snapshots, onReverted }: DeckHistoryTimelineProps) {
  const { t } = useTranslation();

  if (snapshots.length === 0) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
        {t('deckHistory.empty')}
      </p>
    );
  }

  return (
    <ol className="space-y-1">
      {snapshots.map((snap, idx) => {
        const isCurrentVersion = idx === 0;
        return (
          <li
            key={snap.id}
            className="flex items-start justify-between gap-3 py-2 px-3 rounded hover:bg-gray-50 dark:hover:bg-gray-700/50"
          >
            <div className="flex flex-col gap-0.5 min-w-0">
              <span className="text-sm text-gray-900 dark:text-white truncate">
                {snap.change_summary}
                {isCurrentVersion && (
                  <span className="ml-2 text-xs text-indigo-600 dark:text-indigo-400">
                    ({t('deckHistory.currentVersion')})
                  </span>
                )}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  {formatRelativeTime(snap.created_at)}
                </span>
                <DiffSummary snapshot={snap} />
              </div>
            </div>
            <RevertButton
              deckId={deckId}
              snapshotId={snap.id}
              onReverted={onReverted}
              disabled={isCurrentVersion}
            />
          </li>
        );
      })}
    </ol>
  );
}
```

**Acceptance criteria:**
- [ ] `DeckHistoryTimeline` created at `frontend/src/components/DeckHistoryTimeline.tsx`
- [ ] Shows empty state message when `snapshots` is empty
- [ ] Each snapshot row displays: `change_summary`, relative timestamp, diff summary
- [ ] Most recent snapshot (index 0) shows "Current version" label and has `RevertButton` disabled
- [ ] All other snapshots have active `RevertButton`
- [ ] `formatRelativeTime` uses `Intl.RelativeTimeFormat` (no external date library)
- [ ] `DiffSummary` renders added/removed card counts using i18n plural keys

---

## Task 13 — Frontend: `DeckHistoryModal` component

**Layer:** [frontend]
**Depends on:** Task 12

**Files:**
- Create: `frontend/src/components/DeckHistoryModal.tsx`

**Description:**

```tsx
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { AccessibleModal } from './AccessibleModal';
import { DeckHistoryTimeline } from './DeckHistoryTimeline';

interface DeckHistoryModalProps {
  deckId: number;
  onClose: () => void;
  onReverted: () => void;
}

export function DeckHistoryModal({ deckId, onClose, onReverted }: DeckHistoryModalProps) {
  const { t } = useTranslation();

  const { data, isLoading, error } = useQuery({
    queryKey: ['deck-history', deckId],
    queryFn: () => api.getDeckHistory(deckId),
  });

  return (
    <AccessibleModal isOpen titleId="deck-history-modal-title" onClose={onClose} className="z-[60]">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <h2 id="deck-history-modal-title" className="text-base font-semibold text-gray-900 dark:text-white">
            {t('deckHistory.title')}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm"
          >
            {t('deckHistory.close')}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('deckHistory.loading')}</p>
          )}
          {error && (
            <p role="alert" className="text-sm text-red-600 dark:text-red-400">
              {error instanceof Error ? error.message : t('deckHistory.loading')}
            </p>
          )}
          {data && (
            <DeckHistoryTimeline
              deckId={deckId}
              snapshots={data.snapshots}
              onReverted={() => {
                onReverted();
                onClose();
              }}
            />
          )}
        </div>
      </div>
    </AccessibleModal>
  );
}
```

**Acceptance criteria:**
- [ ] `DeckHistoryModal` created at `frontend/src/components/DeckHistoryModal.tsx`
- [ ] Uses `AccessibleModal` with `z-[60]` (above `DeckDetailModal`'s `z-50`)
- [ ] `titleId="deck-history-modal-title"` wired to the `<h2>`
- [ ] Shows loading state while query is in flight
- [ ] Shows error message if query fails
- [ ] Calls `onReverted()` and `onClose()` after a successful revert

---

## Task 14 — Frontend: wire "History" button into `DeckDetailModal`

**Layer:** [frontend]
**Depends on:** Task 13

**Files:**
- Modify: `frontend/src/components/DeckDetailModal.tsx`

**Description:**

**1. Add import at top of file:**
```tsx
import { DeckHistoryModal } from './DeckHistoryModal';
```

**2. Add state variable** (alongside other `useState` declarations near the top of `DeckDetailModal`):
```tsx
const [historyOpen, setHistoryOpen] = useState(false);
```

**3. Add "History" button** to the action bar in the header (`div` containing Export, Import, Add card, Delete buttons). Insert between the Import button and the Add card button:

```tsx
<button
  type="button"
  onClick={() => setHistoryOpen(true)}
  className="px-3 py-1.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium"
>
  {t('deckDetail.history')}
</button>
```

**4. Render `DeckHistoryModal` conditionally**, after the `{importOpen && <DeckImportModal ...>}` block:

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

**Acceptance criteria:**
- [ ] "History" button appears in the `DeckDetailModal` header action bar
- [ ] Clicking "History" opens `DeckHistoryModal`
- [ ] After a successful revert, the history modal closes and the deck view refreshes
- [ ] `DeckDetailModal` still passes existing tests (mana curve dark mode test)
- [ ] No regression in existing button layout

---

## Task 15 — Tests: pytest unit tests for `_compute_diff` and `DeckRepository` snapshot methods

**Layer:** [backend] / [core]
**Depends on:** Tasks 2, 6, 7

**Files:**
- Create: `tests/test_deck_snapshots.py`

**Description:**

Create a pytest test file with unit tests for the snapshot-related functionality. Use `scope="function"` on all fixtures. Mock the database layer using `MagicMock` — do not require a real database connection.

**Test cases to include:**

1. `test_compute_diff_empty_before` — all cards are in `added`, nothing in `removed` or `quantity_changed`
2. `test_compute_diff_added_card` — a card present in `after` but not `before` is in `added`
3. `test_compute_diff_removed_card` — a card present in `before` but not `after` is in `removed`
4. `test_compute_diff_quantity_changed` — same card_id with different quantity is in `quantity_changed`
5. `test_compute_diff_commander_changed` — `commander_changed` is set when the commander card changes
6. `test_compute_diff_commander_unchanged` — `commander_changed` is `None` when same commander
7. `test_compute_diff_no_changes` — identical before and after produces empty diff with `commander_changed=None`

Import `_compute_diff` directly from the module:
```python
from deckdex.storage.deck_repository import _compute_diff
```

**Example fixture and test pattern:**
```python
import pytest
from deckdex.storage.deck_repository import _compute_diff


def snapshot_entry(card_id: int, name: str, qty: int, is_commander: bool = False) -> dict:
    return {"card_id": card_id, "name": name, "quantity": qty, "is_commander": is_commander}


def test_compute_diff_empty_before():
    after = [snapshot_entry(1, "Sol Ring", 1), snapshot_entry(2, "Lightning Bolt", 4)]
    diff = _compute_diff(before=[], after=after)
    assert len(diff["added"]) == 2
    assert diff["removed"] == []
    assert diff["quantity_changed"] == []
    assert diff["commander_changed"] is None
```

**Acceptance criteria:**
- [ ] `tests/test_deck_snapshots.py` created
- [ ] All 7 test functions present and passing
- [ ] All fixtures use `scope="function"` (none require scope="module")
- [ ] No database connection required (tests exercise `_compute_diff` only)
- [ ] `pytest tests/test_deck_snapshots.py` passes

---

## Task 16 — Tests: frontend Vitest tests for `DeckHistoryTimeline` and `RevertButton`

**Layer:** [frontend]
**Depends on:** Tasks 11, 12

**Files:**
- Create: `frontend/src/components/__tests__/DeckHistory.test.tsx`

**Description:**

Create a Vitest test file covering the timeline and revert button components.

**Mock setup:**
```typescript
vi.mock('../../api/client', () => ({
  api: {
    revertDeck: vi.fn(),
  },
}));
```

**Test cases:**

1. `DeckHistoryTimeline renders empty state when snapshots is empty` — renders the `deckHistory.empty` i18n key text
2. `DeckHistoryTimeline renders snapshot change_summary` — given one snapshot, `screen.getByText('Added 2x Lightning Bolt')` is in the DOM
3. `DeckHistoryTimeline first snapshot has disabled RevertButton` — the button for index 0 has `disabled` attribute
4. `DeckHistoryTimeline subsequent snapshots have active RevertButton` — button for index > 0 is not disabled
5. `RevertButton calls api.revertDeck and invokes onReverted on success` — mock `api.revertDeck` to resolve, click button, assert `onReverted` called

**Helper to build a snapshot:**
```typescript
function makeSnapshot(id: number, changeSummary: string, isFirst = false): DeckSnapshot {
  return {
    id,
    created_at: new Date().toISOString(),
    created_by: 1,
    change_summary: changeSummary,
    diff: { added: [], removed: [], quantity_changed: [], commander_changed: null },
  };
}
```

**Acceptance criteria:**
- [ ] `frontend/src/components/__tests__/DeckHistory.test.tsx` created
- [ ] 5 test cases present and passing
- [ ] `api.revertDeck` is mocked (not calling real network)
- [ ] `npx vitest run` passes for this file
- [ ] No existing tests broken

---

## Execution Order

```
Task 1  (migration)
  └─► Task 2  (helper + diff function)
        ├─► Task 3  (wire snapshots into mutations)
        │     └─► Task 4  (add_cards_from_import)
        │           └─► Task 5  (update import route)
        ├─► Task 6  (get_history)
        └─► Task 7  (revert_to_snapshot)
              └─► Task 8  (backend endpoints)
                    └─► Task 9  (client.ts)
                          └─► Task 11 (RevertButton)
                                └─► Task 12 (DeckHistoryTimeline)
                                      └─► Task 13 (DeckHistoryModal)
                                            └─► Task 14 (wire into DeckDetailModal)

Task 10 (i18n) — parallel with Tasks 9–14, must complete before Task 11
Task 15 (pytest unit tests) — after Task 2
Task 16 (vitest tests) — after Tasks 11–12
```

Tasks 3, 6, 7 can be done in parallel after Task 2 completes.
Tasks 5 and 8 must follow their direct dependencies.
Task 15 can be written and run after Task 2 (no DB required).
Task 16 can be written and run after Tasks 11–12.
