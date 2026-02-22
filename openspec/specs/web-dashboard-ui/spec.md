# Web Dashboard UI

React (Vite, port 5173). **Overview:** 2-column grid: Total Cards, Total Value (subtitle Avg: €X.XX); 30s auto-refresh; skeleton loaders. **Table:** sortable (name, type, rarity, price, Added); default sort newest first (created_at desc); 50 cards/page; rows clickable → card detail modal; Edit/Delete do not open detail. **Mana symbols:** Scryfall-style SVGs in card text (`.card-symbol`); no raw {W}/{U}. **Filters:** search, rarity, type, set, price range; active filters as removable chips; result count; Clear Filters. GET /api/cards and GET /api/stats with same params so list and stats match. **Jobs:** Restore on app mount (GET /api/jobs); Process Cards and Update Prices in Settings → Deck Actions. Progress modal: WebSocket + GET /api/jobs/{id} for initial state; Minimize + Stop; elapsed timer. Bottom bar: fixed when jobs exist; single app-wide bar (global-jobs-ui); content area reserves space so bar doesn’t overlap. **Styling:** Tailwind v4; theme (light/dark). **Data:** TanStack Query. **Errors:** Toast on API failure; ErrorBoundary. **Nav:** Settings, Analytics (beta) → /analytics.

### Requirements (compact)

- **Stats:** 2 cards (Total Cards, Total Value + Avg); request GET /api/stats with current filter params; 30s refetch; skeleton while loading. No job restore on Dashboard mount (global layer does it).
- **Filters:** GET /api/cards with search, rarity, type, set_name, price_min, price_max; chips + result count + Clear Filters; no client-side filter of unfiltered response.
- **Table:** Sort by name/type/rarity/price/Added (numeric for price, lexicographic others; empty price last). Default: Added desc (newest first). Added column sortable, shows date when created_at present.
- **Jobs bar:** One bar at app level when jobs exist; Dashboard does not render its own. Main content (Dashboard + Settings) reserves bottom space so bar doesn’t overlap.
- **Settings:** Deck Actions last section: Process Cards (scope), Update Prices; trigger → job in global bar.
- **Job modal:** Open from bar; progress + log; close dismisses; live updates.
- **Card row click:** Opens detail modal (not Edit/Delete). Table wired to modal + image API by card id.
- **Add card:** Single name field + autocomplete (collection + Scryfall); no type/rarity/price/set inputs; Edit modal keeps all fields.
- **Nav:** Analytics (beta) link next to Settings → /analytics; route /analytics renders Analytics page (analytics-dashboard spec); responsive + theme.
## Requirements
### Requirement: Login page replaces anonymous access
The frontend SHALL display a login page for unauthenticated users instead of showing the dashboard directly.

#### Scenario: Unauthenticated user sees login page
- **WHEN** an unauthenticated user opens the application
- **THEN** the app SHALL redirect to `/login` and display a "Continue with Google" button

#### Scenario: Authenticated user sees dashboard
- **WHEN** an authenticated user opens the application at `/`
- **THEN** the app SHALL display the dashboard with that user's cards and stats

### Requirement: All pages wrapped in ProtectedRoute
Every page (Dashboard, Settings, Analytics, Decks) SHALL be wrapped in a `ProtectedRoute` component that redirects to `/login` when the user is not authenticated.

#### Scenario: ProtectedRoute redirects unauthenticated user
- **WHEN** an unauthenticated user navigates to `/settings`
- **THEN** the app SHALL redirect to `/login`

#### Scenario: ProtectedRoute allows authenticated user
- **WHEN** an authenticated user navigates to `/settings`
- **THEN** the app SHALL render the Settings page normally

### Requirement: Loading state during auth check
The app SHALL show a loading indicator while checking authentication status on mount (not the login page and not the dashboard).

#### Scenario: Loading spinner during auth check
- **WHEN** the app is checking the authentication status (`isLoading = true`)
- **THEN** the app SHALL display a centered loading spinner or skeleton
- **THEN** the app SHALL NOT flash the login page or the dashboard

