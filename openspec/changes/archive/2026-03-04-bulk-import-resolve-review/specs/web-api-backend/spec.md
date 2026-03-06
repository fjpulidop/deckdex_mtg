## MODIFIED Requirements

### Requirement: Import scoped by user
File import and card resolution SHALL create/resolve cards belonging to the authenticated user. The resolve endpoint SHALL use the authenticated user's Scryfall settings to determine whether to use Scryfall as a fallback.

#### Scenario: Import file for user
- **WHEN** an authenticated user calls `POST /api/import/file` with a CSV/JSON file
- **THEN** all imported cards SHALL be created with `user_id` set to the authenticated user's ID

#### Scenario: Resolve uses user's Scryfall setting
- **WHEN** an authenticated user calls `POST /api/import/resolve`
- **THEN** the backend SHALL check the user's `scryfall_enabled` setting to determine whether Scryfall autocomplete is used as a fallback for unresolved cards
