# Web Dashboard UI

React (Vite, port 5173). **Overview:** Dashboard layout (top to bottom): Collection Insights widget, Filters, CardTable. No static stats cards. **Table:** sortable (name, type, rarity, price, Added); default sort newest first (created_at desc); 50 cards/page; rows clickable → card detail modal; Edit/Delete do not open detail. **Mana symbols:** Scryfall-style SVGs in card text (`.card-symbol`); no raw {W}/{U}. Color filter buttons use mana symbol SVGs (not plain letters). **Filters:** search, rarity, type, set, price range; active filters as removable chips; result count; Clear Filters. GET /api/cards with same params. **Jobs:** Restore on app mount (GET /api/jobs). Progress modal: WebSocket + GET /api/jobs/{id} for initial state; Minimize + Stop; elapsed timer. Bottom bar: fixed when jobs exist; single app-wide bar (global-jobs-ui); content area reserves space so bar doesn’t overlap. **Styling:** Tailwind v4; theme (light/dark). **Data:** TanStack Query. **Errors:** Toast on API failure; ErrorBoundary. **Nav:** Settings, Analytics (beta) → /analytics.

### Requirements (compact)

- **Dashboard layout:** Collection Insights → Filters → CardTable. No title block (navbar provides branding). No static stats cards.
- **Collection Insights:** Interactive widget with search/autocomplete (keyword matching against catalog), 5-6 contextual suggestion chips, animated response area. Fetches catalog from GET /api/insights/catalog, suggestions from GET /api/insights/suggestions, executes via POST /api/insights/{id}.
- **Filters:** GET /api/cards with search, rarity, type, set_name, price_min, price_max; chips + result count + Clear Filters; no client-side filter of unfiltered response. Color buttons use `card-symbol card-symbol-{W|U|B|R|G}` SVGs.
- **Table:** Sort by name/type/rarity/price/Added (numeric for price, lexicographic others; empty price last). Default: Added desc (newest first). Added column sortable, shows date when created_at present.
- **Jobs bar:** One bar at app level when jobs exist; Dashboard does not render its own. Main content (Dashboard + Settings) reserves bottom space so bar doesn’t overlap.
- **Update Prices:** Slate/gray outline button (tertiary) in CardTable toolbar after Import list; triggers price update job → global jobs bar.
- **Job modal:** Open from bar; progress + log; close dismisses; live updates.
- **Card row click:** Opens detail modal (not Edit/Delete). Table wired to modal + image API by card id.
- **Add card:** Single name field + autocomplete (collection + Scryfall); no type/rarity/price/set inputs; Edit modal keeps all fields.
- **Import list button:** Indigo outline button next to "Add card" in CardTable toolbar; opens Import List modal (file/text tabs → resolve → navigate to /import review step). Secondary importance styling (outline/ghost).
- **Nav:** Analytics (beta) link next to Settings → /analytics; route /analytics renders Analytics page (analytics-dashboard spec); responsive + theme.

### Requirement: Collection Insights widget replaces Top 5 Most Valuable
The Dashboard SHALL display a Collection Insights widget. The TopValueCards component has been removed.

#### Scenario: Insights widget visible on dashboard
- **WHEN** an authenticated user views the Dashboard
- **THEN** the Collection Insights widget SHALL be displayed before Filters
- **THEN** no "Top 5 Most Valuable" section SHALL be displayed

### Requirement: Insights search autocomplete
The Collection Insights widget SHALL include a text input that filters the insight catalog by keyword matching as the user types.

#### Scenario: User types and sees matching questions
- **WHEN** the user types "value" in the insights search input
- **THEN** a dropdown SHALL appear showing insights whose keywords match

#### Scenario: User selects a question from autocomplete
- **WHEN** the user clicks a question in the autocomplete dropdown
- **THEN** the system SHALL execute that insight and display the response in the response area below
- **THEN** the dropdown SHALL close

### Requirement: Contextual suggestion chips
The Collection Insights widget SHALL display 5-6 suggestion chips below the search input. Chips represent the most relevant questions for the user's current collection state.

#### Scenario: Chip hover effect
- **WHEN** the user hovers over a suggestion chip
- **THEN** the chip SHALL display an elevation effect (shadow-lg), slight scale increase (1.03), and border color change
- **THEN** the transition SHALL be smooth (200ms ease)

#### Scenario: Chip click executes insight
- **WHEN** the user clicks a suggestion chip
- **THEN** the system SHALL execute the corresponding insight and display the response

### Requirement: Rich response visualizations
The response area SHALL render different visualizations based on the `response_type` of the insight response.

#### Scenario: Value response renders big number with breakdown
- **WHEN** an insight returns `response_type: "value"`
- **THEN** the primary value SHALL be displayed in a large, bold font with count-up animation
- **THEN** if breakdown data is present, it SHALL fade in with staggered delay (50ms per item)

