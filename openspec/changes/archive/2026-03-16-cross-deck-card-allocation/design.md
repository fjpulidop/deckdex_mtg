# Technical Design: Cross-Deck Card Allocation Visualization

## Context

The existing stack:
- `deck_cards` table: (deck_id, card_id, quantity, is_commander). PK is (deck_id, card_id).
- `decks` table: id, name, user_id.
- `cards` table: id, name, image_url, type_line, mana_cost, prices, user_id.
- `DeckRepository` in `deckdex/storage/deck_repository.py` handles all deck/card DB queries.
- The frontend has a working `CardGallery` component with lazy-loaded image tiles, `useImageCache` hook, and the `apiFetch` client in `api/client.ts`.
- The `/decks` route uses `DeckDetailModal` + `DeckCardPickerModal`; card removal calls `DELETE /api/decks/{deck_id}/cards/{card_id}`.

## Goals / Non-Goals

**Goals:**
- Expose all card allocation data in a single API call (cards + their deck memberships), scoped to the authenticated user.
- Render a full image grid at `/allocations` with color-coded status overlays.
- Allow removing a card from a specific deck directly from a click-through popover.

**Non-Goals:**
- Adding cards to decks from this view.
- Deck filtering (show cards only in a specific deck) — future iteration.
- Paginating the allocations endpoint (client receives all at once; the collection is user-scoped and manageable in a single query with a JOIN).

---

## 1. Backend

### 1.1 New Endpoint: `GET /api/cards/allocations`

**Route file:** `backend/api/routes/cards.py` (add new route) OR a new `backend/api/routes/allocations.py` included in `backend/api/main.py`.

Recommended: add to `cards.py` to avoid proliferating route files for a single endpoint. The route path `GET /api/cards/allocations` must be registered **before** any generic `GET /api/cards/{id}` wildcard route to avoid path collision in FastAPI. FastAPI evaluates routes in registration order for same-prefix conflicts.

**Authentication:** `get_current_user_id` dependency, same as all data endpoints.

**DB query:** Single query with a LEFT JOIN:

```sql
SELECT
    c.id            AS card_id,
    c.name          AS card_name,
    c.image_url,
    c.type_line,
    c.mana_cost,
    c.quantity,
    d.id            AS deck_id,
    d.name          AS deck_name
FROM cards c
LEFT JOIN deck_cards dc ON dc.card_id = c.id
LEFT JOIN decks d       ON d.id = dc.deck_id AND d.user_id = %(user_id)s
WHERE c.user_id = %(user_id)s
ORDER BY c.name ASC
```

This returns one row per (card, deck) pair. Cards in no deck appear once with `deck_id = NULL`. The aggregation into the response shape is done in Python (not SQL) for simplicity and to avoid a JSONB aggregation dependency.

**Response shape (Pydantic model):**

```python
class DeckRef(BaseModel):
    deck_id: int
    deck_name: str

class CardAllocation(BaseModel):
    card_id: int
    card_name: str
    image_url: str | None
    type_line: str | None
    mana_cost: str | None
    quantity: int
    decks: list[DeckRef]   # empty list = card is available (in no deck)

class CardAllocationsResponse(BaseModel):
    cards: list[CardAllocation]
```

`decks` being an empty list means "available" — this is the canonical definition of the green state. The frontend derives status from `len(decks)`.

**501 when no Postgres:** Same guard as deck routes — if `DeckRepository` is unavailable (no `DATABASE_URL`), return 501 with a clear message.

**Implementation note:** The aggregation loop in Python:
```python
seen: dict[int, CardAllocation] = {}
for row in rows:
    if row["card_id"] not in seen:
        seen[row["card_id"]] = CardAllocation(
            card_id=row["card_id"],
            card_name=row["card_name"],
            image_url=row["image_url"],
            type_line=row["type_line"],
            mana_cost=row["mana_cost"],
            quantity=row["quantity"],
            decks=[],
        )
    if row["deck_id"] is not None:
        seen[row["card_id"]].decks.append(
            DeckRef(deck_id=row["deck_id"], deck_name=row["deck_name"])
        )
return CardAllocationsResponse(cards=list(seen.values()))
```

### 1.2 Where the Query Lives

Add a method `get_all_card_allocations(user_id: int) -> list[dict]` to `DeckRepository`. This keeps all deck-related SQL in the repository layer, consistent with project conventions. The route handler calls this method and does the Python aggregation.

Alternatively, add a new method to the card repository. However, the allocation JOIN spans both cards and deck_cards, which are already within `DeckRepository`'s scope. Keeping it there avoids cross-repository dependencies.

---

## 2. Frontend

### 2.1 New API Client Method

In `frontend/src/api/client.ts`, add:

```typescript
export interface DeckRef {
  deck_id: number;
  deck_name: string;
}

export interface CardAllocation {
  card_id: number;
  card_name: string;
  image_url: string | null;
  type_line: string | null;
  mana_cost: string | null;
  quantity: number;
  decks: DeckRef[];
}

export interface CardAllocationsResponse {
  cards: CardAllocation[];
}
```

And in the `api` object:
```typescript
getCardAllocations: async (): Promise<CardAllocationsResponse> => {
  const res = await apiFetch(`${API_BASE}/cards/allocations`);
  if (!res.ok) throw new Error(`Failed to fetch allocations: ${res.status}`);
  return res.json();
},
```

### 2.2 New Page: `CardAllocations`

**File:** `frontend/src/pages/CardAllocations.tsx`

