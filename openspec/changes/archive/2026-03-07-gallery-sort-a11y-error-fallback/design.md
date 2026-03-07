## Overview

Three focused changes to `CardGallery.tsx` and locale files. No backend, no new hooks, no new components beyond what is already present in the file.

---

## 1. Sort Controls in Gallery Toolbar

### Problem

`CardGallery` receives `sortBy`, `sortDir`, and `onSortChange` from `Dashboard.tsx` (line 362-366 of Dashboard) but never destructures or uses them. The toolbar renders action buttons (Add, Import, Update Prices) but no sort UI. Users in gallery mode have no way to reorder cards.

### Design Decision: Inline Toolbar Sort Bar (not a separate component)

A `<select>` for the column and a toggle `<button>` for direction, placed in the same toolbar `<div>` used for action buttons, separated by a `ml-auto` spacer to push sort controls to the right. This matches common gallery/grid UI patterns and requires no new component or file.

**Why not a separate `SortBar` component?** The sort state is simple (two values, one callback), the gallery toolbar already exists as a local JSX block, and the project convention for small UI blocks is to keep them inline within the component they belong to. Introducing a new component for two controls adds abstraction without benefit.

### Sort Columns

Reuse the same column set as `CardTable`: `name`, `type`, `rarity`, `price`, `created_at` (labelled "Added"). These map exactly to the keys handled by Dashboard's `handleSortChange` and the `API_SORT_COLUMN` map (`price` → `price_eur`). No new mapping needed.

### Props Destructuring

Add `sortBy`, `sortDir`, `onSortChange` to the destructured props in `CardGallery`. These are already typed as optional in `CardCollectionViewProps` (`frontend/src/types/collection.ts`).

### Sort Bar JSX (inside existing toolbar div)

```tsx
// Right side of toolbar — only rendered when onSortChange is provided
{onSortChange && (
  <div className="ml-auto flex items-center gap-2">
    <label htmlFor="gallery-sort-by" className="text-sm text-gray-600 dark:text-gray-400 sr-only">
      {t('gallery.sortBy')}
    </label>
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
      {sortDir === 'asc' ? '↑' : '↓'}
    </button>
  </div>
)}
```

The sort bar also appears in the loading skeleton toolbar for visual consistency (props are available there too — toolbar JSX is shared via the `toolbar` const).

---

## 2. Semantic Grid Roles

### Problem

The grid `<div>` at line 181 of `CardGallery.tsx` has only Tailwind layout classes. Each `CardTile` is a `<button>` — correct for interactivity but the container gives no enumeration semantics. Screen readers cannot tell users how many items exist or navigate by item.

### Design Decision: `role="list"` / `role="listitem"` over `role="grid"`

`role="grid"` implies two-dimensional keyboard navigation (arrow keys between cells), which we are not implementing. `role="list"` with `role="listitem"` wrappers is the correct semantic for a collection of equivalent interactive items where count announcement is needed but no two-dimensional navigation is warranted. This is consistent with how `CardTable` rows are announced (the native `<table>` / `<tr>` structure provides equivalent semantics there).

### Implementation

Wrap each `CardTile` in a `<div role="listitem">` and add `role="list"` to the grid container:

```tsx
<div role="list" className={`p-4 ${GRID_CLASSES}`}>
  {cards.map((card, index) => (
    <div key={card.id ?? index} role="listitem">
      <CardTile card={card} onRowClick={onRowClick} />
    </div>
  ))}
</div>
```

The `key` moves from `CardTile` to the wrapper `<div>`, which is correct — React keys belong on the outermost element of the mapped expression.

The loading skeleton grid does not need `role="list"` (skeleton items are `aria-hidden`; the container is purely presentational during load).

---

## 3. Image Error Fallback

### Problem

`useImageCache` already distinguishes three states via `{ src, loading, error }`. However, `CardTile` renders:

```tsx
{isVisible && (loading || (!src)) && (
  <div className="absolute inset-0 animate-pulse bg-gray-300 dark:bg-gray-600" aria-hidden />
)}
```

When `error` is `true`, `src` is `null` and `loading` is `false`, so `(!src)` is `true` and the skeleton animation plays indefinitely. The user sees an endlessly pulsing tile with no indication that the image failed to load.

### Design Decision: Explicit Error Branch in CardTile

Add a separate render branch that checks `error` before the loading branch. When `error` is `true`, render a static placeholder with a card-back SVG icon and localized "Image unavailable" text. This is the same label already used in `CardDetailModal` (`cardDetail.imageUnavailable` in `en.json`), so no new locale key is required for the text — only new gallery-specific keys for the aria-label of the sort controls are needed.

### Implementation

```tsx
// Error placeholder (checked before loading skeleton)
{isVisible && error && (
  <div
    className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 gap-1 p-2"
    aria-label={t('cardDetail.imageUnavailable')}
  >
    {/* Card back placeholder icon */}
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

{/* Loading skeleton — only shown when genuinely loading (not error) */}
{isVisible && !error && (loading || !src) && (
  <div className="absolute inset-0 animate-pulse bg-gray-300 dark:bg-gray-600" aria-hidden />
)}
```

Reusing `cardDetail.imageUnavailable` is intentional — the text is identical in meaning and avoids key proliferation. The SVG icon is inline (no import) since it's a single small shape used only here.

---

## 4. Quantity Badge

### Problem

`onQuantityChange` is in `CardCollectionViewProps` but `CardGallery` never reads `quantity` from the card. The table view has a dedicated Qty column. Gallery users have no visual indicator that they own multiple copies of a card.

### Design Decision: Passive Badge Only (no edit interaction)

Render a small numeric badge in the top-right corner of the tile when `card.quantity > 1`. No click handler. Editing quantity happens via the card detail modal (accessible by clicking the tile). This is consistent with how the design treats gallery mode as a visual browse experience, not an edit surface.

```tsx
{(card.quantity ?? 0) > 1 && (
  <div
    className="absolute top-1 right-1 z-10 bg-indigo-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
    aria-label={t('gallery.quantityBadge', { count: card.quantity })}
  >
    {card.quantity}
  </div>
)}
```

Placed inside `CardTile` after the pre-intersection placeholder block, so it renders at all times once `isVisible` is true (the badge position is on top of whatever state the image is in).

---

## 5. Locale Keys

### New keys required in `en.json` and `es.json` under `gallery`:

| Key | English | Spanish |
|-----|---------|---------|
| `gallery.sortBy` | `"Sort by"` | `"Ordenar por"` |
| `gallery.sortDirAsc` | `"Sort ascending"` | `"Orden ascendente"` |
| `gallery.sortDirDesc` | `"Sort descending"` | `"Orden descendente"` |
| `gallery.quantityBadge` | `"{{count}} copies"` | `"{{count}} copias"` |

No new keys needed for the error placeholder (reuses `cardDetail.imageUnavailable`).

---

## File Change Summary

| File | Nature of Change |
|------|-----------------|
| `frontend/src/components/CardGallery.tsx` | Destructure sort props; add sort bar in toolbar; add `role="list"` on grid; wrap tiles in `role="listitem"`; add error branch in `CardTile`; add quantity badge in `CardTile` |
| `frontend/src/locales/en.json` | Add 4 keys under `gallery` |
| `frontend/src/locales/es.json` | Add 4 keys under `gallery` |
| `frontend/src/hooks/useImageCache.ts` | No changes |
| `frontend/src/types/collection.ts` | No changes |
| `frontend/src/pages/Dashboard.tsx` | No changes |
