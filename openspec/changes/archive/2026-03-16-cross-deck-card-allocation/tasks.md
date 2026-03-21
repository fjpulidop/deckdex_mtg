# Implementation Tasks: Cross-Deck Card Allocation Visualization

Tasks are ordered by dependency. Backend tasks must complete before frontend integration tasks.
All tasks are atomic: each has a single clear deliverable and acceptance criteria.

---

## Phase 1 — Backend

### Task B1: Add `get_all_card_allocations` to DeckRepository [backend]

**File:** `deckdex/storage/deck_repository.py`

**Description:**
Add method `get_all_card_allocations(self, user_id: int) -> list[dict]` to `DeckRepository`.
The method executes a LEFT JOIN query:

```sql
SELECT
    c.id        AS card_id,
    c.name      AS card_name,
    c.image_url,
    c.type_line,
    c.mana_cost,
    c.quantity,
    d.id        AS deck_id,
    d.name      AS deck_name
FROM cards c
LEFT JOIN deck_cards dc ON dc.card_id = c.id
LEFT JOIN decks d       ON d.id = dc.deck_id AND d.user_id = %(user_id)s
WHERE c.user_id = %(user_id)s
ORDER BY c.name ASC
```

Returns a list of raw dicts (one row per card-deck pair; cards in no deck appear once with
`deck_id = None`).

**Acceptance criteria:**
- Method exists on `DeckRepository` and executes without error against a real DB.
- Returns an empty list when the user has no cards.
- Returns one row per card when the user has cards but no decks (deck_id=None in each row).
- Returns multiple rows for the same card when it is in multiple decks.
- Rows are ordered by card name ascending.

**Dependencies:** None (pure DB layer addition).

---

### Task B2: Add Pydantic response models for allocations [backend]

**File:** `backend/api/routes/cards.py` (or a new `backend/api/routes/allocations.py`)

**Description:**
Define Pydantic models:
```python
class DeckRef(BaseModel):
    deck_id: int
    deck_name: str

class CardAllocation(BaseModel):
    card_id: int
    card_name: str
    image_url: str | None = None
    type_line: str | None = None
    mana_cost: str | None = None
    quantity: int
    decks: list[DeckRef]

class CardAllocationsResponse(BaseModel):
    cards: list[CardAllocation]
```

**Acceptance criteria:**
- Models are importable and Pydantic validates them correctly.
- `CardAllocation` with `decks=[]` is valid (available card).
- No existing model is modified.

**Dependencies:** None.

---

### Task B3: Implement `GET /api/cards/allocations` route [backend]

**File:** `backend/api/routes/cards.py`

**Description:**
Add route `GET /api/cards/allocations` using `get_current_user_id` and `require_deck_repo`
(or equivalent guard for 501 when no Postgres). The handler:
1. Calls `repo.get_all_card_allocations(user_id)` to get flat rows.
2. Aggregates in Python: groups rows by `card_id`, builds `CardAllocation` with `decks` list.
3. Returns `CardAllocationsResponse`.

**Critical:** Register this route **before** any `GET /{id}` wildcard in the same router.
In FastAPI, route matching is first-registration-wins for ambiguous paths.

**Acceptance criteria:**
- `GET /api/cards/allocations` returns HTTP 200 with `CardAllocationsResponse` shape when authenticated and Postgres is available.
- Returns HTTP 401 when no valid JWT cookie is present.
- Returns HTTP 501 when Postgres is not configured.
- Path `/api/cards/allocations` is not accidentally matched as a card-by-id route.
- Verify with `curl` or a test that the route resolves correctly even though `"allocations"` could look like a card id string.

**Dependencies:** B1, B2.

---

### Task B4: Backend tests for the allocations endpoint [backend]

**File:** `tests/test_allocations.py` (new file)

**Description:**
Write pytest tests using `scope="function"` fixtures with a mocked `DeckRepository`.
Cover:
1. Returns 401 when unauthenticated.
2. Returns 501 when `get_deck_repo()` returns `None`.
3. Happy path: mocked repo returns flat rows → response has correctly aggregated `cards` with `decks` populated.
4. Card in no deck: `decks` array is empty in response.
5. Card in multiple decks: `decks` array has multiple entries.
6. Empty collection: `cards` array is empty.

**All fixtures MUST use `scope="function"`** — module-scope mocks cause cross-test pollution
(project-wide rule).

Pydantic validation errors return HTTP 400, not 422 (project-wide convention). If any
invalid payload test is added, assert 400.

**Acceptance criteria:**
- All 6+ test cases pass with `pytest tests/test_allocations.py`.
- No `scope="module"` in fixture definitions.
- Tests do not hit a real database.

