# Web API Backend (delta: card created_at and list order)

Card list and card response SHALL include creation timestamp so the dashboard can show newest cards first.

## ADDED Requirements

### Requirement: Card response SHALL include created_at

The system SHALL include an optional **`created_at`** field in each card object returned by GET `/api/cards` and GET `/api/cards/{id}` (and any other endpoint that returns card data). The value SHALL be an ISO 8601 timestamp string (e.g. from the `cards.created_at` column when using Postgres), or SHALL be omitted if not available (e.g. when the source does not provide it). This allows the frontend to sort and display cards by date added.

#### Scenario: Card list includes created_at when available
- **WHEN** client requests GET `/api/cards` and the collection is stored in Postgres (or another source that provides creation time)
- **THEN** each card object in the response MAY include a `created_at` field with an ISO timestamp string

#### Scenario: Single card response includes created_at when available
- **WHEN** client requests GET `/api/cards/{id}` and the card exists and the store provides creation time
- **THEN** the response MAY include `created_at` with an ISO timestamp string

### Requirement: Card list SHALL be ordered by newest first by default

When the collection is served from a store that supports ordering (e.g. Postgres), GET `/api/cards` SHALL return cards in an order that supports "newest first" as the default UX. For example, the underlying repository SHALL order by `created_at DESC NULLS LAST, id DESC` so that the first page of results contains the most recently added cards. Filtering and pagination SHALL apply to this ordered list so that the same ordering is preserved when filters are applied.

#### Scenario: Unfiltered list returns newest cards first
- **WHEN** client requests GET `/api/cards` without filter parameters (or with only limit/offset)
- **THEN** the returned list is ordered so that the most recently added cards (by created_at) appear first, when the store supports it

#### Scenario: Filtered list preserves newest-first order
- **WHEN** client requests GET `/api/cards` with filter parameters (search, rarity, type, etc.)
- **THEN** the filtered result is ordered so that the most recently added cards in that subset appear first, when the store supports it
