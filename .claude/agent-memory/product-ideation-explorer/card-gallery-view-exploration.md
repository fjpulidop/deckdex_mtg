# Card Gallery View Exploration

**Date:** 2026-03-07
**Status:** Exploration complete

## What Exists

### Card Display
- **CardTable.tsx** (401 lines): The sole card display component. Pure table layout with columns: Qty, Added, Name, Type, Rarity, Price, Set. Server-side sorting (7 columns), server-side pagination (50 cards/page), keyboard navigation (arrow keys + Enter), inline quantity editing.
- **CardDetailModal.tsx** (453 lines): Opens on row click. Left panel shows card image (280x390 max), right panel shows structured text (mana, type, description, P/T, set, rarity, price). Supports edit mode, delete, single-card price update, and image lightbox zoom.
- **Dashboard.tsx** (330 lines): Orchestrates CollectionInsights -> Filters -> CardTable. Owns filter/sort/pagination state. URL-driven filters via searchParams.

### Image Infrastructure
- **Backend API**: `GET /api/cards/{id}/image` returns raw image bytes. Per-card endpoint (no batch).
- **card_image_service.py**: Resolves images via filesystem ImageStore keyed by scryfall_id. Catalog-first lookup, Scryfall fallback only if user has Scryfall enabled. Returns `(bytes, content_type)`.
- **ImageStore**: Filesystem-based (replaced BYTEA). Files at `{base_dir}/{scryfall_id}.jpg`. Atomic writes, path traversal protection.
- **useCardImage.ts hook**: Fetches single card image via `api.fetchCardImage(cardId)`, returns Blob URL. Auto-revokes on unmount/cardId change. No caching between components -- each mount triggers a new fetch.
- **api.fetchCardImage()**: Uses `apiFetch()` (cookie auth), converts response to Blob URL via `URL.createObjectURL()`.

### Key Observations
- Images are only loaded one-at-a-time (detail modal, deck builder, insight list items)
- No batch image endpoint exists
- No client-side image cache exists (each `useCardImage` mount re-fetches)
- Page size is 50 cards -- gallery view showing 50 images simultaneously would be 50 individual API calls
- Card interface has no `image_url` field for collection cards (only InsightListItem has one)
- The global image cache on the backend is per-scryfall_id, so different users' copies of the same card share one cached image file

## What's Missing

1. **No gallery/grid view** -- zero references to "gallery", "grid view", or "CardGrid" in codebase or specs
2. **No view toggle** -- no table/grid mode switch anywhere
3. **No batch image loading** -- each card image requires a separate API call
4. **No client-side image cache** -- `useCardImage` hook creates/revokes Blob URLs per mount; no shared cache means switching views would re-fetch everything
5. **No image URL in card list response** -- API returns card data without image URLs; images must be fetched by separate endpoint per card
6. **No thumbnail/small image sizes** -- backend serves "normal" Scryfall size (~488x680); no smaller sizes for grid thumbnails
7. **No lazy loading / virtualization** -- CardTable renders all 50 rows in DOM (fine for table, heavy for 50 images)
8. **No skeleton/placeholder for image grids** -- only CardDetailModal has image skeleton

## Improvement Ideas

| # | Idea | Description | Value (1-5) | Complexity (1-5) | Ratio |
|---|------|-------------|-------------|-------------------|-------|
| 1 | **Table/Gallery view toggle** | Add toggle buttons (list/grid icons) in CardTable toolbar. Table mode stays as-is. Gallery mode renders responsive card image grid. User preference persisted in localStorage. | 5 | 3 | 1.67 |
| 2 | **CardGallery component** | New component rendering cards as image tiles in responsive Tailwind grid (2 cols mobile, 3-4 tablet, 5-6 desktop). Each tile: card image, name, price overlay, rarity badge. Click opens CardDetailModal (same behavior as table row click). | 5 | 3 | 1.67 |
| 3 | **Client-side image blob cache** | Shared in-memory cache (Map or module-level singleton) for Blob URLs keyed by card ID. Prevents re-fetching when switching between table/gallery or paginating back. LRU eviction at ~200 entries. | 4 | 2 | 2.00 |
| 4 | **Intersection Observer lazy loading** | Only fetch images for gallery tiles that enter the viewport. Critical for performance with 50-card pages. Use `IntersectionObserver` with rootMargin for pre-fetching nearby tiles. | 4 | 2 | 2.00 |
| 5 | **Image URL in card list response** | Add `image_url` field to card list API response (constructed as `/api/cards/{id}/image`). Frontend can use `<img src>` directly with cookie auth instead of Blob URL dance. Eliminates need for `useCardImage` hook per tile. | 4 | 2 | 2.00 |
| 6 | **Reduced page size for gallery mode** | When gallery view active, reduce page size from 50 to 20-24 (fits nicely in grid layouts). Reduces simultaneous image loads. Configurable via URL param or toggle. | 3 | 1 | 3.00 |
| 7 | **Gallery tile skeleton loading** | Shimmer placeholder (card-shaped rectangles) while images load. MTG card aspect ratio (63:88) maintained. Staggered fade-in as images arrive. | 3 | 1 | 3.00 |
| 8 | **Hover card preview in table mode** | Hover over a card name in table view to see a floating card image tooltip. Similar to Moxfield's hover behavior. Uses `useCardImage` with short delay. | 4 | 2 | 2.00 |
| 9 | **Batch image endpoint** | `GET /api/cards/images?ids=1,2,3` returning multipart response or JSON with base64-encoded thumbnails. Reduces HTTP overhead from 50 requests to 1. | 3 | 4 | 0.75 |
| 10 | **Thumbnail size images** | Backend serves small/thumbnail size (146x204) alongside normal size. Uses Scryfall `small` image URI. Reduces bandwidth for grid view by ~75%. | 3 | 3 | 1.00 |
| 11 | **Virtual scroll for gallery** | Use react-window or similar for virtualized grid rendering. Only renders visible tiles in DOM. Important for collections >200 cards if page size increases. | 2 | 3 | 0.67 |
| 12 | **Gallery sorting by visual attributes** | In gallery mode, sort by color identity (WUBRG grouping) or CMC (creates visual mana curve). Leverages existing server-side sort but with gallery-optimized defaults. | 3 | 1 | 3.00 |
| 13 | **Multi-select in gallery view** | Shift-click or lasso selection for bulk operations (add to deck, export, delete). More natural in visual grid than in table. | 3 | 4 | 0.75 |
| 14 | **Gallery card size slider** | Slider to adjust tile size from small (5-6 per row) to large (2-3 per row). Persistent preference. Similar to Moxfield's card size control. | 2 | 2 | 1.00 |
| 15 | **Card flip animation for DFCs** | Double-faced cards show front by default; hover or click flips to back face. Requires knowing card layout from Scryfall data (already in card_faces). | 2 | 3 | 0.67 |

