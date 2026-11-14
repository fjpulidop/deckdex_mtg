# Spec Delta

## Purpose

Defines how Scryfall requests identify themselves, surface failure causes, retry and respect rate limits, so grouped price lookups succeed and failures are diagnosable.

## ADDED Requirements

### Requirement: Scryfall requests identify the client
The system SHALL send an explicit User-Agent and `Accept: application/json` on every Scryfall GET and POST request.

#### Scenario: Grouped lookup headers
- **WHEN** a grouped card lookup is posted to Scryfall
- **THEN** the request carries the DeckDex User-Agent and the JSON Accept header

### Requirement: Scryfall error detail is surfaced
When a Scryfall request fails with an HTTP response, the raised error message SHALL include the response status and Scryfall's error detail (and rule when present).

#### Scenario: 400 with body
- **WHEN** Scryfall answers 400 with a JSON body containing `details`
- **THEN** the raised error message contains "Scryfall response:" followed by that detail

### Requirement: Non-429 client errors are not retried
The system SHALL NOT retry a Scryfall request that fails with a 4xx status other than 429.

#### Scenario: 400 is final
- **WHEN** a request returns 400
- **THEN** it is attempted once and the error is raised

### Requirement: Rate limiting pauses all requests
On a 429 the system SHALL pause all Scryfall requests for the Retry-After seconds (default when absent, capped at a maximum) and retry; if the final attempt is still 429 it SHALL raise a rate-limit error.

#### Scenario: Retry-After honoured
- **WHEN** Scryfall answers 429 with a Retry-After header
- **THEN** all requests wait for that period before the retry

#### Scenario: Persistent 429
- **WHEN** every attempt returns 429
- **THEN** a rate-limit error is raised

### Requirement: Grouped lookup fallback
The grouped price lookup SHALL resolve names in chunks within the 75-identifier limit, fall back to per-name lookups for names not resolved or for a chunk whose request failed, and SHALL NOT fall back when the failure is a rate-limit error.

#### Scenario: Failed chunk
- **WHEN** a grouped request fails with a non-rate-limit error
- **THEN** a warning including the error detail is logged and each name is looked up individually

#### Scenario: Rate limited
- **WHEN** a grouped request raises a rate-limit error
- **THEN** the error propagates and no per-card lookups are made
