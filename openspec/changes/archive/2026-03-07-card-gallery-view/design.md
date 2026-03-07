# Design: Card Gallery/Grid View

## Overview

This design adds a gallery (grid) view to the Dashboard, alongside the existing table view. Users toggle between views via icon buttons in the Dashboard toolbar. The gallery renders card images in a responsive grid with lazy loading and uses a shared client-side blob cache to eliminate redundant HTTP requests across the app session.

---

## 1. Shared Props Interface: `CardCollectionViewProps`

Both `CardTable` and the new `CardGallery` accept identical collection-level props. Extract a shared interface in `CardTable.tsx` (or a new `frontend/src/types/collection.ts` file) and re-export it.

```ts
// frontend/src/types/collection.ts  (new file)
import type { Card } from '../api/client';

export interface CardCollectionViewProps {
  cards: Card[];
  isLoading?: boolean;
  onAdd?: () => void;
  onImport?: () => void;
  onUpdatePrices?: () => void;
  updatingPrices?: boolean;
  onRowClick?: (card: Card) => void;
  onQuantityChange?: (id: number, qty: number) => void;
  serverTotal?: number;
  sortBy?: string;
  sortDir?: 'asc' | 'desc';
  onSortChange?: (key: string, dir: 'asc' | 'desc') => void;
  page?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
}
```

`CardTable` imports and re-uses this type (replacing its local `CardTableProps`). `CardGallery` accepts the same type.

---

## 2. Client-Side Image Cache: `useImageCache` hook

**File**: `frontend/src/hooks/useImageCache.ts`

The current `useCardImage` hook creates a new blob URL on each mount and revokes it on unmount. This means reopening the detail modal re-fetches from the backend. The gallery would multiply this problem (24 tiles each independently fetching).

**Design**: module-level singleton `Map<number, string>` that persists across component mounts for the lifetime of the browser session.

```ts
// Module-level cache — lives for the browser session
const imageCache = new Map<number, string>();

// Tracks in-flight requests to avoid duplicate fetches for the same card
const inflightRequests = new Map<number, Promise<string>>();

export function useImageCache(cardId: number | null): {
  src: string | null;
  loading: boolean;
  error: boolean;
}
```

**Behavior**:
- If `cardId` is null: return `{ src: null, loading: false, error: false }`.
- If `imageCache.has(cardId)`: return `{ src: imageCache.get(cardId), loading: false, error: false }` immediately (no effect needed).
- If an in-flight request exists for `cardId` (via `inflightRequests`): attach to it, update state on resolution.
- Otherwise: create the fetch via `api.fetchCardImage(cardId)`, store the promise in `inflightRequests`, on success store the blob URL in `imageCache` and remove from `inflightRequests`.
- **No revocation**: blob URLs are retained for the session. This is intentional — revoking on unmount defeats the cache. Memory impact is negligible (typical JPEG thumbnails are 30–80KB each; 500 unique cards = ~40MB max, well within browser limits for a localhost app).
- `useCardImage` is refactored to use `useImageCache` internally so existing usage in `CardDetailModal` transparently benefits.

**Decision rationale**: A module-level Map is the simplest approach that requires no React Context, no provider changes, and works identically across all components. An LRU bound is explicitly out of scope.

---

## 3. View Toggle in Dashboard

**File**: `frontend/src/pages/Dashboard.tsx`

### Toggle State

```ts
type CollectionView = 'table' | 'gallery';

// Persisted to localStorage
const [view, setView] = useState<CollectionView>(() => {
  const stored = localStorage.getItem('collectionView');
  return stored === 'gallery' ? 'gallery' : 'table';
});

const handleViewChange = (next: CollectionView) => {
  setView(next);
  localStorage.setItem('collectionView', next);
  setPage(1); // reset pagination when switching views
};
```

### Page Size

```ts
const PAGE_SIZE = view === 'gallery' ? 24 : 50;
```

The page size feeds directly into the `useCards` query params. Switching views resets `page` to 1 and triggers a re-fetch with the new limit. Because TanStack Query keys include `limit`, switching views will hit a new cache key — which is acceptable; the 30s stale time means a switch back to table will use the cached table response.

### Toolbar Placement

The toggle buttons render as a small button group placed to the right of the Filters component, in the same container row as the result count chip. Specifically: a `div` with `flex items-center justify-between` wrapping the filter chips row and the view toggle group.