## Recommended Priority

### Phase 1: MVP Gallery View (Medium effort, ~3-4 days)
These items form the minimum viable gallery experience:

1. **#3 Client-side image blob cache** (do first -- foundational for performance)
2. **#1 Table/Gallery view toggle** (the switch itself)
3. **#2 CardGallery component** (the grid layout)
4. **#4 Intersection Observer lazy loading** (critical for 50-image pages)
5. **#7 Gallery tile skeleton loading** (polished loading experience)
6. **#6 Reduced page size for gallery mode** (quick win for perf)

### Phase 2: Polish (~1-2 days)
7. **#8 Hover card preview in table mode** (high value, adds visual browsing to existing table)
8. **#12 Gallery sorting by visual attributes** (trivial to add, leverages existing sort)
9. **#14 Card size slider** (nice-to-have UX)

### Phase 3: Performance optimization (if needed)
10. **#5 Image URL in card list response** (architectural simplification)
11. **#10 Thumbnail size images** (bandwidth reduction)
12. **#11 Virtual scroll** (only if large collections cause issues)

### Deferred / Low Priority
- **#9 Batch image endpoint**: High complexity, moderate gain. LazyLoad + client cache solve most of the N+1 problem.
- **#13 Multi-select**: Valuable but complex; better suited for a dedicated "collection management" feature.
- **#15 Card flip animation**: Cool but niche; few DFCs in most collections.

## Competitive Analysis

| Platform | Gallery View | Key Features |
|----------|-------------|--------------|
| **Moxfield** | Yes (default) | Card size slider, sort by name/CMC/color/price, hover for details, drag-to-deck |
| **Archidekt** | Yes (default) | Category-grouped grid, card size toggle, hover zoom |
| **EDHREC** | Grid only | Card images with recommendation scores |
| **Deckbox** | Both views | Toggle between list and visual, basic grid |
| **TCGPlayer** | Grid default | Product tiles with price overlays, responsive |
| **MTGGoldfish** | Grid in decklists | Small card images in deck view, table for collection |

**Key differentiator opportunity**: DeckDex can offer gallery view that integrates tightly with the existing filter system (color identity, rarity, price range, set) -- most competitors separate their filters from the visual view. The existing server-side filtering + pagination infrastructure means gallery view gets all the same filter capabilities for free.

## Technical Considerations

- **Image auth**: Images are served via authenticated endpoint (`/api/cards/{id}/image`). Using `<img src>` directly works because `apiFetch` uses cookie auth (credentials: 'include'). However, plain `<img>` tags won't send cookies by default -- the Blob URL approach from `useCardImage` sidesteps this. Gallery view should continue using Blob URLs or ensure cookies are sent.
- **Scryfall rate limits**: Images fetched from Scryfall are cached on first request. A user's first gallery page load could trigger up to 50 Scryfall image downloads if none are cached. The filesystem ImageStore mitigates this for subsequent loads.
- **Memory pressure**: 50 Blob URLs in memory is fine (Blob URLs are just references). The actual image data is held by the browser's blob storage, which handles memory management.
- **Accessibility**: Gallery view needs `role="list"` / `role="listitem"`, meaningful alt text per image (card name), keyboard navigation (arrow keys between tiles), and focus management consistent with table view.
- **i18n**: View toggle labels and any gallery-specific text should use translation keys.

## Architecture Decision: Where does the toggle live?

**Option A**: Toggle in CardTable toolbar, CardTable renders either table or grid internally.
- Pro: Self-contained, toolbar already has action buttons.
- Con: CardTable becomes a misnomer; component grows large.

**Option B**: Toggle in Dashboard, Dashboard renders either CardTable or CardGallery.
- Pro: Clean separation, each component focused.
- Con: Both components need same props (pagination, sorting, click handlers).

**Recommendation**: Option B with a shared props interface. Create `CardCollectionViewProps` type. Dashboard owns the toggle state and renders the appropriate component. Both components import from same props type. This keeps components focused and testable.
