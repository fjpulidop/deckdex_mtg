# Delta Spec: Cross-Deck Card Allocation Visualization

This file documents the additions and changes to existing specs triggered by this feature.

---

## Changes to `openspec/specs/decks/spec.md`

### ADD: Requirement — Card allocation query

```
### Requirement: Card allocation query across all decks

The system SHALL expose a method in DeckRepository (or equivalent data layer) to retrieve
all cards owned by a user alongside the decks they are assigned to. The method SHALL return
a result that allows the caller to determine, for each card: the card's id, name, and
metadata; and the list of deck ids and names that include that card.

#### Scenario: Query with mixed allocation state
- **WHEN** the user has cards in no decks, cards in one deck, and cards in multiple decks
- **THEN** the query result SHALL correctly associate each card with zero, one, or many deck entries

#### Scenario: Query when no decks exist
- **WHEN** the user has cards but no decks
- **THEN** all cards SHALL be returned with an empty deck list
```

---

## Changes to `openspec/specs/web-api-backend/spec.md`

### ADD: Requirement — GET /api/cards/allocations endpoint

```
### Requirement: Card allocations endpoint

The system SHALL expose GET /api/cards/allocations. The endpoint SHALL require authentication
(get_current_user). It SHALL return all cards belonging to the authenticated user, each with
the list of decks the card is assigned to (may be empty). The response SHALL include for each
card: card_id, card_name, image_url, type_line, mana_cost, quantity, and a decks array
(each entry: deck_id, deck_name). When Postgres is not configured, the endpoint SHALL return
HTTP 501. The route SHALL be registered before any wildcard card routes to avoid path conflicts.

#### Scenario: Authenticated user with cards and decks
- **WHEN** the user calls GET /api/cards/allocations with a valid session
- **THEN** the response contains all the user's cards; cards assigned to decks include those
  deck references; cards in no deck have an empty decks array

#### Scenario: Unauthenticated request
- **WHEN** the request has no valid JWT cookie
- **THEN** the endpoint returns HTTP 401

#### Scenario: No Postgres configured
- **WHEN** DATABASE_URL is not set and the user calls GET /api/cards/allocations
- **THEN** the endpoint returns HTTP 501 with a descriptive message
```

---

## Changes to `openspec/specs/deck-builder-ui/spec.md`

### ADD: Requirement — Allocation visualization page

```
### Requirement: Cross-deck card allocation page

The system SHALL provide a page at route /allocations accessible from the main navigation
(labeled e.g. "Allocations" with an "alpha" badge). The page SHALL display all cards in the
user's collection as an image grid. Each card tile SHALL show a color-coded status indicator:
green when the card is in no deck (available), orange when the card is in exactly one deck,
red when the card is in two or more decks. Clicking a card tile SHALL open a detail popover
showing the card's name and the list of decks it is assigned to. When a card is in one or
more decks, each deck entry SHALL have a "Remove" action that removes the card from that deck
and updates the tile status. The page SHALL require authentication. When Postgres is not
available, the page SHALL display an informative message rather than an error.

#### Scenario: Grid displays status badges
- **WHEN** the user navigates to /allocations
- **THEN** each card tile shows a status badge: green (not in any deck), orange (in 1 deck),
  red (in 2+ decks)

#### Scenario: Popover shows deck assignments
- **WHEN** the user clicks a card tile
- **THEN** a popover opens listing the card's name and each deck it belongs to (or a message
  indicating it is available if in no deck)

#### Scenario: Remove card from deck via popover
- **WHEN** the user clicks "Remove" next to a deck in the card allocation popover
- **THEN** the system calls DELETE /api/decks/{deck_id}/cards/{card_id}, the popover updates
  to reflect the removal, and the tile's status badge updates accordingly

#### Scenario: No Postgres
- **WHEN** the backend returns 501 for the allocations request
- **THEN** the page displays a message explaining that deck features require Postgres
  (DATABASE_URL must be configured)
```

---

## No Changes Required

The following specs are unaffected by this feature:

- `openspec/specs/data-model/spec.md` — no schema changes; all data is derivable from existing tables.
- `openspec/specs/decks/spec.md` — existing CRUD endpoints are unchanged; only an additive query method is added.
- All other specs (analytics, settings, CLI, etc.) — fully orthogonal.
