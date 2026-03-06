## ADDED Requirements

### Requirement: Resolve endpoint parses and resolves card names
The backend SHALL expose `POST /api/import/resolve` that accepts a file upload or pasted text, parses it using existing importers, and resolves each card name against the local catalog and optionally Scryfall. The response SHALL include per-card resolution status and suggestions for unresolved cards.

#### Scenario: All cards resolve against catalog
- **WHEN** a user submits a file where all card names exist in the catalog
- **THEN** the endpoint SHALL return all cards with `status: "matched"` and `resolved_name` set to the catalog match

#### Scenario: Card name has typo with catalog suggestions
- **WHEN** a user submits a file containing a misspelled card name (e.g., "Ligthning Bolt")
- **THEN** the endpoint SHALL return that card with `status: "suggested"` and `suggestions` containing up to 3 fuzzy matches from the catalog

#### Scenario: Scryfall fallback for unresolved cards
- **WHEN** a card name has no catalog matches and Scryfall is enabled for the user
- **THEN** the endpoint SHALL call Scryfall autocomplete and return up to 3 suggestions with `status: "suggested"`

#### Scenario: No matches found anywhere
- **WHEN** a card name has no catalog matches and no Scryfall results (or Scryfall is disabled)
- **THEN** the endpoint SHALL return that card with `status: "not_found"` and empty `suggestions`

#### Scenario: Scryfall lookup cap
- **WHEN** more than 50 cards are unresolved after catalog lookup
- **THEN** the endpoint SHALL only perform Scryfall autocomplete for the first 50 unresolved cards and mark the rest as `not_found`

### Requirement: Resolve response shape
The resolve endpoint SHALL return a JSON object with the following structure: `format` (string), `total` (int), `matched_count` (int), `unresolved_count` (int), and `cards` (array). Each card object SHALL contain: `original_name` (string), `quantity` (int), `set_name` (string or null), `status` ("matched" | "suggested" | "not_found"), `resolved_name` (string or null), `suggestions` (array of strings, max 3).

#### Scenario: Response includes summary counts
- **WHEN** the resolve endpoint processes 500 cards with 488 matched and 12 unresolved
- **THEN** the response SHALL include `total: 500`, `matched_count: 488`, `unresolved_count: 12`

#### Scenario: Matched card includes resolved name
- **WHEN** a card is matched exactly
- **THEN** its entry SHALL have `status: "matched"`, `resolved_name` set to the catalog name, and `suggestions: []`

### Requirement: Resolve endpoint input validation
The resolve endpoint SHALL accept the same input formats as the existing preview endpoint: a file upload (CSV, TXT) or pasted text (Form field). It SHALL reuse existing parser infrastructure (`detect_format`, importer parsers).

#### Scenario: No input provided
- **WHEN** neither file nor text is provided
- **THEN** the endpoint SHALL return HTTP 400

#### Scenario: Empty file
- **WHEN** the uploaded file contains no parseable cards
- **THEN** the endpoint SHALL return HTTP 400 with message "No cards found"

### Requirement: Import from corrected card list
The backend SHALL accept `POST /api/import/external` with a JSON body containing a `cards` array (each with `name`, `quantity`, optional `set_name`) and `mode` field, as an alternative to file/text upload. This allows the frontend to send user-corrected card names directly.

#### Scenario: Import with corrected JSON body
- **WHEN** a user sends a JSON body with `cards: [{name: "Lightning Bolt", quantity: 4}]` and `mode: "merge"`
- **THEN** the backend SHALL parse the cards array into `ParsedCard` list and proceed with the existing import flow

#### Scenario: JSON body with empty cards array
- **WHEN** a user sends a JSON body with `cards: []`
- **THEN** the backend SHALL return HTTP 400 with message "No cards found"

### Requirement: Review step in import wizard
The import wizard UI SHALL include a Review step after resolve completes and before mode selection. This step SHALL display all resolved and unresolved cards, allowing users to correct unresolved ones before proceeding.

#### Scenario: All cards matched — review step shows summary only
- **WHEN** the resolve step returns 0 unresolved cards
- **THEN** the review step SHALL show a summary ("500 cards matched") and allow the user to proceed immediately

#### Scenario: Unresolved cards shown with suggestions
- **WHEN** the resolve step returns cards with `status: "suggested"`
- **THEN** the review step SHALL display each unresolved card with its suggestions as selectable options

#### Scenario: User accepts a suggestion
- **WHEN** the user selects a suggested name for an unresolved card
- **THEN** that card SHALL be included in the final import list with the selected name

#### Scenario: User types a manual name
- **WHEN** the user types a custom name in the manual input for an unresolved card
- **THEN** the UI SHALL show autocomplete suggestions from the existing suggest endpoint (debounced 300ms)
- **THEN** the selected/typed name SHALL be used in the final import list

#### Scenario: User skips an unresolved card
- **WHEN** the user chooses to skip an unresolved card
- **THEN** that card SHALL be excluded from the final import list

#### Scenario: Bulk accept all suggestions
- **WHEN** the user clicks "Accept all suggestions"
- **THEN** all cards with `status: "suggested"` SHALL use their first suggestion as the resolved name

#### Scenario: Bulk skip all unresolved
- **WHEN** the user clicks "Skip all unresolved"
- **THEN** all unresolved cards SHALL be excluded from the final import list
