## Why

The gallery view shipped with sort props wired from Dashboard but never renders sort UI, leaving gallery users unable to reorder cards. The grid container has no semantic role, so screen readers see a flat sequence of unlabeled interactive elements. Image fetch errors silently cycle into the same loading skeleton as genuine in-progress loads, giving users no indication that content failed to load.

## What Changes

- **Sort bar in gallery toolbar**: Render a sort-by select and direction toggle inside the gallery toolbar using the already-passed `sortBy`, `sortDir`, and `onSortChange` props. Supports the same columns available in table view (name, type, rarity, price, Added).
- **Semantic grid role**: Add `role="list"` to the grid container and `role="listitem"` to each tile wrapper so assistive technology can enumerate items and announce count.
- **Image error fallback**: When `useImageCache` resolves to `error: true`, render a distinct static placeholder (card back icon + localized text) instead of the infinite skeleton animation. The skeleton is reserved for genuine loading state only.
- **Quantity badge on tile**: Surface the `quantity` field from the `Card` type as a small badge on each tile when `quantity > 1`, consistent with the table view showing qty. The `onQuantityChange` prop remains unimplemented in gallery (out of scope — editing quantity belongs to the detail modal).

## Capabilities

### New Capabilities

- None

### Modified Capabilities

- `web-dashboard-ui`: Gallery sort controls, grid semantic roles, and image error state are new behavioral requirements for the gallery view. Delta spec covers new gallery-specific requirements only.

## Impact

- `frontend/src/components/CardGallery.tsx`: Sort bar, grid role, tile role, error placeholder rendering.
- `frontend/src/hooks/useImageCache.ts`: No code changes needed — `error` field already exposed.
- `frontend/src/locales/en.json` and `es.json`: New keys for gallery sort labels and image error text.
- No backend changes. No API changes. No migration.

## Non-goals

- Inline quantity editing in gallery mode (belongs to card detail modal).
- Persisting gallery sort separately from table sort (they share the same `sortBy`/`sortDir` state in Dashboard — intentional, consistent experience when toggling views).
- Keyboard-operable sort controls beyond native `<select>` and `<button>` (native elements are already keyboard-accessible).
