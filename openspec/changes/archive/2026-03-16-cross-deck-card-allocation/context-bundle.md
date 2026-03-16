# Context Bundle: Cross-Deck Card Allocation Visualization

This file provides the exact file locations, relevant code sections, and precise changes
needed for each implementation task. A developer should be able to implement the full feature
using this file plus the design and tasks docs.

---

## Key Files

### Backend

| File | Role |
|------|------|
| `deckdex/storage/deck_repository.py` | Add `get_all_card_allocations` method |
| `backend/api/routes/cards.py` | Add `GET /api/cards/allocations` route and Pydantic models |
| `backend/api/dependencies.py` | `get_current_user_id`, `get_deck_repo` — no changes needed |
| `tests/test_allocations.py` | New test file |

### Frontend

| File | Role |
|------|------|
| `frontend/src/api/client.ts` | Add types and `getCardAllocations` method |
| `frontend/src/components/AllocationTile.tsx` | New component |
| `frontend/src/components/AllocationPopover.tsx` | New component |
| `frontend/src/pages/CardAllocations.tsx` | New page |
| `frontend/src/components/Navbar.tsx` | Add nav link |
| `frontend/src/App.tsx` | Register route |
| `frontend/src/locales/en.json` | Add i18n key |
| `frontend/src/locales/es.json` | Add i18n key |

---

## Backend Changes

### `deckdex/storage/deck_repository.py`

Add at end of class `DeckRepository`:

```python
def get_all_card_allocations(self, user_id: int) -> list[dict]:
    """Return all cards for user with their deck assignments.

    Returns a flat list of rows: one row per (card, deck) pair.
    Cards in no deck appear once with deck_id=None, deck_name=None.
    """
    sql = """
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
    """
    with self._get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"user_id": user_id})
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
```

Note: Match the existing `_get_connection` / cursor pattern used elsewhere in the file.
If the repo uses a different DB access pattern (e.g. `psycopg2` context manager, SQLAlchemy
session), adapt accordingly while keeping the SQL query identical.

---

### `backend/api/routes/cards.py`

**Step 1:** Add Pydantic models near the top of the file (after existing imports):

```python
class DeckRef(BaseModel):
    deck_id: int
    deck_name: str

class CardAllocation(BaseModel):
    card_id: int
    card_name: str
    image_url: Optional[str] = None
    type_line: Optional[str] = None
    mana_cost: Optional[str] = None
    quantity: int
    decks: List[DeckRef]

class CardAllocationsResponse(BaseModel):
    cards: List[CardAllocation]
```

**Step 2:** Add the route. It MUST be placed before any route that has a path parameter
`/{id}` or `/{card_id}` in the same router to prevent "allocations" being matched as an id:

```python
@router.get("/allocations", response_model=CardAllocationsResponse)
async def get_card_allocations(
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Return all collection cards with their deck assignment lists."""
    rows = repo.get_all_card_allocations(user_id=user_id)

    # Aggregate flat rows into per-card structure
    seen: dict[int, CardAllocation] = {}
    for row in rows:
        cid = row["card_id"]
        if cid not in seen:
            seen[cid] = CardAllocation(
                card_id=cid,
                card_name=row["card_name"] or "",
                image_url=row.get("image_url"),
                type_line=row.get("type_line"),
                mana_cost=row.get("mana_cost"),
                quantity=row.get("quantity") or 1,
                decks=[],
            )
        if row.get("deck_id") is not None:
            seen[cid].decks.append(
                DeckRef(deck_id=row["deck_id"], deck_name=row["deck_name"])
            )

    return CardAllocationsResponse(cards=list(seen.values()))
```

**Step 3:** Check that `require_deck_repo` and `get_current_user_id` are already imported
in `cards.py`. If `require_deck_repo` is currently only in `decks.py`, either:
  (a) Move it to `backend/api/dependencies.py` and import from both route files, or
  (b) Duplicate the guard in `cards.py` (less preferred — leads to drift).

