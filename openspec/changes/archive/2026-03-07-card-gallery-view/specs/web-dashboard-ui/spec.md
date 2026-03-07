# Web Dashboard UI — Delta Spec (card-gallery-view change)

This file contains additions and modifications to the `web-dashboard-ui` spec introduced by the `card-gallery-view` change. All existing requirements in `openspec/specs/web-dashboard-ui/spec.md` remain in effect unchanged.

---

### Requirement: Dashboard view toggle (table vs. gallery)
The Dashboard SHALL render a view toggle control in the toolbar area (between the Filters component and the CardTable/CardGallery). The toggle SHALL contain two icon buttons: a table-rows icon for table view and a 2x2-grid icon for gallery view.

#### Scenario: Toggle is visible on Dashboard
- **WHEN** an authenticated user views the Dashboard
- **THEN** a view toggle button group SHALL be visible with table and gallery icons
- **THEN** the active view button SHALL have `aria-pressed="true"`
- **THEN** the inactive view button SHALL have `aria-pressed="false"`

#### Scenario: Toggle group has accessible label
- **WHEN** the view toggle renders
- **THEN** the wrapping `div` SHALL have `role="group"` and `aria-label` set to the localized "Switch collection view" string

---

### Requirement: CardTable and CardGallery share CardCollectionViewProps
The `CardTable` component's props interface SHALL be extracted into an exported `CardCollectionViewProps` interface (in `frontend/src/types/collection.ts`). `CardTable` and `CardGallery` SHALL both accept this interface. The Dashboard SHALL pass identical props to whichever view is active.

#### Scenario: Dashboard passes same props regardless of active view
- **WHEN** the user switches from table to gallery view
- **THEN** the same `cards`, `isLoading`, `serverTotal`, `page`, `totalPages`, `onPageChange`, `onSortChange`, `sortBy`, `sortDir` props SHALL be passed to the active component

---

### Requirement: Dashboard page size adjusts per view mode
The `PAGE_SIZE` constant in Dashboard SHALL be `50` when table view is active and `24` when gallery view is active. Switching views SHALL reset `page` to `1`.

#### Scenario: Switching to gallery reduces page size
- **WHEN** the user switches from table view (50 cards/page) to gallery view
- **THEN** the Dashboard SHALL re-fetch with `limit=24` and `page=1`

#### Scenario: Switching back to table restores page size
- **WHEN** the user switches from gallery view back to table view
- **THEN** the Dashboard SHALL re-fetch with `limit=50` and `page=1`
