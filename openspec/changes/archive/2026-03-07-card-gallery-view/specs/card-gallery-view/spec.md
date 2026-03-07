# Card Gallery View

Responsive image gallery for browsing the MTG card collection. Complements the existing table view with a visual-first browsing experience, client-side image caching, and IntersectionObserver-based lazy loading.

---

### Requirement: View toggle persists to localStorage
The Dashboard SHALL provide a view toggle that switches between `table` view and `gallery` view. The selected view SHALL be persisted to `localStorage` under the key `'collectionView'` and restored on page load.

#### Scenario: User switches to gallery view
- **WHEN** an authenticated user clicks the gallery icon button in the Dashboard toolbar
- **THEN** the Dashboard SHALL render the CardGallery component in place of CardTable
- **THEN** the active view button SHALL have `aria-pressed="true"` and appear visually selected (indigo fill)
- **THEN** `localStorage.getItem('collectionView')` SHALL return `'gallery'`

#### Scenario: View preference survives page reload
- **WHEN** a user has selected gallery view and reloads the page
- **THEN** the Dashboard SHALL render the gallery view on load without requiring re-selection

#### Scenario: Switching view resets pagination
- **WHEN** the user is on page 3 in table view and switches to gallery view
- **THEN** the page SHALL reset to 1

---

### Requirement: Gallery page size is 24 cards
When gallery view is active, the Dashboard SHALL request 24 cards per page instead of 50. This reduces the number of simultaneous image requests on initial load.

#### Scenario: Gallery mode uses 24-card pages
- **WHEN** the user is in gallery view and the API request is made
- **THEN** the `limit` query parameter SHALL be `24`
- **WHEN** the user is in table view
- **THEN** the `limit` query parameter SHALL be `50`

---

### Requirement: CardGallery displays a responsive image grid
The `CardGallery` component SHALL render cards in a responsive CSS grid. Column count SHALL adapt to viewport width: 2 columns on mobile, 3 at sm, 4 at md, 5 at lg, 6 at xl.

#### Scenario: Gallery renders card tiles
- **WHEN** a page of cards is loaded in gallery view
- **THEN** each card SHALL be rendered as a tile with the standard MTG card aspect ratio (63:88)
- **THEN** clicking any tile SHALL open the CardDetailModal for that card

#### Scenario: Gallery shows loading skeleton
- **WHEN** the card data is loading (`isLoading = true`)
- **THEN** the gallery SHALL display 24 card-shaped skeleton placeholders with `animate-pulse`
- **THEN** no tiles with card data SHALL be visible

---

### Requirement: Gallery tiles lazy-load images via IntersectionObserver
Card images SHALL only be fetched when the tile is within 200px of the viewport. Tiles outside this threshold SHALL render a static placeholder until they approach the viewport.

#### Scenario: Off-screen tile does not fetch image
- **WHEN** a gallery tile is rendered outside the 200px root margin
- **THEN** no request to `GET /api/cards/{id}/image` SHALL be made for that tile

#### Scenario: Tile entering viewport triggers image fetch
- **WHEN** a gallery tile scrolls within 200px of the viewport
- **THEN** the tile SHALL begin fetching its card image
- **THEN** an `animate-pulse` skeleton SHALL display during the fetch
- **THEN** the fetched image SHALL replace the skeleton when loaded

---

### Requirement: Card image blob cache shared across all consumers
The system SHALL maintain a module-level `Map<number, string>` (card id → blob URL) that persists for the browser session. Both gallery tiles and the CardDetailModal SHALL use this cache via the `useImageCache` hook.

#### Scenario: Image fetched once per session
- **WHEN** a user opens a card detail modal for card id 42
- **THEN** the image SHALL be fetched via `GET /api/cards/42/image` and stored in the cache
- **WHEN** the user closes the modal and scrolls to card 42's tile in gallery view
- **THEN** the tile SHALL display the image immediately from cache without a new HTTP request

#### Scenario: In-flight deduplication
- **WHEN** two components simultaneously need the image for the same card id
- **THEN** only one `GET /api/cards/{id}/image` request SHALL be made
- **THEN** both consumers SHALL receive the blob URL when the single request resolves

#### Scenario: Null card id returns no-image state
- **WHEN** `useImageCache(null)` is called
- **THEN** the hook SHALL return `{ src: null, loading: false, error: false }` immediately

---

### Requirement: Tile hover overlay shows card name and price
When a gallery tile is hovered or focused (keyboard), an overlay SHALL slide up from the bottom of the tile displaying the card name and price.

#### Scenario: Hover reveals overlay
- **WHEN** the user hovers over a gallery tile
- **THEN** a gradient overlay SHALL animate upward revealing the card name and price (200ms ease transition)
- **THEN** the overlay SHALL disappear when the mouse leaves the tile

#### Scenario: Focused tile shows overlay for keyboard users
- **WHEN** a gallery tile receives keyboard focus
- **THEN** the overlay SHALL be visible (same as hover state)

---

### Requirement: Gallery toolbar matches CardTable toolbar
The `CardGallery` component SHALL render the same Add card, Import list, and Update Prices buttons as the `CardTable` toolbar when the corresponding callback props are provided.

#### Scenario: Add card button visible in gallery
- **WHEN** the user is in gallery view and `onAdd` prop is provided
- **THEN** a green "Add card" button SHALL be displayed above the grid

---

### Requirement: Gallery pagination follows CardTable pattern
The `CardGallery` component SHALL render pagination controls (Previous / Page X of Y / Next) below the grid using the same visual pattern as `CardTable`.

#### Scenario: Pagination navigates gallery pages
- **WHEN** the user clicks "Next" in gallery pagination
- **THEN** `onPageChange` SHALL be called with `page + 1`
- **THEN** the grid SHALL scroll to the top of the gallery container

---

### Requirement: All gallery strings are localized
Every user-visible string in `CardGallery` (button labels, aria-labels, empty state, loading text) SHALL use `t()` from `useTranslation()`. Strings SHALL be defined in `en.json` and `es.json` under the `gallery` and `viewToggle` namespaces.

#### Scenario: Gallery renders in Spanish
- **WHEN** the user has selected Spanish as their language
- **THEN** all gallery text SHALL be displayed in Spanish