Option (a) is recommended. The existing `require_deck_repo` function in `decks.py`:
```python
def require_deck_repo() -> DeckRepository:
    repo = get_deck_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Decks require Postgres. Set DATABASE_URL to use the deck builder.",
        )
    return repo
```
Move this to `backend/api/dependencies.py` and update `decks.py` import.

---

### `tests/test_allocations.py` (new file)

```python
"""Tests for GET /api/cards/allocations endpoint."""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def mock_user_id():
    with patch("backend.api.dependencies.get_current_user_id", return_value=1):
        yield 1


@pytest.fixture()
def mock_deck_repo():
    repo = MagicMock()
    with patch("backend.api.dependencies.get_deck_repo", return_value=repo):
        yield repo


def test_allocations_unauthenticated(client):
    """Unauthenticated request returns 401."""
    response = client.get("/api/cards/allocations")
    assert response.status_code == 401


def test_allocations_no_postgres(client, mock_user_id):
    """Returns 501 when Postgres is not configured."""
    with patch("backend.api.dependencies.get_deck_repo", return_value=None):
        response = client.get("/api/cards/allocations")
    assert response.status_code == 501


def test_allocations_empty_collection(client, mock_user_id, mock_deck_repo):
    """Returns empty cards list when user has no cards."""
    mock_deck_repo.get_all_card_allocations.return_value = []
    response = client.get("/api/cards/allocations")
    assert response.status_code == 200
    assert response.json() == {"cards": []}


def test_allocations_card_in_no_deck(client, mock_user_id, mock_deck_repo):
    """Card with deck_id=None appears with empty decks array."""
    mock_deck_repo.get_all_card_allocations.return_value = [
        {"card_id": 1, "card_name": "Lightning Bolt", "image_url": None,
         "type_line": "Instant", "mana_cost": "{R}", "quantity": 1,
         "deck_id": None, "deck_name": None},
    ]
    response = client.get("/api/cards/allocations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["cards"]) == 1
    assert data["cards"][0]["decks"] == []


def test_allocations_card_in_one_deck(client, mock_user_id, mock_deck_repo):
    """Card in one deck has one entry in decks array."""
    mock_deck_repo.get_all_card_allocations.return_value = [
        {"card_id": 2, "card_name": "Sol Ring", "image_url": None,
         "type_line": "Artifact", "mana_cost": "{1}", "quantity": 1,
         "deck_id": 10, "deck_name": "My Commander"},
    ]
    response = client.get("/api/cards/allocations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["cards"]) == 1
    assert len(data["cards"][0]["decks"]) == 1
    assert data["cards"][0]["decks"][0]["deck_id"] == 10


def test_allocations_card_in_multiple_decks(client, mock_user_id, mock_deck_repo):
    """Card in two decks appears once with two entries in decks array."""
    mock_deck_repo.get_all_card_allocations.return_value = [
        {"card_id": 3, "card_name": "Island", "image_url": None,
         "type_line": "Land", "mana_cost": None, "quantity": 4,
         "deck_id": 10, "deck_name": "Deck A"},
        {"card_id": 3, "card_name": "Island", "image_url": None,
         "type_line": "Land", "mana_cost": None, "quantity": 4,
         "deck_id": 11, "deck_name": "Deck B"},
    ]
    response = client.get("/api/cards/allocations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["cards"]) == 1  # deduplicated
    assert len(data["cards"][0]["decks"]) == 2
```

Note: Adjust the mock/patch paths to match actual import paths in your project structure.
If `get_current_user_id` is applied via a cookie dependency (not patchable directly),
use `app.dependency_overrides` pattern instead.

---

## Frontend Changes

### `frontend/src/api/client.ts`

Add after the `BatchAddResult` interface (around line 187):

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

Add to the `api` object (find the closing `}` of the `api` const and add before it):

```typescript
  getCardAllocations: async (): Promise<CardAllocationsResponse> => {
    const res = await apiFetch(`${API_BASE}/cards/allocations`);
    if (!res.ok) throw new Error(`Failed to fetch allocations: ${res.status}`);
    return res.json();
  },
```

---

### `frontend/src/components/Navbar.tsx`

