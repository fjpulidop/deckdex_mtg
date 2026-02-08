## ADDED Requirements

### Requirement: Backend SHALL provide single-card price update endpoint

The system SHALL provide POST `/api/prices/update/{card_id}` where `card_id` is the surrogate card id (integer). The endpoint SHALL start a background job that updates only that card's price (e.g. from Scryfall) and writes the result to the collection. The response SHALL be JSON with job_id (and optionally status/message) so the client can poll GET `/api/jobs/{job_id}` or use the existing WebSocket progress flow. The job SHALL use the same progress and completion semantics as the bulk price update job (progress events, completion summary, cancellation via POST `/api/jobs/{id}/cancel`). Single-card update jobs MAY run concurrently with each other and with the bulk POST `/api/prices/update` job; the 409 conflict SHALL apply only to concurrent bulk price update requests, not to single-card updates. If the card_id does not exist, the system SHALL return 404.

#### Scenario: POST single-card price update returns job_id
- **WHEN** client sends POST request to `/api/prices/update/{card_id}` with a valid card id
- **THEN** system responds with status 200 and JSON containing job_id (and optionally status/message), and starts a background job that updates that card's price

#### Scenario: Single-card price update job uses same progress and completion as bulk
- **WHEN** a single-card price update job is running
- **THEN** the job reports progress and completion via the same mechanism as the bulk price update (e.g. WebSocket progress, GET /api/jobs/{id} with status and summary when complete)

#### Scenario: Single-card update returns 404 when card not found
- **WHEN** client sends POST request to `/api/prices/update/{card_id}` and no card exists with that id
- **THEN** system responds with status 404 and does not create a job

#### Scenario: Single-card update not blocked by bulk price update
- **WHEN** a bulk price update job is already running (POST `/api/prices/update` returned 200 and job is in progress)
- **THEN** a client MAY successfully start a single-card price update via POST `/api/prices/update/{card_id}` and receive a job_id without receiving 409
