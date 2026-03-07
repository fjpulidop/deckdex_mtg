# Tasks: Card Gallery View

Ordered implementation tasks. Each task is self-contained and can be reviewed independently. Execute in the listed order — later tasks depend on earlier ones.

---

## Task 1: Extract `CardCollectionViewProps` interface

**Layer**: Frontend — Types

**Files**:
- `frontend/src/types/collection.ts` (create)
- `frontend/src/components/CardTable.tsx` (modify)

**Description**:
Create `frontend/src/types/collection.ts` with the `CardCollectionViewProps` interface containing all current `CardTableProps` fields (cards, isLoading, onAdd, onImport, onUpdatePrices, updatingPrices, onRowClick, onQuantityChange, serverTotal, sortBy, sortDir, onSortChange, page, totalPages, onPageChange). Remove the local `CardTableProps` interface from `CardTable.tsx` and replace it with an import of `CardCollectionViewProps`. Export `CardCollectionViewProps` from `collection.ts`.

**Acceptance criteria**:
- `frontend/src/types/collection.ts` exports `CardCollectionViewProps`
- `CardTable.tsx` imports and uses `CardCollectionViewProps` instead of its own local type
- TypeScript compilation passes with no new errors (`npm run build` in frontend)

**Dependencies**: None

---

## Task 2: Implement `useImageCache` hook

**Layer**: Frontend — Hooks

**Files**:
- `frontend/src/hooks/useImageCache.ts` (create)

**Description**:
Create a new hook `useImageCache(cardId: number | null)` that maintains a module-level `Map<number, string>` (card id → blob URL) and a `Map<number, Promise<string>>` for in-flight deduplication.

Logic:
1. If `cardId` is null: return `{ src: null, loading: false, error: false }`.
2. If `imageCache.has(cardId)`: return `{ src: imageCache.get(cardId)!, loading: false, error: false }` (no useEffect needed; use `useState` initializer).
3. Otherwise: use `useEffect` to start the fetch. Check `inflightRequests` first — if a promise exists, attach to it. Otherwise call `api.fetchCardImage(cardId)`, store the promise in `inflightRequests`, on resolution store blob URL in `imageCache` and remove from `inflightRequests`, then call `setState`. On error set `error: true`.
4. Use a `cancelled` ref to guard against setting state after unmount.

Return type: `{ src: string | null; loading: boolean; error: boolean }` — identical to the current `useCardImage` return type.

**Acceptance criteria**:
- Hook returns `src` immediately (no loading flash) for already-cached card ids
- Two simultaneous calls for the same card id result in exactly one `api.fetchCardImage` call (verified by test or manual inspection)
- `useImageCache(null)` returns `{ src: null, loading: false, error: false }` synchronously
- TypeScript strict: no `any`

**Dependencies**: Task 1 (interface extraction) not required, but should be done before Task 3

---

## Task 3: Refactor `useCardImage` to delegate to `useImageCache`

**Layer**: Frontend — Hooks

**Files**:
- `frontend/src/hooks/useCardImage.ts` (modify)

**Description**:
Replace the implementation of `useCardImage` with a thin wrapper that calls `useImageCache` and returns its result. The hook signature and return type must remain identical so `CardDetailModal` requires no changes.

```ts
import { useImageCache } from './useImageCache';

export function useCardImage(cardId: number | null) {
  return useImageCache(cardId);
}
```

The old fetch-and-revoke logic (including blob URL revocation on unmount) is removed. This is intentional: revocation would invalidate the shared cache.

**Acceptance criteria**:
- `CardDetailModal` compiles and works without any changes to its code
- Opening the detail modal for a card already viewed in gallery (or vice versa) does NOT trigger a new network request

**Dependencies**: Task 2

---

## Task 4: Create `CardGallery` component

**Layer**: Frontend — Components

**Files**:
- `frontend/src/components/CardGallery.tsx` (create)

**Description**:
Implement the `CardGallery` component accepting `CardCollectionViewProps`. Structure:

1. **Toolbar**: Render Add card (green, `onAdd`), Import list (indigo outline, `onImport`), Update Prices (gray outline, `onUpdatePrices`) buttons when the respective prop is provided. Use the same button classes as CardTable toolbar for visual consistency. Use `t()` for all labels.

2. **Loading skeleton**: When `isLoading` is true, render a `div` with the responsive grid classes containing 24 `aspect-[63/88] rounded-lg bg-gray-200 dark:bg-gray-700 animate-pulse` divs. Return early.

3. **Empty state**: When `cards.length === 0` and not loading, render a centered empty message using `t('gallery.noCards')`.

4. **Grid**: `grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3` containing one `CardTile` per card.

5. **CardTile** (internal component or sub-component in same file):
   - `useRef<HTMLButtonElement>` + `useEffect` with `IntersectionObserver` (`rootMargin: '200px'`, disconnect after first intersection)
   - `isVisible` state (boolean, starts false)
   - Call `useImageCache(isVisible && card.id != null ? card.id : null)`
   - Render: `<button>` with `aspect-[63/88] rounded-lg overflow-hidden relative w-full focus:outline-none focus:ring-2 focus:ring-indigo-400 group`
   - Inside: animated placeholder when `loading` or `(isVisible && !src)`, the image when `src` exists, a static gray div when `!isVisible`, and the hover overlay
   - Overlay: `absolute inset-x-0 bottom-0 translate-y-full group-hover:translate-y-0 group-focus:translate-y-0 transition-transform duration-200 bg-gradient-to-t from-black/80 to-transparent p-2` containing card name (white, `text-xs font-semibold truncate`) and price (gray, `text-xs`)

6. **Pagination footer**: Identical to CardTable pagination footer (Previous button, "Page X of Y", Next button, total card count on left). Only rendered when `totalPages > 1`. Uses `t('cardTable.showing', ...)` and `t('cardTable.page', ...)` keys — reuse existing keys.

7. Scroll-to-top on page change via `containerRef` and `scrollIntoView`.

**Acceptance criteria**:
- Gallery renders 24 tiles in a responsive grid
- Clicking any tile calls `onRowClick` with the card
- Images only load when tiles approach the viewport (verified by Network tab: no image requests for off-screen tiles on initial load)
- Toolbar buttons function identically to CardTable toolbar
- Pagination controls navigate pages and scroll the grid to top
- Component compiles in TypeScript strict mode

**Dependencies**: Tasks 1, 2

---

## Task 5: Add view toggle and integrate gallery into Dashboard

**Layer**: Frontend — Pages

**Files**:
- `frontend/src/pages/Dashboard.tsx` (modify)

**Description**:

1. Add `CollectionView` type (`'table' | 'gallery'`) and view state initialized from `localStorage.getItem('collectionView')` (defaults to `'table'`).

2. Add `handleViewChange` callback that sets view, persists to `localStorage`, and resets `page` to 1.

3. Change `PAGE_SIZE` to be derived from `view`: `const PAGE_SIZE = view === 'gallery' ? 24 : 50;`.

4. Add the toggle button group to the JSX, placed between the Filters component and the CardTable/CardGallery. The toggle group has `role="group"` and `aria-label={t('viewToggle.label')}`. Use inline SVG icons (table rows icon and 2x2-grid icon). Active button: `bg-indigo-600 text-white`. Inactive: `bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400`.

5. Replace the `<CardTable ... />` JSX with a conditional: table view renders `CardTable`, gallery view renders `CardGallery` with identical props.

6. Add `import { CardGallery } from '../components/CardGallery';` at the top.

**Acceptance criteria**:
- Toggle switches between table and gallery views
- `aria-pressed` is correct on both buttons
- Switching view resets to page 1 and triggers a new fetch with updated limit
- LocalStorage persists the view across hard refreshes
- Table view is unchanged (no visual regression)

**Dependencies**: Tasks 1, 4

---

## Task 6: Add i18n strings (en.json + es.json)