In the `navLinks` array (around line 56), add between the decks and analytics entries:

```typescript
{ path: '/allocations', label: t('navbar.allocations'), badge: 'alpha' },
```

Result:
```typescript
const navLinks = [
  { path: '/dashboard', label: t('navbar.collection') },
  { path: '/decks', label: t('navbar.deckBuilder'), badge: 'alpha' },
  { path: '/allocations', label: t('navbar.allocations'), badge: 'alpha' },
  { path: '/analytics', label: t('navbar.analytics'), badge: 'beta' },
  ...(user?.is_admin ? [{ path: '/admin', label: t('navbar.admin') }] : []),
];
```

---

### `frontend/src/locales/en.json`

Add to the `navbar` section:
```json
"allocations": "Allocations"
```

### `frontend/src/locales/es.json`

Add to the `navbar` section:
```json
"allocations": "Asignaciones"
```

---

### `frontend/src/App.tsx`

Add import:
```typescript
import { CardAllocations } from './pages/CardAllocations';
```

Add route inside the authenticated route tree (alongside `/decks`):
```tsx
<Route path="/allocations" element={<ProtectedRoute><CardAllocations /></ProtectedRoute>} />
```

---

## Component Skeletons

### `frontend/src/components/AllocationTile.tsx`

```tsx
import { useRef, useEffect, useState } from 'react';
import type { CardAllocation } from '../api/client';
import { useImageCache } from '../hooks/useImageCache';

export type AllocationStatus = 'available' | 'assigned' | 'shared';

export function getAllocationStatus(deckCount: number): AllocationStatus {
  if (deckCount === 0) return 'available';
  if (deckCount === 1) return 'assigned';
  return 'shared';
}

const STATUS_COLORS: Record<AllocationStatus, string> = {
  available: 'bg-green-500',
  assigned: 'bg-orange-500',
  shared: 'bg-red-500',
};

const STATUS_LABELS: Record<AllocationStatus, string> = {
  available: 'Available',
  assigned: 'In 1 deck',
  shared: 'In multiple decks',
};

interface AllocationTileProps {
  allocation: CardAllocation;
  onTileClick: (allocation: CardAllocation) => void;
}

export function AllocationTile({ allocation, onTileClick }: AllocationTileProps) {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLButtonElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observerRef.current?.disconnect();
        }
      },
      { rootMargin: '200px' },
    );
    observerRef.current.observe(el);
    return () => observerRef.current?.disconnect();
  }, []);

  const cardId = isVisible ? allocation.card_id : null;
  const { src } = useImageCache(cardId);
  const status = getAllocationStatus(allocation.decks.length);

  return (
    <button
      ref={ref}
      type="button"
      onClick={() => onTileClick(allocation)}
      aria-label={`${allocation.card_name} — ${STATUS_LABELS[status]}`}
      className="relative aspect-[63/88] rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 w-full"
    >
      {src && (
        <img
          src={src}
          alt={allocation.card_name}
          className="absolute inset-0 w-full h-full object-cover"
        />
      )}
      {/* Status badge */}
      <span
        aria-hidden="true"
        className={`absolute bottom-1 right-1 w-3 h-3 rounded-full border-2 border-white dark:border-gray-800 ${STATUS_COLORS[status]}`}
      />
    </button>
  );
}
```

---

### `frontend/src/components/AllocationPopover.tsx`

