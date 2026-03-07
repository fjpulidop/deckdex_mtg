## ADDED Requirements

### Requirement: Insights catalog route returns full catalog list
The system SHALL have HTTP integration tests verifying that `GET /api/insights/catalog` returns a non-empty JSON list where every entry contains `id` and `label` fields, and the response status is 200.

#### Scenario: Catalog returns list with expected shape
- **WHEN** an authenticated client sends `GET /api/insights/catalog`
- **THEN** the response status SHALL be 200, the body SHALL be a JSON list, each entry SHALL contain `id` and `label` fields, and the list SHALL be non-empty

### Requirement: Execute insight route returns result on success
The system SHALL have HTTP integration tests verifying that `POST /api/insights/{insight_id}` returns a 200 response with the standard insight envelope when the insight ID is valid and the service executes successfully.

#### Scenario: Valid insight ID returns envelope
- **WHEN** an authenticated client sends `POST /api/insights/total_cards` with `InsightsService.execute` mocked to return a valid envelope
- **THEN** the response status SHALL be 200 and the body SHALL contain `insight_id`, `question`, `answer_text`, `response_type`, and `data` fields

### Requirement: Execute insight route returns 404 for unknown insight ID
The system SHALL have HTTP integration tests verifying that `POST /api/insights/{insight_id}` returns 404 when `InsightsService.execute` raises `ValueError`.

#### Scenario: Unknown insight ID returns 404
- **WHEN** an authenticated client sends `POST /api/insights/nonexistent_id` and `InsightsService.execute` raises `ValueError`
- **THEN** the response status SHALL be 404

### Requirement: Execute insight route returns 501 for unimplemented insight
The system SHALL have HTTP integration tests verifying that `POST /api/insights/{insight_id}` returns 501 when `InsightsService.execute` raises `NotImplementedError`.

#### Scenario: Unimplemented insight returns 501
- **WHEN** an authenticated client sends `POST /api/insights/some_id` and `InsightsService.execute` raises `NotImplementedError`
- **THEN** the response status SHALL be 501

### Requirement: Execute insight route returns 500 on unexpected error
The system SHALL have HTTP integration tests verifying that `POST /api/insights/{insight_id}` returns 500 when `InsightsService.execute` raises an unexpected `Exception`.

#### Scenario: Unexpected exception returns 500
- **WHEN** an authenticated client sends `POST /api/insights/some_id` and `InsightsService.execute` raises a generic `Exception`
- **THEN** the response status SHALL be 500

### Requirement: Suggestions route returns suggestion list on success
The system SHALL have HTTP integration tests verifying that `GET /api/insights/suggestions` returns a 200 response with a list of suggestion objects, each containing `id` and `label` fields.

#### Scenario: Suggestions returns valid list
- **WHEN** an authenticated client sends `GET /api/insights/suggestions` with `InsightsSuggestionEngine.get_suggestions` mocked to return suggestion objects
- **THEN** the response status SHALL be 200, the body SHALL be a JSON list, and each entry SHALL contain `id` and `label` fields

### Requirement: Suggestions route returns 500 on unexpected error
The system SHALL have HTTP integration tests verifying that `GET /api/insights/suggestions` returns 500 when `InsightsSuggestionEngine` raises an unexpected exception.

#### Scenario: Suggestion engine failure returns 500
- **WHEN** an authenticated client sends `GET /api/insights/suggestions` and `InsightsSuggestionEngine` raises an exception during construction or `get_suggestions`
- **THEN** the response status SHALL be 500
