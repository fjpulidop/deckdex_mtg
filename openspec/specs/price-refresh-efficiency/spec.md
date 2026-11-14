# price-refresh-efficiency Specification

## Purpose
Makes the bulk price refresh fast and cheap: it only looks up cards whose price is stale, resolves them with grouped lookups, and records when each card was last checked so repeated runs do not repeat work.

## Requirements

### Requirement: Per-card last-checked timestamp
The system SHALL store a nullable UTC timestamp of the last price lookup per card, set for every looked-up card whether or not its price changed. Freshness SHALL NOT be inferred from price history.

#### Scenario: Never-refreshed card is stamped
- **WHEN** a refresh looks up a card whose last-checked value is NULL
- **THEN** the card's last-checked timestamp is set to the lookup time

#### Scenario: Unchanged price still stamped
- **WHEN** a looked-up card's price equals its stored price
- **THEN** its last-checked timestamp is updated and no price history row is added

### Requirement: Stale-card selection
The bulk refresh SHALL look up only stale cards. A card is stale when force is set, the freshness window is 0, its last-checked value is NULL, or the time since last check exceeds the window.

#### Scenario: Fresh cards are skipped
- **WHEN** a refresh runs and a card was checked within the freshness window
- **THEN** the card is not looked up and is counted in `skipped_fresh`

#### Scenario: Immediate re-run
- **WHEN** a refresh completes and is started again within the window without force
- **THEN** zero lookups are made and every card is reported as `skipped_fresh`

#### Scenario: Force bypasses freshness
- **WHEN** a refresh runs with force set
- **THEN** fresh cards are looked up anyway

### Requirement: Freshness window configuration
The processing configuration SHALL provide a price freshness window in seconds, an integer of 0 or more, where 0 means always refresh.

#### Scenario: Negative window rejected
- **WHEN** the configuration sets the freshness window below 0
- **THEN** configuration validation fails with an error

### Requirement: Grouped price lookup
The bulk refresh SHALL resolve prices for stale cards through grouped lookups, not one request per card, applying the request delay between grouped requests. Names the grouped lookup cannot resolve SHALL fall back to the per-card lookup.

#### Scenario: Fewer requests than per-card
- **WHEN** a full refresh runs over N stale cards with distinct names
- **THEN** the number of requests made is lower than N

#### Scenario: Grouped request fails
- **WHEN** a grouped request fails
- **THEN** the cards in that group are looked up individually and the job continues
- **AND** a warning records the grouped error, including available Scryfall response status and detail

#### Scenario: Grouped rate limit exhausts retries
- **WHEN** a grouped lookup still returns 429 after its configured retry budget
- **THEN** every card in that group falls back to an individual lookup
- **AND** the grouped warning includes the available 429 response detail

### Requirement: Price and history writes
The refresh SHALL persist a changed price together with the checked timestamp, and SHALL add exactly one price history row per card whose price changed to a numeric value.

#### Scenario: Changed price
- **WHEN** a looked-up card's price differs from its stored price
- **THEN** the stored price is updated and exactly one price history row is added

#### Scenario: Non-numeric price
- **WHEN** the new price is not numeric
- **THEN** the price update is stored, no history row is added and the job continues

### Requirement: Per-card failures do not abort the job
Cards that are not found, have no usable name, or return a non-numeric price SHALL be counted in the summary and SHALL NOT abort the job.

#### Scenario: Card not found
- **WHEN** a card cannot be found by the price source
- **THEN** it is reported in `error_count` and `not_found_cards` and other cards are still processed

### Requirement: Cancellation keeps written work
When a refresh is cancelled, cards already written SHALL keep their new price and checked timestamp.

#### Scenario: Cancel mid-run
- **WHEN** a refresh is cancelled after some groups were written
- **THEN** those cards keep their price and timestamp and later cards are untouched

### Requirement: Force option on the update endpoint
`POST /api/prices/update` SHALL accept an optional body with a boolean `force` (default false), SHALL keep working with no body, and SHALL keep its response shape and single-running-job guard.

#### Scenario: No body
- **WHEN** the endpoint is called without a body
- **THEN** a job is created with force false

#### Scenario: Force true
- **WHEN** the endpoint is called with `{"force": true}`
- **THEN** the job ignores the freshness window

#### Scenario: Job already running
- **WHEN** a price update job is already running
- **THEN** the endpoint responds 409

### Requirement: Refresh summary
The completion payload SHALL keep `status`, `error_count` and `not_found_cards` and SHALL add `cards_checked`, `skipped_fresh`, `prices_changed`, `requests_made` and `elapsed_seconds`.

#### Scenario: Everything fresh
- **WHEN** every card is fresh and force is not set
- **THEN** the job completes successfully with `cards_checked` 0, `requests_made` 0 and `skipped_fresh` equal to the number of cards