```tsx
import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import type { CardAllocation } from '../api/client';

interface AllocationPopoverProps {
  allocation: CardAllocation;
  onRemoveFromDeck: (deckId: number, cardId: number) => void;
  onClose: () => void;
}

export function AllocationPopover({ allocation, onRemoveFromDeck, onClose }: AllocationPopoverProps) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`${allocation.card_name} allocation details`}
      className="absolute z-50 top-0 left-full ml-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-600 p-3"
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white pr-2 leading-tight">
          {allocation.card_name}
        </h3>
        <button
          ref={closeRef}
          onClick={onClose}
          aria-label="Close"
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {allocation.decks.length === 0 ? (
        <p className="text-xs text-green-600 dark:text-green-400">
          Available — not in any deck
        </p>
      ) : (
        <ul className="space-y-1">
          {allocation.decks.map((deck) => (
            <li key={deck.deck_id} className="flex items-center justify-between gap-2">
              <span className="text-xs text-gray-700 dark:text-gray-300 truncate">
                {deck.deck_name}
              </span>
              <button
                onClick={() => onRemoveFromDeck(deck.deck_id, allocation.card_id)}
                aria-label={`Remove from ${deck.deck_name}`}
                className="flex-shrink-0 text-xs text-red-600 dark:text-red-400 hover:underline focus:outline-none focus:ring-2 focus:ring-red-500 rounded"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

---

### `frontend/src/pages/CardAllocations.tsx`

```tsx
import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { CardAllocation } from '../api/client';
import { AllocationTile } from '../components/AllocationTile';
import { AllocationPopover } from '../components/AllocationPopover';

export function CardAllocations() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<CardAllocation | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['card-allocations'],
    queryFn: api.getCardAllocations,
  });

  const handleRemove = async (deckId: number, cardId: number) => {
    await api.removeDeckCard(deckId, cardId);
    await queryClient.invalidateQueries({ queryKey: ['card-allocations'] });
    setSelected(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  // Detect 501 (no Postgres) — the thrown error includes the status code
  if (error) {
    const msg = error instanceof Error ? error.message : '';
    const isNoPg = msg.includes('501');
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        {isNoPg
          ? 'Deck features require a Postgres database. Set DATABASE_URL to enable allocations.'
          : 'Failed to load allocations. Please try again.'}
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Card Allocations</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          See where each card is used across your decks.
        </p>
      </div>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-3">
        {data?.cards.map((allocation) => (
          <div key={allocation.card_id} className="relative">
            <AllocationTile
              allocation={allocation}
              onTileClick={setSelected}
            />
            {selected?.card_id === allocation.card_id && (
              <AllocationPopover
                allocation={allocation}
                onRemoveFromDeck={handleRemove}
                onClose={() => setSelected(null)}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Existing Code Reuse

| Component/Hook | Where reused in this feature |
|----------------|------------------------------|
| `useImageCache(cardId)` | `AllocationTile` — same lazy image loading as `CardGallery` |
| `api.removeDeckCard(deckId, cardId)` | `CardAllocations` page remove handler — already in `client.ts` |
| `apiFetch` | New `getCardAllocations` method in `client.ts` |
| `ProtectedRoute` | Wrapping `/allocations` in `App.tsx` |
| `DeckRepository.require_deck_repo` guard | Reused (moved to `dependencies.py`) for allocations route |
| TanStack Query `useQuery` + `invalidateQueries` | Same pattern as DeckBuilder and Dashboard pages |

---

## Warnings

- **FastAPI route order:** `GET /api/cards/allocations` must be registered before
  `GET /api/cards/{id}` or any other parameterized card route. Failure to do so will cause
  `"allocations"` to be parsed as a card id (integer coercion will fail with a 422, but the
  wrong handler will be invoked). Confirm by checking that `router.get("/allocations")` is
  defined before `router.get("/{id}")` in `cards.py`.

- **`require_deck_repo` location:** If this guard is only in `decks.py`, it must be moved
  to `dependencies.py` before both route files can import it. This is a safe refactor with
  no behavior change.

- **Popover z-index:** The popover uses `absolute` positioning. If the grid tiles are
  inside a container with `overflow: hidden`, the popover will be clipped. Set
  `overflow: visible` on the containing element or use a portal (e.g., React `createPortal`
  into `document.body`). The current skeleton uses `left-full ml-2` which positions the
  popover to the right of the tile — ensure tiles near the right edge don't get clipped by
  the page container. An edge-case fix can be deferred to a follow-up.

- **`api.removeDeckCard` method name:** Confirm the exact method name in `client.ts`.
  It may be `deleteCardFromDeck`, `removeDeckCard`, or similar. Check the existing
  `DeckDetailModal.tsx` for the correct call pattern and use the same method name.
