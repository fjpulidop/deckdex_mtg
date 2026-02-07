# API Specification Delta

## MODIFIED Requirements

### Requirement: OpenAI API integration
The system SHALL integrate with OpenAI's Chat Completions API (not the deprecated Completion API) to classify game strategy and tier for MTG cards.

The integration SHALL:
- Use the modern `openai` SDK version >= 1.30.0
- Authenticate using `OPENAI_API_KEY` environment variable
- Call the Chat Completions endpoint with structured message format (system + user roles)
- Request JSON-formatted responses using `response_format={"type": "json_object"}`
- Use `gpt-3.5-turbo` model by default (configurable via `OPENAI_MODEL` environment variable)
- Parse responses using `json.loads()` instead of regex patterns
- Implement granular error handling for rate limits, authentication failures, API errors, and connection issues
- Apply exponential backoff retry logic for transient errors (rate limits, connection issues)
- Remain optional - the system SHALL function without OpenAI API access by returning None for strategy and tier fields

#### Scenario: Chat Completions API usage
- **WHEN** analyzing a card with OpenAI enabled
- **THEN** the system SHALL call `client.chat.completions.create()` with messages array

#### Scenario: JSON mode enabled
- **WHEN** requesting card analysis
- **THEN** the system SHALL include `response_format={"type": "json_object"}` in the API call

#### Scenario: Structured prompt format
- **WHEN** constructing the API request
- **THEN** the system SHALL send two messages: a system message defining the MTG expert role and a user message with card details

#### Scenario: Model configuration
- **WHEN** `OPENAI_MODEL` environment variable is not set
- **THEN** the system SHALL use `gpt-3.5-turbo` as the default model

#### Scenario: Response parsing without regex
- **WHEN** OpenAI returns a response
- **THEN** the system SHALL parse `response.choices[0].message.content` as JSON to extract strategy and tier

#### Scenario: Rate limit handling
- **WHEN** OpenAI returns HTTP 429 (rate limit)
- **THEN** the system SHALL retry with exponential backoff up to 3 times

#### Scenario: Authentication error handling
- **WHEN** OpenAI returns HTTP 401 (authentication error)
- **THEN** the system SHALL log a critical error and fail fast without retrying

#### Scenario: Graceful degradation on errors
- **WHEN** OpenAI API calls fail after retries
- **THEN** the system SHALL continue operation with None values for strategy and tier
