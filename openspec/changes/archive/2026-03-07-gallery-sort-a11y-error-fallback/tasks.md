## Tasks

### Task 1: Add locale keys for gallery sort controls and quantity badge

**Files:** `frontend/src/locales/en.json`, `frontend/src/locales/es.json`

Add the following keys under the existing `"gallery"` object in both locale files:

```json
"sortBy": "Sort by",
"sortDirAsc": "Sort ascending",
"sortDirDesc": "Sort descending",
"quantityBadge": "{{count}} copies"
```

Spanish equivalents:
```json
"sortBy": "Ordenar por",
"sortDirAsc": "Orden ascendente",
"sortDirDesc": "Orden descendente",
"quantityBadge": "{{count}} copias"
```

**Acceptance criteria:**
- Both locale files have all four new keys under `gallery`.
- No existing keys are removed or renamed.
- `npm run build` (or `npm run lint`) passes with no TypeScript errors.

**Dependencies:** None. Safe to start immediately.

---

### Task 2: Fix image error fallback in CardTile

**File:** `frontend/src/components/CardGallery.tsx`

In the `CardTile` function body, destructure `error` from the `useImageCache` result (it is already returned by the hook at line 43 — just add it to the destructuring: `const { src, loading, error } = useImageCache(cardId)`).

Replace the current single loading/skeleton block:

```tsx
{isVisible && (loading || (!src)) && (
  <div className="absolute inset-0 animate-pulse bg-gray-300 dark:bg-gray-600" aria-hidden />
)}
```

With two separate branches — error placeholder first, then loading skeleton:

```tsx
{/* Error placeholder — static, no animation */}
{isVisible && error && (
  <div
    className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 gap-1 p-2"
    aria-label={t('cardDetail.imageUnavailable')}
  >
    <svg
      className="w-8 h-8 opacity-40"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      aria-hidden="true"
    >
      <rect x="3" y="2" width="18" height="20" rx="2" />
      <circle cx="12" cy="11" r="4" />
      <path d="M8 18c0-2.2 1.8-4 4-4s4 1.8 4 4" />
    </svg>
    <span className="text-xs text-center leading-tight">
      {t('cardDetail.imageUnavailable')}
    </span>
  </div>
)}

{/* Loading skeleton — only when genuinely loading */}
{isVisible && !error && (loading || !src) && (
  <div className="absolute inset-0 animate-pulse bg-gray-300 dark:bg-gray-600" aria-hidden />
)}
```

**Acceptance criteria:**
- When `useImageCache` returns `{ error: true }`, the tile shows the static placeholder (no `animate-pulse` class).
- When `useImageCache` returns `{ loading: true }`, the tile shows the pulsing skeleton.
- When `useImageCache` returns `{ src: "blob:..." }`, the tile shows the image (existing behavior unchanged).
- No TypeScript errors.

**Dependencies:** Task 1 (locale keys must exist before referencing `t('cardDetail.imageUnavailable')` — though that key already exists, confirm no import changes needed).

---

### Task 3: Add quantity badge to CardTile

**File:** `frontend/src/components/CardGallery.tsx`

Inside the `CardTile` return, after the pre-intersection placeholder block and before the hover overlay `<div>`, add the quantity badge:

```tsx
{/* Quantity badge — shown for multi-copy cards */}
{(card.quantity ?? 0) > 1 && (
  <div
    className="absolute top-1 right-1 z-10 bg-indigo-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
    aria-label={t('gallery.quantityBadge', { count: card.quantity })}
  >
    {card.quantity}
  </div>
)}
```

**Acceptance criteria:**
- Cards with `quantity > 1` show a numeric badge in the top-right corner of the tile.
- Cards with `quantity <= 1` or `quantity` undefined show no badge.
- The badge uses the `gallery.quantityBadge` locale key for its `aria-label`.
- Badge does not interfere with the hover overlay or the card image.

**Dependencies:** Task 1 (locale key `gallery.quantityBadge` must exist).

---

### Task 4: Add semantic list roles to the gallery grid

**File:** `frontend/src/components/CardGallery.tsx`

In the main return (not the loading skeleton), locate the grid `<div>` at the cards map:

```tsx
<div className={`p-4 ${GRID_CLASSES}`}>
  {cards.map((card, index) => (
    <CardTile
      key={card.id ?? index}
      card={card}
      onRowClick={onRowClick}
    />
  ))}
</div>
```

Change it to:

```tsx
<div role="list" className={`p-4 ${GRID_CLASSES}`}>
  {cards.map((card, index) => (
    <div key={card.id ?? index} role="listitem">
      <CardTile card={card} onRowClick={onRowClick} />
    </div>
  ))}
</div>
```

Note: The `key` prop moves from `<CardTile>` to the outer `<div role="listitem">`.

**Acceptance criteria:**
- Grid container has `role="list"`.
- Each tile is wrapped in `<div role="listitem">`.
- Visual output is unchanged (the wrapper `<div>` is unstyled and does not break the CSS grid layout).
- The loading skeleton grid is NOT changed (skeleton items are decorative, not list items).

