# Web Dashboard UI (delta: newest card first in table)

The card table SHALL show newly added cards first by default and SHALL expose a sortable "Added" column for date added.

## ADDED Requirements

### Requirement: Card table SHALL default to "newest first" sort

The card table SHALL use **date added** (created_at) as the **default sort column**, with **descending** direction (newest first), so that when the user opens the dashboard or refreshes after adding a card, the most recently added cards appear at the top of the first page. The user SHALL still be able to change the sort to name, type, rarity, or price; changing the sort column or direction SHALL behave as today. This ensures that newly added cards are visible immediately without searching.

#### Scenario: Default sort is date added descending
- **WHEN** the user opens the dashboard or the card table is first rendered
- **THEN** the table is sorted by created_at (date added) in descending order so the newest cards appear first

#### Scenario: Newly added card appears at top after refresh
- **WHEN** the user has just added a card (e.g. via Process Cards or Add card) and the list is refetched
- **THEN** that card appears at or near the top of the first page (first row when no other newer cards exist)

#### Scenario: User can change sort to other columns
- **WHEN** the user clicks another column header (e.g. Name, Type, Rarity, Price)
- **THEN** the table re-sorts by that column; the user can also click the "Added" column again to return to newest-first order

### Requirement: Card table SHALL show an "Added" column (date added)

The card table SHALL include an **"Added"** column that displays the date the card was added to the collection (when available), derived from the card's `created_at` value. The column SHALL be **sortable** (same as Name, Type, Rarity, Price) so the user can toggle between newest-first and oldest-first. The column header MAY indicate the current sort (e.g. arrow). When `created_at` is not present for a card, the cell MAY show a placeholder (e.g. "—").

#### Scenario: Added column displays date when available
- **WHEN** a card has a `created_at` value in the API response
- **THEN** the "Added" column displays a human-readable date (e.g. "8 Feb 2025") for that card

#### Scenario: Added column is sortable
- **WHEN** the user clicks the "Added" column header
- **THEN** the table toggles sort direction (ascending/descending) for date added, and the header indicates the current direction (e.g. ↑ or ↓)
