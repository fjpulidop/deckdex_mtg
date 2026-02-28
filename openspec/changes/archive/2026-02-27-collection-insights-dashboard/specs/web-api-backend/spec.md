## ADDED Requirements

### Requirement: Insights catalog endpoint
The backend SHALL expose `GET /api/insights/catalog` that returns the full list of available insight questions with their metadata (id, label, label_key, keywords, category, icon, response_type, popular).

#### Scenario: Catalog returns all insights
- **WHEN** an authenticated user calls `GET /api/insights/catalog`
- **THEN** the backend SHALL return a JSON array with all 17 insight entries
- **THEN** each entry SHALL contain at minimum: `id`, `label`, `category`, `response_type`, `keywords`

### Requirement: Insights suggestions endpoint
The backend SHALL expose `GET /api/insights/suggestions` that returns the top 5-6 most relevant insight IDs for the authenticated user based on collection signals.

#### Scenario: Suggestions returned for user with collection
- **WHEN** an authenticated user calls `GET /api/insights/suggestions`
- **THEN** the backend SHALL return a JSON array of 5-6 objects, each containing `id` and `label`
- **THEN** the suggestions SHALL be ordered by relevance score (highest first)

#### Scenario: Suggestions for empty collection
- **WHEN** an authenticated user with no cards calls `GET /api/insights/suggestions`
- **THEN** the backend SHALL return fallback suggestions including `total_cards` and `total_value`

### Requirement: Insights execute endpoint
The backend SHALL expose `POST /api/insights/{insight_id}` that executes the specified insight computation and returns a rich typed response.

#### Scenario: Valid insight execution
- **WHEN** an authenticated user calls `POST /api/insights/total_value`
- **THEN** the backend SHALL return HTTP 200 with a JSON object containing `insight_id`, `question`, `answer_text`, `response_type`, and `data`

#### Scenario: Invalid insight ID
- **WHEN** an authenticated user calls `POST /api/insights/nonexistent`
- **THEN** the backend SHALL return HTTP 404

#### Scenario: Unauthenticated request
- **WHEN** an unauthenticated client calls `POST /api/insights/total_value`
- **THEN** the backend SHALL return HTTP 401
