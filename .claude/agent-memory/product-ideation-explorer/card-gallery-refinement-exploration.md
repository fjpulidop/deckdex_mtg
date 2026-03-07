# Card Gallery View Refinement Exploration

**Date:** 2026-03-07
**Status:** Exploration complete
**Previous exploration:** card-gallery-view-exploration.md (pre-implementation)

## What Was Built (Phase 1 MVP -- Delivered)

Since the initial exploration, the gallery MVP has been fully implemented:

### CardGallery.tsx (231 lines)
- **Responsive grid**: Tailwind grid with breakpoints (2 cols mobile -> 3 sm -> 4 md -> 5 lg -> 6 xl)
- **IntersectionObserver lazy loading**: Each CardTile uses IO with 200px rootMargin; image fetch deferred until visible
- **Skeleton loading**: 24 card-shaped pulse placeholders during isLoading
- **Hover overlay**: Name + price slide up on hover/focus (translate-y animation, gradient overlay)
- **Card aspect ratio**: Correct MTG 63:88 maintained via `aspect-[63/88]`
- **Empty state**: "No cards found" message when cards array empty
- **Toolbar**: Mirrors CardTable's Add/Import/Update Prices buttons
- **Pagination**: Full prev/next/showing-X-of-Y footer, shared i18n keys with CardTable

### useImageCache.ts (84 lines)
- **Module-level singleton cache**: Map<number, string> keyed by card ID
- **Deduplication**: inflightRequests Map prevents concurrent fetches for same card
- **useSyncExternalStore**: Proper external store pattern with stable snapshot objects
- **No Blob URL revocation**: Intentional -- keeps cache valid across component unmounts
- **Error tracking**: errorCards Set tracks failed fetches

### Dashboard.tsx Integration
- **View toggle**: Table/Gallery icon buttons with aria-pressed, persisted to localStorage
- **Adaptive page size**: 24 for gallery, 50 for table
- **Page reset on toggle**: Switching views resets to page 1
- **Shared CardCollectionViewProps**: Both views use same interface (types/collection.ts)

### Tests
- **CardGallery.test.tsx** (105 lines): 6 tests covering skeleton, tile rendering, click handlers, empty state, toolbar
- **Dashboard.test.tsx**: 4 gallery-specific tests (toggle, localStorage persistence, page size)

## Gaps Found

### 1. CRITICAL: No keyboard navigation in gallery grid
- CardTable has full arrow key navigation (up/down/left/right between rows, Enter to select)
- CardGallery tiles are `<button>` elements (Tab-navigable) but NO arrow key support
- With a 6-column grid, Tab order is left-to-right/top-to-bottom but there's no way to navigate the 2D grid with arrows
- This is a significant a11y regression from table view
- **Fix**: Add roving tabindex pattern with arrow key handlers matching grid dimensions

### 2. CRITICAL: No `role="grid"` or `role="list"` on the container
- The grid `<div>` has no semantic role -- screen readers see it as a generic container
- Tiles have aria-label but the collection of tiles has no semantic structure
- **Fix**: Add `role="list"` on grid container, `role="listitem"` wrapper on each tile (or `role="grid"` with `role="row"` + `role="gridcell"` for 2D nav)

### 3. MAJOR: Gallery ignores sort controls
- CardGallery receives `sortBy`, `sortDir`, `onSortChange` props but NEVER uses them
- No sort indicators or sort affordance in gallery view
- Users cannot change sort order while in gallery mode (must switch to table, sort, switch back)
- **Fix**: Add a compact sort dropdown/pills above the grid (e.g., "Sort by: Name | Price | Added | Rarity")

### 4. MAJOR: Gallery ignores onQuantityChange
- CardTable has inline QuantityCell editing (click qty -> input -> save)
- CardGallery receives onQuantityChange in props interface but never renders quantity or uses it
- Gallery tiles show no quantity badge at all -- users with 4x Lightning Bolt see no indication
- **Fix**: Add quantity badge (top-left corner overlay), click-to-edit or long-press-to-edit

### 5. MODERATE: No card rarity/type visual indicators
- Hover overlay shows only name + price
- No rarity indicator (color coding or icon) visible at a glance
- No type line visible
- Moxfield shows rarity gem + set icon on hover; Archidekt shows rarity border coloring
- **Fix**: Add rarity-colored border-bottom or corner gem; add type line to hover overlay

### 6. MODERATE: No card size control
- Fixed responsive grid (2-6 columns based on breakpoint)
- No user control over tile size (Moxfield has small/medium/large toggle)
- Users with large monitors get tiny tiles at 6-col; users who want overview can't go smaller
- **Fix**: Add size slider or S/M/L toggle that adjusts grid-cols classes; persist to localStorage

### 7. MODERATE: Toolbar duplication
- CardGallery duplicates the entire CardTable toolbar (Add/Import/Update Prices)
- Same button classes, same logic, same i18n keys -- ~30 lines of identical JSX
- If toolbar changes (new button, style update), both components must be updated
- **Fix**: Extract shared `CollectionToolbar` component

### 8. MODERATE: Pagination footer duplication
- CardGallery duplicates the entire CardTable pagination footer (~30 lines)
- Same showing/prev/next pattern, same i18n keys
- **Fix**: Extract shared `PaginationFooter` component

### 9. MINOR: No hover card preview in table mode
- DeckDetailModal has hover preview (hover card name -> show image in sidebar)
- CardTable has NO hover preview -- clicking opens detail modal instead
- Hover preview is a major UX win for visual card identification in table mode
- Moxfield does this extremely well
- **Fix**: Add hover tooltip with card image using useImageCache (debounced ~200ms)