**Route:** `/allocations` — added to `App.tsx` under `ProtectedRoute`, alongside `/decks` and `/analytics`.

**Data fetching:** Use `useQuery` from TanStack Query with key `['card-allocations']`. Show a spinner while loading. Show an error message on failure (including when the backend returns 501 for no Postgres — surface this as "deck features require Postgres").

**Layout:** Reuse the same responsive grid as `CardGallery` (`grid-cols-[repeat(auto-fill,minmax(120px,1fr))]` or similar). Each tile is an `AllocationTile` component.

### 2.3 `AllocationTile` Component

**File:** `frontend/src/components/AllocationTile.tsx`

Props:
```typescript
interface AllocationTileProps {
  allocation: CardAllocation;
  onRemoveFromDeck: (deckId: number, cardId: number) => void;
}
```

**Rendering:**
- Card image loaded via `useImageCache(allocation.card_id)` — reuses the existing lazy-load/cache hook.
- Status badge: positioned bottom-right, small colored circle or pill.
  - `decks.length === 0` → green (`bg-green-500`)
  - `decks.length === 1` → orange (`bg-orange-500`)
  - `decks.length >= 2` → red (`bg-red-500`)
- Clicking the tile opens the `AllocationPopover` inline (toggle state local to tile).

**Status derivation function** (pure, exported for tests):
```typescript
export type AllocationStatus = 'available' | 'assigned' | 'shared';

export function getAllocationStatus(deckCount: number): AllocationStatus {
  if (deckCount === 0) return 'available';
  if (deckCount === 1) return 'assigned';
  return 'shared';
}
```

### 2.4 `AllocationPopover` Component

**File:** `frontend/src/components/AllocationPopover.tsx`

A small overlay anchored to the tile (positioned absolute within the tile's relative container, or rendered in a portal if overflow clipping is an issue). Opens on tile click, dismisses on outside click or Escape.

**Content when `decks.length === 0`:**
```
Card name
"Available — not in any deck"
[Close]
```

**Content when `decks.length >= 1`:**
```
Card name
Assigned to:
  [Deck A name]  [Remove]
  [Deck B name]  [Remove]
[Close]
```

The `[Remove]` button calls `onRemoveFromDeck(deckId, cardId)` passed down from `CardAllocations` page. The page handler calls `api.removeDeckCard(deckId, cardId)` then invalidates the `['card-allocations']` query via `queryClient.invalidateQueries`.

**Accessibility:**
- `role="dialog"`, `aria-label="Card allocation details"`.
- Focus trap within the popover while open.
- Escape key closes it.

### 2.5 Nav Link

In `Navbar.tsx`, add an entry to `navLinks`:
```typescript
{ path: '/allocations', label: t('navbar.allocations'), badge: 'alpha' },
```

Add the i18n key `navbar.allocations` to `en.json` and `es.json`.

### 2.6 Router Registration

In `App.tsx` (or wherever routes are defined), add:
```tsx
<Route path="/allocations" element={<ProtectedRoute><CardAllocations /></ProtectedRoute>} />
```

---

## 3. Key Design Decisions

### Decision 1: Single JOIN query vs. multiple requests
A single SQL JOIN returning all allocation data in one round-trip is the correct approach here. The alternative (fetch all cards, then fetch all deck memberships separately, merge in the frontend) would require two API calls and client-side join logic. The JOIN in the repository layer is cleaner, tested in one place, and requires zero extra latency.

### Decision 2: Aggregation in Python vs. SQL JSONB
SQL `json_agg` / `array_agg` would let us return the grouped result directly. However, this introduces a PostgreSQL-specific function and is harder to mock in tests. Python-side aggregation over a flat row list is portable, readable, and consistent with how the rest of the project handles multi-row results from the repository layer.

### Decision 3: Popover vs. modal for card detail
A popover (anchored to the tile) is more appropriate than a full-screen modal here because the action (remove from deck) is lightweight. The existing `CardDetailModal` is heavyweight by design. Opening it on every tile click in a grid of 1,000 cards would be disorienting. The popover keeps focus local to the card and dismisses trivially.

### Decision 4: Route placement in `cards.py`
Adding `/api/cards/allocations` to the existing `cards.py` router keeps the router file count low. The critical constraint is FastAPI route registration order: the `allocations` literal path must appear before any `/{id}` wildcard in the same router. Since FastAPI uses the first matching route for a given request, registering `GET /allocations` before `GET /{id}` prevents `"allocations"` from being matched as a card id.

### Decision 5: No Postgres → 501, consistent with deck routes
Allocation data depends on `deck_cards`, which only exists in Postgres. Returning 501 mirrors the existing pattern in `decks.py` (`require_deck_repo()`). The frontend should detect this and show an informative message rather than an error toast.

---

## 4. Data Flow Summary

```
User navigates to /allocations
  → CardAllocations page mounts
  → useQuery(['card-allocations']) fires
  → GET /api/cards/allocations
  → FastAPI authenticates (JWT cookie)
  → DeckRepository.get_all_card_allocations(user_id)
  → SQL LEFT JOIN: cards + deck_cards + decks
  → Python aggregation → CardAllocationsResponse
  → JSON response
  → AllocationTile rendered per card, status badge derived from decks.length
  → User clicks tile → AllocationPopover opens
  → User clicks [Remove] on a deck
  → DELETE /api/decks/{deck_id}/cards/{card_id}
  → queryClient.invalidateQueries(['card-allocations'])
  → Grid re-renders with updated badge
```