**Dependencies:** B3.

---

## Phase 2 — Frontend Types and API Client

### Task F1: Add TypeScript types and API client method [frontend]

**File:** `frontend/src/api/client.ts`

**Description:**
Add interfaces:
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

Add method to the `api` export object:
```typescript
getCardAllocations: async (): Promise<CardAllocationsResponse> => {
  const res = await apiFetch(`${API_BASE}/cards/allocations`);
  if (!res.ok) throw new Error(`Failed to fetch allocations: ${res.status}`);
  return res.json();
},
```

**Acceptance criteria:**
- TypeScript compiler accepts the new types with strict mode.
- No existing interface is modified.
- `api.getCardAllocations()` is callable from components.
- Method uses `apiFetch` (not raw `fetch`), consistent with all other API calls.

**Dependencies:** B3 (integration), but can be written before B3 is deployed.

---

## Phase 3 — Frontend Components

### Task F2: Implement `getAllocationStatus` utility and `AllocationTile` component [frontend]

**File:** `frontend/src/components/AllocationTile.tsx` (new file)

**Description:**
Create a pure utility function and tile component:

```typescript
export type AllocationStatus = 'available' | 'assigned' | 'shared';

export function getAllocationStatus(deckCount: number): AllocationStatus {
  if (deckCount === 0) return 'available';
  if (deckCount === 1) return 'assigned';
  return 'shared';
}
```

`AllocationTile` renders:
- Card image loaded via `useImageCache(allocation.card_id)` with lazy-load (IntersectionObserver pattern from `CardGallery`).
- Status badge overlay (bottom-right corner, small pill):
  - `available` → `bg-green-500`
  - `assigned` → `bg-orange-500`
  - `shared` → `bg-red-500`
- Clicking tile calls `onTileClick(allocation)` prop.

**Props interface:**
```typescript
interface AllocationTileProps {
  allocation: CardAllocation;
  onTileClick: (allocation: CardAllocation) => void;
}
```

**Acceptance criteria:**
- Tile renders with image placeholder before viewport intersection.
- Status badge renders with correct color for each of the 3 states.
- Click handler fires with the allocation object.
- Component is typed with TypeScript strict mode (no implicit `any`).

**Dependencies:** F1.

---

### Task F3: Implement `AllocationPopover` component [frontend]

**File:** `frontend/src/components/AllocationPopover.tsx` (new file)

**Description:**
Popover anchored to the tile. Displayed when a tile is clicked (state managed in `CardAllocations` page). Receives:

```typescript
interface AllocationPopoverProps {
  allocation: CardAllocation;
  onRemoveFromDeck: (deckId: number, cardId: number) => void;
  onClose: () => void;
}
```

**Content:**
- Card name as heading.
- If `allocation.decks.length === 0`: message "Available — not in any deck".
- If `allocation.decks.length >= 1`: list of decks, each with deck name and a "Remove" button.
- Close button (or Escape key to dismiss).

**Accessibility:**
- `role="dialog"`, `aria-modal="true"`, `aria-label` = card name + " allocation details".
- Trap focus within the popover while open (or use `AccessibleModal` if it supports the use case).
- Escape key calls `onClose`.
- "Remove" button has `aria-label="Remove from [deck name]"`.

**Loading state for remove action:** Show a brief disabled state on the "Remove" button while the mutation is in-flight (use local `isPending` state set before the `onRemoveFromDeck` call resolves).

**Acceptance criteria:**
- Popover renders with correct content for 0-deck, 1-deck, and 2-deck cases.
- Remove button calls `onRemoveFromDeck` with correct deckId and cardId.
- Escape key and close button call `onClose`.
- `role="dialog"` is present in the DOM.

**Dependencies:** F1.

---

### Task F4: Implement `CardAllocations` page [frontend]

**File:** `frontend/src/pages/CardAllocations.tsx` (new file)

**Description:**
Main page component for `/allocations`.

```typescript
export function CardAllocations() { ... }
```

**Behavior:**
- `useQuery(['card-allocations'], api.getCardAllocations)` — loads allocation data.
- Shows a loading spinner while fetching.
- On HTTP 501 (no Postgres): shows a user-friendly message (not an error toast) explaining that deck features require Postgres/DATABASE_URL.
- On other errors: shows a generic error message.
- Grid: `grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-3` (same breakpoints as `CardGallery`).
- Renders one `AllocationTile` per `CardAllocation`.
- State: `selectedAllocation: CardAllocation | null` — set when tile is clicked, cleared on popover close.
- When `selectedAllocation` is set: renders `AllocationPopover`.
- `onRemoveFromDeck` handler:
  1. Calls `api.removeDeckCard(deckId, cardId)` (already exists in client).
  2. On success: calls `queryClient.invalidateQueries({ queryKey: ['card-allocations'] })`.
  3. On error: shows error toast or inline message.
  4. Clears `selectedAllocation` after successful removal (popover closes).