**Layer**: Frontend — Localization

**Files**:
- `frontend/src/locales/en.json` (modify)
- `frontend/src/locales/es.json` (modify)

**Description**:
Add the following keys to both locale files. Add them as top-level objects at an appropriate location in the JSON (after `"cardTable"` section).

**en.json**:
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

**es.json**:
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

**Acceptance criteria**:
- Both JSON files are valid (no parse errors)
- All `t('viewToggle.*')` and `t('gallery.*')` calls in Dashboard and CardGallery resolve without missing-key warnings
- Switching language to Spanish shows Spanish strings in the toggle and gallery

**Dependencies**: Tasks 4, 5 (strings must be used before they can be verified)

---

## Task 7: Tests for `useImageCache` hook

**Layer**: Tests

**Files**:
- `frontend/src/hooks/useImageCache.test.ts` (create)

**Description**:
Write Vitest + React Testing Library tests covering:

1. **Cache hit**: Mock `api.fetchCardImage`. Call the hook twice with the same card id. Assert `api.fetchCardImage` was called exactly once.
2. **Null id**: Call `useImageCache(null)`. Assert immediate return of `{ src: null, loading: false, error: false }` with no API calls.
3. **Error state**: Mock `api.fetchCardImage` to reject. Assert hook returns `{ src: null, loading: false, error: true }`.
4. **In-flight dedup**: Two renders with same id, first fetch not yet resolved. Assert only one call to `api.fetchCardImage`.

Use `vi.mock('../api/client')` to mock the `api` object. Use `renderHook` from `@testing-library/react`.

**Acceptance criteria**:
- All 4 test cases pass under `npm run test` (Vitest)
- No TypeScript errors in the test file

**Dependencies**: Task 2

---

## Task 8: Tests for `CardGallery` component

**Layer**: Tests

**Files**:
- `frontend/src/components/CardGallery.test.tsx` (create)

**Description**:
Write Vitest + React Testing Library tests covering:

1. **Renders loading skeletons**: Pass `isLoading={true}` and assert 24 skeleton divs are present (check for `animate-pulse` class count).
2. **Renders card tiles**: Pass `cards` array with 3 cards and assert 3 `<button>` elements with correct `aria-label` matching card names.
3. **Tile click calls onRowClick**: Click a tile and assert `onRowClick` was called with the corresponding card object.
4. **Empty state**: Pass `cards={[]}` and `isLoading={false}` and assert the empty state message is shown.
5. **Toolbar buttons render**: Pass `onAdd`, `onImport`, `onUpdatePrices` props and assert the corresponding buttons are present.

Use `vi.mock('../hooks/useImageCache')` to return `{ src: 'blob:test', loading: false, error: false }` for all calls. Mock `IntersectionObserver` if needed (set `isVisible = true` by default in the mock).

**Acceptance criteria**:
- All 5 test cases pass
- Tests run in isolation (no real API calls)

**Dependencies**: Tasks 4, 6

---

## Task 9: Tests for Dashboard view toggle

**Layer**: Tests

**Files**:
- `frontend/src/pages/Dashboard.test.tsx` (modify existing or create)

**Description**:
Add test cases to the Dashboard test suite:

1. **Default renders table view**: On first render (no localStorage value), assert `CardTable` is rendered and `CardGallery` is not.
2. **Toggle to gallery view**: Click the gallery toggle button; assert `CardGallery` renders and `CardTable` does not.
3. **localStorage persisted**: After clicking gallery toggle, assert `localStorage.getItem('collectionView')` returns `'gallery'`.
4. **Gallery mode page size**: In gallery mode, assert the `useCards` hook (or API call) receives `limit=24`.

Mock `CardTable` and `CardGallery` as simple `<div data-testid="card-table"/>` and `<div data-testid="card-gallery"/>` to keep the test focused on Dashboard behavior.

**Acceptance criteria**:
- All 4 test cases pass
- No regressions in existing Dashboard tests

**Dependencies**: Tasks 4, 5, 6