**Dependencies:** None.

---

### Task 5: Wire sort controls into the gallery toolbar

**File:** `frontend/src/components/CardGallery.tsx`

**Step 5a — Destructure sort props:**

Add `sortBy`, `sortDir`, `onSortChange` to the destructured props in the `CardGallery` function signature. These are already declared as optional in `CardCollectionViewProps`.

```tsx
export function CardGallery({
  cards,
  isLoading,
  onAdd,
  onImport,
  onUpdatePrices,
  updatingPrices,
  onRowClick,
  serverTotal,
  page = 1,
  totalPages = 1,
  onPageChange,
  sortBy,
  sortDir,
  onSortChange,
}: CardCollectionViewProps) {
```

**Step 5b — Add sort bar to toolbar:**

The `toolbar` const already contains the action buttons. Append the sort bar to the right of the existing button group. The full `toolbar` const becomes:

```tsx
const toolbar = (onAdd || onImport || onUpdatePrices || onSortChange) && (
  <div className="px-6 py-3 border-b border-gray-200 dark:border-gray-600 flex flex-wrap items-center gap-2">
    {onAdd && (
      <button
        type="button"
        onClick={onAdd}
        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm dark:bg-green-500 dark:hover:bg-green-600"
      >
        {t('cardTable.addCard')}
      </button>
    )}
    {onImport && (
      <button
        type="button"
        onClick={onImport}
        className="px-4 py-2 border border-indigo-600 text-indigo-600 bg-transparent rounded hover:bg-indigo-50 text-sm dark:border-indigo-400 dark:text-indigo-400 dark:hover:bg-indigo-950"
      >
        {t('cardTable.importList')}
      </button>
    )}
    {onUpdatePrices && (
      <button
        type="button"
        onClick={onUpdatePrices}
        disabled={updatingPrices}
        className="px-4 py-2 border border-gray-400 text-gray-600 bg-transparent rounded hover:bg-gray-50 text-sm disabled:opacity-50 dark:border-gray-500 dark:text-gray-400 dark:hover:bg-gray-800"
      >
        {updatingPrices ? t('cardTable.starting') : t('cardTable.updatePrices')}
      </button>
    )}
    {onSortChange && (
      <div className="ml-auto flex items-center gap-2">
        <select
          id="gallery-sort-by"
          value={sortBy ?? 'created_at'}
          onChange={(e) => onSortChange(e.target.value, sortDir ?? 'desc')}
          className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200"
          aria-label={t('gallery.sortBy')}
        >
          <option value="name">{t('cardTable.columns.name')}</option>
          <option value="type">{t('cardTable.columns.type')}</option>
          <option value="rarity">{t('cardTable.columns.rarity')}</option>
          <option value="price">{t('cardTable.columns.price')}</option>
          <option value="created_at">{t('cardTable.columns.added')}</option>
        </select>
        <button
          type="button"
          onClick={() => onSortChange(sortBy ?? 'created_at', sortDir === 'asc' ? 'desc' : 'asc')}
          aria-label={sortDir === 'asc' ? t('gallery.sortDirDesc') : t('gallery.sortDirAsc')}
          className="p-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600"
        >
          {sortDir === 'asc' ? '\u2191' : '\u2193'}
        </button>
      </div>
    )}
  </div>
);
```

**Acceptance criteria:**
- Sort `<select>` and direction `<button>` appear in the gallery toolbar when `onSortChange` is provided.
- Changing the select calls `onSortChange(newColumn, currentDir)`.
- Clicking the direction button calls `onSortChange(currentColumn, toggledDir)`.
- Direction button `aria-label` correctly describes the next action ("Sort ascending" when currently descending, and vice versa).
- Action buttons (Add, Import, Update Prices) are unaffected in position and behavior.
- The toolbar also appears in the loading skeleton path (already the case because `toolbar` const is rendered in both branches — no change needed there).
- `npm run lint` passes with no new TypeScript or ESLint errors.

**Dependencies:** Task 1 (locale keys `gallery.sortBy`, `gallery.sortDirAsc`, `gallery.sortDirDesc` must exist).

---

### Task 6: Verify end-to-end in browser

**No file changes. Manual verification.**

Open the dashboard in gallery view and confirm:

1. **Sort controls visible**: Sort select and direction toggle appear in the toolbar to the right of action buttons.
2. **Sort works**: Changing the sort column or direction re-fetches cards and reorders the gallery.
3. **Shared sort state**: Switching to table view after changing sort in gallery shows the same sort column/direction.
4. **Quantity badge**: Any card with quantity > 1 shows the numeric badge in the top-right of its tile.
5. **Error fallback**: Simulate an image error (e.g., temporarily break the image endpoint or use a card id that returns 404) — the tile should show the static placeholder, not the pulse animation.
6. **Accessibility**: Run a screen reader (VoiceOver/NVDA) or browser a11y audit — grid should be announced as a list with item count.

**Acceptance criteria:**
- All six items above are confirmed working in the browser.
- No regressions in table view.
- No console errors introduced.