**Page header:** Title "Card Allocations", brief subtitle "See where each card is used across your decks."

**Acceptance criteria:**
- Page renders grid with status badges for all cards.
- Clicking a tile opens the popover for that card.
- Removing from a deck via popover triggers cache invalidation and the badge updates on next render.
- 501 response shows informative message instead of error.
- TypeScript strict mode, no implicit `any`.

**Dependencies:** F2, F3, F1.

---

## Phase 4 — Navigation and Routing

### Task F5: Add nav link and route for `/allocations` [frontend]

**Files:**
- `frontend/src/components/Navbar.tsx`
- `frontend/src/App.tsx` (or wherever routes are defined)
- `frontend/src/locales/en.json`
- `frontend/src/locales/es.json`

**Description:**

In `Navbar.tsx`, add to `navLinks` array (after the Decks link, before Analytics):
```typescript
{ path: '/allocations', label: t('navbar.allocations'), badge: 'alpha' },
```

In `App.tsx` (inside the authenticated/protected route tree):
```tsx
import { CardAllocations } from './pages/CardAllocations';
// ...
<Route path="/allocations" element={<ProtectedRoute><CardAllocations /></ProtectedRoute>} />
```

In `en.json` and `es.json`, add:
```json
"navbar": {
  "allocations": "Allocations"
}
```
(Spanish: `"Asignaciones"`)

**Acceptance criteria:**
- "Allocations" link appears in the navbar between Decks and Analytics.
- Link has an "alpha" badge styled identically to the "Decks" alpha badge.
- Navigating to `/allocations` renders the `CardAllocations` page (not a 404 or redirect).
- Unauthenticated users navigating to `/allocations` are redirected to `/login` by `ProtectedRoute`.
- i18n keys exist in both `en.json` and `es.json`.

**Dependencies:** F4.

---

## Phase 5 — Frontend Tests

### Task F6: Unit tests for `getAllocationStatus` and `AllocationTile` [frontend]

**File:** `frontend/src/components/__tests__/AllocationTile.test.tsx` (new file)

**Description:**
Use Vitest + Testing Library.

Tests:
1. `getAllocationStatus(0)` returns `'available'`.
2. `getAllocationStatus(1)` returns `'assigned'`.
3. `getAllocationStatus(3)` returns `'shared'`.
4. `AllocationTile` renders with `available` status → green badge is in the DOM.
5. `AllocationTile` renders with `assigned` status → orange badge is in the DOM.
6. `AllocationTile` renders with `shared` status → red badge is in the DOM.
7. Clicking tile calls `onTileClick` with the correct allocation object.

Mock `useImageCache` to return a stable src (avoids IntersectionObserver setup in tests).

**Acceptance criteria:**
- All 7 tests pass with `npm run test` (or `vitest run`).
- No real network calls or DOM image loading.

**Dependencies:** F2.

---

### Task F7: Unit tests for `AllocationPopover` [frontend]

**File:** `frontend/src/components/__tests__/AllocationPopover.test.tsx` (new file)

**Description:**
Tests:
1. Renders "Available — not in any deck" when `allocation.decks` is empty.
2. Renders deck name(s) when `allocation.decks` has entries.
3. Clicking a "Remove" button calls `onRemoveFromDeck` with correct `(deckId, cardId)`.
4. Clicking close button calls `onClose`.
5. Pressing Escape calls `onClose`.
6. `role="dialog"` is present.

**Acceptance criteria:**
- All 6 tests pass.
- No real API calls (mock `onRemoveFromDeck` as a jest/vitest spy).

**Dependencies:** F3.

---

### Task F8: Integration test for `CardAllocations` page [frontend]

**File:** `frontend/src/pages/__tests__/CardAllocations.test.tsx` (new file)

**Description:**
Tests:
1. Shows loading state while query is in-flight.
2. Renders correct number of tiles after data loads (mock API response).
3. Clicking a tile opens the popover for that card.
4. 501 response renders informative message (not an error boundary crash).
5. Remove action calls `api.removeDeckCard` and invalidates cache.

Mock `api.getCardAllocations` and `api.removeDeckCard` using Vitest's module mock. Mock `useImageCache` to return a stable image src.

**Acceptance criteria:**
- All 5 tests pass.
- No real HTTP requests in tests.
- Query client is wrapped in a `QueryClientProvider` in test setup.

**Dependencies:** F4, F5.
