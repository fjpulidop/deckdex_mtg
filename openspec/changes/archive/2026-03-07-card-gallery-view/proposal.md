## Why

DeckDex currently forces users to browse their MTG collection exclusively through a text table. MTG is a visually rich hobby — players identify cards by art, not spreadsheet rows. Leading platforms (Moxfield, Archidekt) default to gallery view because visual browsing dramatically speeds up collection review, deck planning, and card identification. Adding a gallery/grid view with proper image caching and lazy loading brings the dashboard to competitive parity while eliminating the per-mount image re-fetch waste that currently affects the card detail modal.

## What Changes

- **New `CardGallery` component** (`frontend/src/components/CardGallery.tsx`): responsive Tailwind grid of card image tiles (2 to 6 columns depending on viewport), each showing the card image with name/price overlay on hover, click opens the existing `CardDetailModal`.
- **View toggle in Dashboard toolbar**: table/gallery icon buttons rendered in the Dashboard header (above Filters); selection persisted to `localStorage` under key `'collectionView'`.
- **Reduced page size in gallery mode**: 24 cards per page (vs. 50 in table mode) to match typical image-heavy grid UX and avoid over-fetching on initial render.
- **Client-side image blob cache** (`frontend/src/hooks/useImageCache.ts`): module-level `Map<number, string>` keyed by card id, shared across all consumers (both `CardGallery` tiles and `CardDetailModal`). Blob URLs are created once and reused; the cache is not bounded (acceptable for localhost-scale collections).
- **Lazy loading via `IntersectionObserver`**: gallery tiles only fetch their image when they scroll into the viewport (with a small top margin). Tiles outside the viewport render a card-shaped skeleton placeholder.
- **Card-shaped skeleton placeholders**: 63:88 aspect-ratio divs with `animate-pulse` (matching the existing modal skeleton pattern) used both for loading state and before intersection.
- **i18n strings** in `en.json` and `es.json` for all new UI text (toggle aria-labels, skeleton alt text, empty states).
- **`CardCollectionViewProps` interface** extracted as a shared type so `CardTable` and `CardGallery` accept identical props, keeping Dashboard integration clean.

## Capabilities

### New Capabilities
- `card-gallery-view`: Responsive gallery/grid view of the card collection with image tiles, view toggle, client-side image cache, and IntersectionObserver-based lazy loading.

### Modified Capabilities
- `web-dashboard-ui`: Dashboard gains a view toggle (table vs. gallery) that persists to localStorage; page size adjusts per view mode; gallery renders via new `CardGallery` component; `CardCollectionViewProps` interface replaces the current ad-hoc prop bundle passed to `CardTable`.

## Impact

- **Frontend** (`frontend/src/`): New component `CardGallery.tsx`, new hook `useImageCache.ts`, modified `Dashboard.tsx` (toggle state + conditional render + page size logic), modified `CardTable.tsx` (export `CardCollectionViewProps` interface), modified `useCardImage.ts` (use shared cache), modified `en.json` + `es.json`.
- **Backend**: No changes required. Existing `GET /api/cards/{id}/image` endpoint serves gallery images unchanged. The image service already caches on the server filesystem; the new client cache eliminates redundant HTTP round-trips.
- **No database migration**: image caching is client-side (blob URLs in memory).

## Non-goals

- Server-sent thumbnail endpoints (no new backend image routes).
- Drag-and-drop reordering in gallery view.
- Virtual scroll (IntersectionObserver + page size reduction is sufficient for localhost-scale).
- Bounded/LRU client cache (unbounded Map is fine for typical collection sizes of hundreds to a few thousand cards; can be addressed later).
- Quantity editing in gallery tiles (only available in table view).