```tsx
{/* View toggle — table icon vs. gallery grid icon */}
<div role="group" aria-label={t('viewToggle.label')} className="flex border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
  <button
    onClick={() => handleViewChange('table')}
    aria-pressed={view === 'table'}
    aria-label={t('viewToggle.table')}
    className={`px-3 py-2 text-sm ${view === 'table' ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
  >
    {/* Table icon: three horizontal lines */}
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <rect x="0" y="2" width="16" height="2" rx="1"/>
      <rect x="0" y="7" width="16" height="2" rx="1"/>
      <rect x="0" y="12" width="16" height="2" rx="1"/>
    </svg>
  </button>
  <button
    onClick={() => handleViewChange('gallery')}
    aria-pressed={view === 'gallery'}
    aria-label={t('viewToggle.gallery')}
    className={`px-3 py-2 text-sm border-l border-gray-300 dark:border-gray-600 ${view === 'gallery' ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
  >
    {/* Gallery icon: 2x2 grid squares */}
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <rect x="0" y="0" width="7" height="7" rx="1"/>
      <rect x="9" y="0" width="7" height="7" rx="1"/>
      <rect x="0" y="9" width="7" height="7" rx="1"/>
      <rect x="9" y="9" width="7" height="7" rx="1"/>
    </svg>
  </button>
</div>
```

### Conditional Render

```tsx
{view === 'table' ? (
  <CardTable
    cards={displayCards}
    isLoading={isLoading}
    {/* ...all existing props unchanged */}
  />
) : (
  <CardGallery
    cards={displayCards}
    isLoading={isLoading}
    onAdd={handleAddCard}
    onImport={handleImport}
    onUpdatePrices={handleUpdatePrices}
    updatingPrices={triggerPriceUpdate.isPending}
    onRowClick={handleRowClick}
    serverTotal={serverTotal}
    sortBy={sortBy}
    sortDir={sortDir}
    onSortChange={handleSortChange}
    page={page}
    totalPages={totalPages}
    onPageChange={handlePageChange}
  />
)}
```

---

## 4. CardGallery Component

**File**: `frontend/src/components/CardGallery.tsx`

### Responsive Grid

```
xs (< 640px):  2 columns
sm (640px+):   3 columns
md (768px+):   4 columns
lg (1024px+):  5 columns
xl (1280px+):  6 columns
```

Tailwind class: `grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3`

### Card Tile Structure

Each tile is a `<button>` element (keyboard-accessible, `onClick` opens modal) with:
- Fixed aspect ratio: `aspect-[63/88]` (standard MTG card ratio) via Tailwind's `aspect-ratio` utility
- Overflow hidden, rounded corners
- The card image fills the tile via `object-cover`
- Hover: name/price overlay slides up from the bottom (opacity transition)
- Skeleton placeholder when image is loading or intersection not triggered

```tsx
function CardTile({ card, onRowClick }: { card: Card; onRowClick?: (card: Card) => void }) {
  const { t } = useTranslation();
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLButtonElement>(null);

  // IntersectionObserver: trigger image fetch when tile enters viewport
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setIsVisible(true); observer.disconnect(); } },
      { rootMargin: '200px' } // preload 200px before entering viewport
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Only fetch image when visible
  const cardId = isVisible && card.id != null ? card.id : null;
  const { src, loading } = useImageCache(cardId);

  return (
    <button
      ref={ref}
      type="button"
      onClick={() => onRowClick?.(card)}
      aria-label={t('gallery.tileLabel', { name: card.name ?? 'Unknown' })}
      className="relative aspect-[63/88] rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 group w-full"
    >
      {/* Skeleton */}
      {(loading || (!src && isVisible)) && (
        <div className="absolute inset-0 animate-pulse bg-gray-300 dark:bg-gray-600" aria-hidden />
      )}

      {/* Card image */}
      {src && (
        <img
          src={src}
          alt={card.name ?? t('gallery.unknownCard')}
          className="absolute inset-0 w-full h-full object-cover"
          loading="lazy"
        />
      )}

      {/* Not-yet-visible placeholder (pre-intersection) */}
      {!isVisible && (
        <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700" aria-hidden />
      )}

      {/* Hover overlay: name + price */}
      <div className="absolute inset-x-0 bottom-0 translate-y-full group-hover:translate-y-0 group-focus:translate-y-0 transition-transform duration-200 bg-gradient-to-t from-black/80 to-transparent p-2">
        <p className="text-white text-xs font-semibold leading-tight truncate">{card.name ?? '—'}</p>
        {card.price && card.price !== 'N/A' && (
          <p className="text-gray-300 text-xs mt-0.5">€{card.price}</p>
        )}
      </div>
    </button>
  );
}
```

### Toolbar

The gallery toolbar mirrors the CardTable toolbar (Add card, Import list, Update Prices buttons) using the same Tailwind classes for visual consistency. Sorting controls are intentionally omitted from the gallery toolbar — sort is still controlled by `onSortChange` passed from Dashboard, but the sort column/direction UI would clutter the gallery. A future enhancement can add a sort dropdown above the grid.

**Decision**: Dashboard already owns sort state and passes it down. Gallery receives `sortBy`/`sortDir`/`onSortChange` but does not render column headers. The active sort is visible to the user via the existing dashboard sort state (no dedicated sort UI in gallery for this release).

### Pagination

The gallery uses the same pagination footer pattern as CardTable: Previous/Next buttons with page X of Y display, built from the passed-in `page`, `totalPages`, and `onPageChange` props. The component renders a scroll-to-top on page change via `containerRef.current?.scrollIntoView`.

### Loading Skeleton

When `isLoading` is true (initial page load), render a grid of 24 card-shaped skeleton placeholders instead of tiles:

```tsx
if (isLoading) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
      {Array.from({ length: 24 }).map((_, i) => (
        <div key={i} className="aspect-[63/88] rounded-lg bg-gray-200 dark:bg-gray-700 animate-pulse" />
      ))}
    </div>
  );
}
```

### Empty State

```tsx
{cards.length === 0 && !isLoading && (
  <div className="col-span-full py-20 text-center text-gray-500 dark:text-gray-400">
    <p className="text-lg font-medium">{t('gallery.noCards')}</p>
  </div>
)}
```

---

## 5. Refactoring `useCardImage`

**File**: `frontend/src/hooks/useCardImage.ts`

Rewrite to delegate to `useImageCache` so existing `CardDetailModal` usage benefits automatically:

```ts
export function useCardImage(cardId: number | null): CardImageState {
  return useImageCache(cardId);
}
```

This is a pure delegation — the public interface of `useCardImage` is unchanged, so `CardDetailModal` requires no changes.

---

## 6. i18n Strings

### `frontend/src/locales/en.json` additions

```json
"viewToggle": {
  "label": "Switch collection view",
  "table": "Table view",
  "gallery": "Gallery view"
},
"gallery": {
  "tileLabel": "View details for {{name}}",
  "unknownCard": "Unknown card",
  "noCards": "No cards found. Try adjusting your filters.",
  "loading": "Loading cards…"
}
```

### `frontend/src/locales/es.json` additions

```json
"viewToggle": {
  "label": "Cambiar vista de la colección",
  "table": "Vista de tabla",
  "gallery": "Vista de galería"
},
"gallery": {
  "tileLabel": "Ver detalles de {{name}}",
  "unknownCard": "Carta desconocida",
  "noCards": "No se encontraron cartas. Prueba ajustando los filtros.",
  "loading": "Cargando cartas…"
}
```

---

## 7. Backend: No Changes Required

The existing `GET /api/cards/{id}/image` endpoint already serves image bytes efficiently. The backend ImageStore caches images on the filesystem so subsequent requests are disk reads. The new client-side cache eliminates redundant HTTP requests entirely after the first fetch. No new endpoints are needed.

**Why no batch image endpoint**: Lazy loading with IntersectionObserver naturally limits concurrent requests to ~6–12 visible tiles at once (browser's HTTP/2 connection limit handles parallelism). A batch endpoint would add backend complexity for marginal benefit.

---

## 8. File Summary

| File | Change |
|------|--------|
| `frontend/src/types/collection.ts` | New — `CardCollectionViewProps` interface |
| `frontend/src/hooks/useImageCache.ts` | New — module-level blob URL cache |
| `frontend/src/hooks/useCardImage.ts` | Refactor — delegates to `useImageCache` |
| `frontend/src/components/CardGallery.tsx` | New — gallery grid component |
| `frontend/src/components/CardTable.tsx` | Modify — import and re-export `CardCollectionViewProps` |
| `frontend/src/pages/Dashboard.tsx` | Modify — view toggle state, page size logic, conditional render |
| `frontend/src/locales/en.json` | Modify — add `viewToggle` + `gallery` keys |
| `frontend/src/locales/es.json` | Modify — add `viewToggle` + `gallery` keys |

---

## 9. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Module-level Map for image cache | Simplest shared state; no provider needed; works across all components; appropriate for localhost-scale |
| IntersectionObserver over virtual scroll | Sufficient for 24-card pages; simpler; no external deps |
| 24 cards in gallery mode | Standard grid UX; reduces initial image load burst; 4 rows of 6 at 1280px |
| No sort UI in gallery | Sort state is already owned by Dashboard; adding a dropdown is a scope-creep risk; can be added later |
| No quantity edit in gallery | Tiles are too small; quantity editing belongs in table view or detail modal |
| Blob URLs not revoked | Intentional for caching; localhost app has no meaningful memory pressure constraint |
| `localStorage` for view preference | Same pattern as theme preference; survives page reload; no backend needed |