### 10. MINOR: No transition animation between views
- Switching table <-> gallery is instant (no crossfade or layout animation)
- Cards just appear/disappear -- feels abrupt
- **Fix**: CSS transition or React.lazy with Suspense fallback

### 11. MINOR: Image error state not handled in tiles
- useImageCache tracks errors (errorCards Set) but CardTile only renders skeleton or image
- If image fetch fails, tile shows infinite skeleton pulse
- **Fix**: Show card name text + mana cost fallback when error=true, or a broken-image icon

### 12. MINOR: Blob URL memory leak potential
- useImageCache comment says "Blob URLs are never revoked -- intentional"
- For collections of 1000+ cards where user paginates through many pages, Blob URLs accumulate
- Each Blob URL holds a reference to image data (~50-100KB each)
- 500 cached images = ~25-50MB of blob storage
- **Fix**: Add LRU eviction (keep last ~200 entries, revoke oldest). Not urgent for typical use.

## Improvement Ideas

| # | Idea | Value | Complexity | Impact/Effort |
|---|------|-------|------------|----------------|
| 1 | **Sort controls for gallery** -- dropdown or pill bar above grid | 5 | S | **High** |
| 2 | **Quantity badge on tiles** -- corner badge showing qty, click to edit | 4 | S | **High** |
| 3 | **Grid keyboard navigation** -- roving tabindex, arrow keys for 2D grid | 4 | M | **Medium** |
| 4 | **Semantic roles** -- role="list"/role="listitem" on grid/tiles | 4 | XS | **Very High** |
| 5 | **Extract CollectionToolbar** -- shared toolbar component | 3 | S | **High** |
| 6 | **Extract PaginationFooter** -- shared pagination component | 3 | S | **High** |
| 7 | **Rarity visual indicators** -- colored border or gem on tiles | 3 | S | **Medium** |
| 8 | **Image error fallback** -- show card name when image fails | 3 | XS | **Very High** |
| 9 | **Card size toggle** -- S/M/L or slider for tile size | 3 | S | **Medium** |
| 10 | **Hover card preview in table** -- tooltip with card image on name hover | 4 | M | **Medium** |
| 11 | **View transition animation** -- crossfade between table/gallery | 2 | S | **Medium** |
| 12 | **LRU eviction for image cache** -- cap at ~200 entries | 2 | S | **Medium** |

Complexity: XS (<30min), S (1-2hr), M (3-4hr), L (1day+)

## Recommended Priority

### Tier 1: Quick wins with outsized impact (~2-3 hours total)
1. **#4 Semantic roles** (XS) -- Add role="list"/role="listitem". 5-minute fix, significant a11y improvement.
2. **#8 Image error fallback** (XS) -- Already have error state in useImageCache; just render fallback JSX.
3. **#1 Sort controls for gallery** (S) -- Gallery is nearly unusable for finding cards without sort. Add compact pill bar: Name | Price | Added | Rarity with current sort highlighted. Uses existing onSortChange prop.
4. **#2 Quantity badge** (S) -- Visual badge in top-left corner of tile. Essential for users with multiple copies.

### Tier 2: Code quality + DRY (~2 hours total)
5. **#5 Extract CollectionToolbar** (S)
6. **#6 Extract PaginationFooter** (S)

### Tier 3: Polish (~3-4 hours total)
7. **#3 Grid keyboard navigation** (M) -- Roving tabindex with arrow keys. Important for a11y compliance but complex.
8. **#7 Rarity indicators** (S) -- Rarity-colored left border or bottom accent.
9. **#9 Card size toggle** (S) -- S/M/L toggle persisted to localStorage.

### Tier 4: Nice-to-have
10. **#10 Hover preview in table** (M) -- High value but different feature area (table, not gallery).
11. **#11 View transition** (S) -- Polish only.
12. **#12 LRU eviction** (S) -- Only matters for very large collections.

## Competitive Comparison (Post-Implementation)

| Feature | DeckDex | Moxfield | Archidekt | Deckbox |
|---------|---------|----------|-----------|---------|
| Gallery view exists | Yes | Yes | Yes | Yes |
| Lazy loading | Yes (IO) | Yes | Yes | No |
| Image cache | Yes (module) | Browser cache | Browser cache | Browser cache |
| Sort in gallery | **NO** | Yes (dropdown) | Yes (dropdown) | Yes |
| Quantity display | **NO** | Yes (badge) | Yes (badge) | Yes |
| Card size control | **NO** | Yes (slider) | Yes (toggle) | No |
| Keyboard grid nav | **NO** | Partial | No | No |
| Rarity indicators | **NO** | Yes (gem) | Yes (border) | No |
| Hover overlay | Yes (name+price) | Yes (name+price+set) | Yes | No |
| Skeleton loading | Yes | Yes | No | No |

DeckDex has solid fundamentals (lazy loading, image cache, skeleton, a11y labels) but is missing the interaction layer that makes gallery view usable for real collection management.

## Key Architectural Notes

- CardCollectionViewProps interface already includes sortBy/sortDir/onSortChange/onQuantityChange -- the gallery just ignores them. Adding these features requires zero API or type changes.
- useImageCache is well-architected (useSyncExternalStore, dedup, stable snapshots). It can support more concurrent usage without changes.
- The toolbar/pagination duplication is a textbook case for extraction. Both components use identical i18n keys.
- Dashboard already passes all needed props to CardGallery. The gallery just needs to use them.
