# Spec Delta

## Purpose

Defines Scryfall client identification, diagnosable HTTP failures and bounded retries with shared request scheduling for card lookups.

## ADDED Requirements

### Requirement: Scryfall requests identify the client
Scryfall GET and POST requests SHALL send `User-Agent: DeckDex/1.0 (MTG collection manager)` and `Accept: application/json`.

#### Scenario: Grouped lookup headers
- **WHEN** a grouped card lookup is posted to Scryfall
- **THEN** it carries the DeckDex User-Agent and JSON Accept header

#### Scenario: Individual lookup headers
- **WHEN** a Scryfall GET lookup is sent
- **THEN** it carries the same client identification and JSON Accept header

### Requirement: Scryfall error detail is surfaced
A propagated HTTP response failure SHALL retain the original HTTP error text and append available JSON `details` and `rule`. If decoding or reading those JSON fields fails, it SHALL append up to 300 characters of response text. Without usable body detail it SHALL retain the original error text.

#### Scenario: 400 with body
- **WHEN** a 400 error message accompanies JSON containing `rule: generic_user_agent` and `details: Use a custom UA`
- **THEN** the propagated message includes the original 400 text, rule and detail

#### Scenario: Non-JSON error
- **WHEN** a failed response body cannot be decoded as JSON
- **THEN** the error includes at most the first 300 characters of response text

### Requirement: Non-429 client errors are not retried
Scryfall 4xx responses other than 429 SHALL propagate after one attempt. Other request failures SHALL retain the configured attempt budget and exponential retry delay, except that 429 SHALL use the shared cooldown policy.

#### Scenario: 400 is final
- **WHEN** a request returns 400
- **THEN** it is attempted once and the enriched error propagates

#### Scenario: Transient request failure
- **WHEN** a request fails without an HTTP response and the next configured attempt succeeds
- **THEN** the request is retried and its successful result is returned

### Requirement: Requests use shared pacing
Requests SHALL reserve times using one process-shared schedule, with intervals of 0.1 seconds for GET and 0.5 seconds for POST. A reservation SHALL wait until its scheduled time before sending.

#### Scenario: Consecutive grouped requests
- **WHEN** two grouped POST requests reserve times immediately in succession
- **THEN** the second waits for the remaining POST interval

### Requirement: Rate limiting pauses all requests
A non-final 429 SHALL log the status and wait duration, postpone future reservations on the shared schedule, and retry within the configured attempt budget. Numeric Retry-After seconds SHALL be clamped to 0–120; an absent or unparseable value SHALL use 60 seconds. A final 429 SHALL propagate as an exhausted rate-limit failure.

#### Scenario: Retry-After honoured
- **WHEN** a non-final 429 supplies Retry-After of 7 seconds
- **THEN** future shared request reservations are deferred by at least 7 seconds from the cooldown calculation
- **AND** another attempt is made

#### Scenario: Missing Retry-After
- **WHEN** a non-final 429 has no parseable Retry-After value
- **THEN** the shared schedule receives a 60-second cooldown

#### Scenario: Persistent 429
- **WHEN** every configured attempt returns 429
- **THEN** an exhausted rate-limit failure propagates after the final attempt

### Requirement: Collection lookup omits blank identifiers
A collection lookup SHALL reject input lists longer than 75 before filtering, omit empty and whitespace-only names, and send remaining names unchanged. If none remain it SHALL return empty found and unresolved lists without an HTTP request.

#### Scenario: Mixed names
- **WHEN** names are A, empty string and whitespace-only string
- **THEN** only A is sent in the identifiers array

#### Scenario: No usable names
- **WHEN** all input names are blank
- **THEN** both result lists are empty and no request is sent

#### Scenario: Oversized input
- **WHEN** more than 75 names are supplied
- **THEN** the lookup rejects the input before posting
