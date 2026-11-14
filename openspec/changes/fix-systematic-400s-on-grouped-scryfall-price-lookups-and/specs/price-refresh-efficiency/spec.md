# Spec Delta

## MODIFIED Requirements

### Requirement: Grouped price lookup
The bulk refresh SHALL resolve prices for stale cards through grouped lookups, not one request per card, applying the request delay between grouped requests and limiting each group to 75 names. Names the grouped lookup cannot resolve SHALL fall back to the per-card lookup. A grouped failure SHALL trigger per-card fallback unless rate-limit retries are exhausted; exhausted rate-limit failures SHALL propagate without per-card fallback.

#### Scenario: Fewer requests than per-card
- **WHEN** a full refresh runs over N stale cards with distinct names
- **THEN** the number of requests made is lower than N

#### Scenario: Grouped request fails
- **WHEN** a grouped request fails with an error other than an exhausted rate-limit failure
- **THEN** the cards in that group are looked up individually and the job continues
- **AND** a warning records the grouped error, including available Scryfall response detail

#### Scenario: Unresolved name
- **WHEN** a grouped response resolves some names and leaves one unresolved
- **THEN** only the unresolved name receives a per-card lookup

#### Scenario: Rate-limit retries exhausted
- **WHEN** a grouped request exhausts retries with HTTP 429
- **THEN** the rate-limit failure propagates and the group receives no per-card fallback lookups