#### Scenario: Distribution response renders horizontal bars
- **WHEN** an insight returns `response_type: "distribution"`
- **THEN** each item SHALL be rendered as a labeled horizontal bar (grow animation 400ms ease-out, 80ms stagger)
- **THEN** for color-related distributions, bars SHALL use MTG color theming and display Scryfall mana symbols via `card-symbol` CSS classes

#### Scenario: List response renders ranked items
- **WHEN** an insight returns `response_type: "list"`
- **THEN** items SHALL slide in from the left with staggered delay (60ms per item)
- **THEN** if `card_id` is present, the item SHALL be clickable and open the CardDetailModal

#### Scenario: Comparison response renders presence indicators
- **WHEN** an insight returns `response_type: "comparison"`
- **THEN** each item SHALL display a check (green) or cross (red) indicator with scale-in bounce animation

#### Scenario: Timeline response renders period bars
- **WHEN** an insight returns `response_type: "timeline"`
- **THEN** items SHALL be rendered as horizontal bars grouped by period label with staggered grow animation

### Requirement: Mana symbol icons in color filter buttons
The Filters component color toggle buttons SHALL display Scryfall mana symbol SVGs instead of plain letter text.

#### Scenario: Color button shows mana symbol
- **WHEN** the Filters component renders the color toggle bar
- **THEN** each color button (W, U, B, R, G) SHALL display the corresponding Scryfall mana symbol using the `card-symbol card-symbol-{symbol}` CSS classes
- **THEN** the button SHALL retain its circular shape, hover effects, and active/inactive states

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

### Requirement: Import wizard includes Review step
The import wizard SHALL include 6 steps: upload → resolve → review → mode → progress → result. The resolve step replaces the previous preview step and includes format detection, card count, and per-card resolution status.

#### Scenario: Step indicator shows 6 steps
- **WHEN** the user opens the import page
- **THEN** the step indicator SHALL display 6 numbered steps

#### Scenario: Upload triggers resolve instead of preview
- **WHEN** the user uploads a file or submits pasted text
- **THEN** the wizard SHALL call the resolve endpoint and advance to the review step upon completion

### Requirement: Import list button in CardTable toolbar
The CardTable toolbar SHALL display an "Import list" button next to the "Add card" button when an import callback is provided. The button SHALL open an Import List modal. The button SHALL use an outline/ghost style (indigo border, transparent background) to communicate secondary importance relative to the primary "Add card" button.

#### Scenario: Import list button visible on dashboard
- **WHEN** the user views the Dashboard with the CardTable
- **THEN** an "Import list" button SHALL be displayed next to the "Add card" button
- **THEN** the button SHALL have an indigo outline style (not solid fill)

#### Scenario: Clicking Import list opens modal
- **WHEN** the user clicks the "Import list" button
- **THEN** an Import List modal SHALL open with file/text input tabs

#### Scenario: Button label is localized
- **WHEN** the application language is English
- **THEN** the button SHALL display "Import list"
- **WHEN** the application language is Spanish
- **THEN** the button SHALL display "Importar lista"

### Requirement: Import List modal with file and text input
The Import List modal SHALL provide two input modes via a tab toggle: file upload (drag-and-drop zone + file picker) and text paste (textarea). The modal SHALL follow the CardFormModal overlay pattern (fixed overlay, click-outside-to-close).

#### Scenario: Modal displays file/text tabs
- **WHEN** the Import List modal opens
- **THEN** it SHALL display a tab toggle with "File" and "Text" options
- **THEN** the "Text" tab SHALL be selected by default

#### Scenario: File tab shows drag-and-drop zone
- **WHEN** the user selects the "File" tab
- **THEN** a drag-and-drop zone SHALL be displayed accepting `.csv` and `.txt` files
- **THEN** a "Select file" button SHALL be available as alternative

#### Scenario: Text tab shows textarea
- **WHEN** the user selects the "Text" tab
- **THEN** a textarea SHALL be displayed for pasting card lists
- **THEN** a "Continue" button SHALL be enabled only when the textarea is non-empty

#### Scenario: Submit resolves cards and navigates to review
- **WHEN** the user submits a file or text via the modal
- **THEN** the modal SHALL call `api.importResolve()` and show a loading state
- **THEN** on success, the modal SHALL close and navigate to `/import` with the resolved data in route state
- **THEN** on error, the modal SHALL display the error message and remain open

#### Scenario: Click outside closes modal
- **WHEN** the user clicks outside the modal content area
- **THEN** the modal SHALL close without submitting

### Requirement: Import page accepts pre-resolved data from route state
The Import page SHALL check for `resolveData` in React Router location state on mount. If present, it SHALL skip the upload and resolve steps and display the review step immediately.

#### Scenario: Import page receives pre-resolved data
- **WHEN** the Import page loads with `resolveData` in route state
- **THEN** the page SHALL skip to the review step with the provided data
- **THEN** the route state SHALL be cleared to prevent stale data on refresh

