# Spec Delta

## MODIFIED Requirements

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