#### Scenario: Import page loads without route state
- **WHEN** the Import page loads without route state
- **THEN** the page SHALL display the upload step as normal

### Requirement: Update Prices button in CardTable toolbar
The CardTable toolbar SHALL display an "Update Prices" button next to the "Import list" button when an update prices callback is provided. The button SHALL use a tertiary style (slate/gray outline, transparent background) and trigger a price update job that registers in the global jobs bar.

#### Scenario: Update Prices button visible on dashboard
- **WHEN** the user views the Dashboard with the CardTable
- **THEN** an "Update Prices" button SHALL be displayed after the "Import list" button
- **THEN** the button SHALL have a slate/gray outline style (tertiary importance)

#### Scenario: Clicking Update Prices triggers job
- **WHEN** the user clicks the "Update Prices" button
- **THEN** the system SHALL trigger a price update job via the backend
- **THEN** the button SHALL show "Starting..." while the job is being created
- **THEN** the job SHALL appear in the global jobs bar

#### Scenario: Button label is localized
- **WHEN** the application language is English
- **THEN** the button SHALL display "Update Prices"
- **WHEN** the application language is Spanish
- **THEN** the button SHALL display "Actualizar precios"

### Requirement: Animated background on app pages
All authenticated app pages SHALL render the AetherParticles animated background as a fixed, full-viewport decorative layer behind the page content.

#### Scenario: Background present on dashboard
- **WHEN** an authenticated user views the Dashboard
- **THEN** floating WUBRG-colored particles SHALL be visible drifting behind the dashboard content

#### Scenario: Background does not obstruct content
- **WHEN** the AetherParticles background is rendered
- **THEN** all page content (navbar, filters, tables, modals) SHALL render above the background layer

### Requirement: Error messages have role="alert"
All error message containers in the frontend SHALL have `role="alert"` so screen readers automatically announce them when they appear. This applies to all inline error divs in:
- CardFormModal
- SettingsModal
- ProfileModal
- DeckImportModal
- ImportListModal
- DeckBuilder createError
- Dashboard error state

#### Scenario: Form error is announced
- **WHEN** a form submission fails and an error message div appears
- **THEN** the error container SHALL have `role="alert"` so assistive technology announces it

### Requirement: Icon-only buttons have aria-label
All buttons that display only an icon (no visible text) SHALL have an `aria-label` attribute describing their action. Affected buttons include:
- Close (X) buttons in all modals (CardFormModal, CardDetailModal, SettingsModal, ProfileModal, DeckDetailModal, DeckCardPickerModal, DeckImportModal, ImportListModal, JobLogModal)
- Avatar/photo upload button in ProfileModal
- Footer social link icons (landing page)

#### Scenario: Close button is accessible
- **WHEN** a modal close button contains only an icon
- **THEN** the button SHALL have an `aria-label` (e.g., "Close") describing its action

### Requirement: Form label/input associations
All `<label>` elements in forms SHALL be associated with their corresponding `<input>`, `<select>`, or `<textarea>` elements via `htmlFor`/`id` pairs. This applies to all form fields in:
- CardFormModal (name, type, rarity, price, set fields)
- CardDetailModal edit form
- ProfileModal (display name)
- SettingsModal fields
- Filters (search, price min/max, rarity, type, set)

#### Scenario: Clicking label focuses input
- **WHEN** a user clicks a label text in a form
- **THEN** focus SHALL move to the associated input element

### Requirement: CardTable sortable headers are keyboard-accessible
Sortable column headers in CardTable SHALL be operable via keyboard and SHALL communicate sort state to assistive technology.

Each sortable `<th>` element SHALL:
- Have `tabIndex={0}` to be reachable via Tab
- Have `onKeyDown` handler that triggers sort on Enter or Space
- Have `aria-sort="ascending"`, `aria-sort="descending"`, or `aria-sort="none"` reflecting current sort state

#### Scenario: Keyboard user sorts table
- **WHEN** a sortable column header is focused and the user presses Enter or Space
- **THEN** the table SHALL sort by that column (same behaviour as clicking)

#### Scenario: Sort direction is communicated
- **WHEN** a column is sorted ascending
- **THEN** the column header SHALL have `aria-sort="ascending"`
- **WHEN** a column is sorted descending
- **THEN** the column header SHALL have `aria-sort="descending"`
- **WHEN** a column is not the current sort column
- **THEN** the column header SHALL have `aria-sort="none"`

### Requirement: QuantityCell is keyboard-accessible
The QuantityCell component in CardTable SHALL allow keyboard users to enter quantity edit mode. The quantity display element SHALL have `tabIndex={0}`, `role="button"`, and an `onKeyDown` handler that activates edit mode on Enter or Space.

#### Scenario: Keyboard user edits quantity
- **WHEN** the quantity display element is focused and the user presses Enter or Space
- **THEN** the component SHALL enter edit mode (same behaviour as clicking)

