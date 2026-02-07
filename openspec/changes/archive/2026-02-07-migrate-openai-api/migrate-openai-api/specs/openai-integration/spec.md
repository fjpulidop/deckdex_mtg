# OpenAI Integration Specification

## ADDED Requirements

### Requirement: Use Chat Completions API
The system SHALL use OpenAI's Chat Completions API for all LLM interactions.

#### Scenario: Create chat completion request
- **WHEN** the system needs to analyze a card
- **THEN** it SHALL call `client.chat.completions.create()` with a messages array containing system and user roles

#### Scenario: Reject legacy Completion API
- **WHEN** code uses deprecated `openai.Completion.create()`
- **THEN** the system SHALL fail with a clear error message directing to Chat Completions API

### Requirement: Initialize OpenAI client
The system SHALL initialize the OpenAI client once during CardFetcher instantiation.

#### Scenario: Client initialization with API key
- **WHEN** `OPENAI_API_KEY` environment variable is set
- **THEN** the system SHALL create an `OpenAI(api_key=...)` client instance

#### Scenario: Client initialization without API key
- **WHEN** `OPENAI_API_KEY` environment variable is not set
- **THEN** the system SHALL set client to None and log an info message once

#### Scenario: Graceful degradation without API key
- **WHEN** client is None and `get_card_info()` is called
- **THEN** the system SHALL return `(card_data, None, None)` without attempting API calls

### Requirement: Use structured JSON responses
The system SHALL request and parse JSON-formatted responses from OpenAI using JSON mode.

#### Scenario: Enable JSON mode in request
- **WHEN** calling `chat.completions.create()`
- **THEN** the system SHALL include `response_format={"type": "json_object"}` parameter

#### Scenario: Parse JSON response
- **WHEN** OpenAI returns a response
- **THEN** the system SHALL parse `response.choices[0].message.content` using `json.loads()`

#### Scenario: Validate JSON structure
- **WHEN** parsing the JSON response
- **THEN** the system SHALL verify the presence of `strategy` and `tier` keys

#### Scenario: Handle malformed JSON
- **WHEN** `json.loads()` raises `JSONDecodeError`
- **THEN** the system SHALL log a warning and return `(card_data, None, None)`

### Requirement: Format prompts using message roles
The system SHALL structure prompts as message arrays with distinct system and user roles.

#### Scenario: System message defines role
- **WHEN** creating a chat completion
- **THEN** the system message SHALL establish the assistant as an MTG expert that returns JSON

#### Scenario: User message provides task
- **WHEN** creating a chat completion
- **THEN** the user message SHALL contain the card data and request strategy and tier analysis

#### Scenario: Include card text in user message
- **WHEN** constructing the user message
- **THEN** it SHALL include card name, type line, oracle text, and power/toughness or loyalty when present

### Requirement: Use gpt-3.5-turbo model
The system SHALL use the `gpt-3.5-turbo` model by default for card analysis.

#### Scenario: Default model selection
- **WHEN** no model is explicitly configured
- **THEN** the system SHALL use `model="gpt-3.5-turbo"`

#### Scenario: Configurable model via environment
- **WHEN** `OPENAI_MODEL` environment variable is set
- **THEN** the system SHALL use the specified model instead of the default

#### Scenario: Model supports JSON mode
- **WHEN** selecting a model for card analysis
- **THEN** it MUST support JSON mode (gpt-3.5-turbo-1106 or later)

### Requirement: Validate tier values
The system SHALL validate that tier values are within the expected set.

#### Scenario: Valid tier values
- **WHEN** parsing the tier from JSON response
- **THEN** it SHALL only accept values: S, A, B, C, or D (case-insensitive)

#### Scenario: Invalid tier handling
- **WHEN** tier value is not in the valid set
- **THEN** the system SHALL log a warning with the invalid value and set tier to None

#### Scenario: Missing tier in response
- **WHEN** the JSON response does not contain a `tier` key
- **THEN** the system SHALL set tier to None without error

### Requirement: Limit response length
The system SHALL constrain the length of strategy text to prevent excessive output.

#### Scenario: Enforce maximum strategy length
- **WHEN** the strategy text exceeds 500 characters
- **THEN** the system SHALL truncate it to 500 characters

#### Scenario: Request concise responses
- **WHEN** creating the prompt
- **THEN** it SHALL instruct the model to provide strategy in 2-3 sentences maximum

### Requirement: Handle rate limit errors
The system SHALL implement retry logic with exponential backoff for rate limit errors.

#### Scenario: Detect rate limit error
- **WHEN** OpenAI returns a `RateLimitError` (429 status)
- **THEN** the system SHALL catch the specific exception type

#### Scenario: Retry with exponential backoff
- **WHEN** a `RateLimitError` occurs
- **THEN** the system SHALL retry up to 3 times with exponential backoff (1s, 2s, 4s)

#### Scenario: Log rate limit warnings
- **WHEN** retrying due to rate limits
- **THEN** the system SHALL log a warning with attempt number and wait time

#### Scenario: Fail after max retries
- **WHEN** rate limit persists after 3 retry attempts
- **THEN** the system SHALL return `(card_data, None, None)` and log an error

### Requirement: Handle API errors
The system SHALL provide granular error handling for different OpenAI error types.

#### Scenario: Authentication error fails fast
- **WHEN** OpenAI returns `AuthenticationError` (401 status)
- **THEN** the system SHALL log a critical error and not retry

#### Scenario: API connection error retries
- **WHEN** OpenAI returns `APIConnectionError`
- **THEN** the system SHALL retry up to 2 times with 1-second delays

#### Scenario: Invalid request error logs details
- **WHEN** OpenAI returns `InvalidRequestError` (400 status)
- **THEN** the system SHALL log the error message with request details and not retry

#### Scenario: Server error retries once
- **WHEN** OpenAI returns `APIError` (500, 502, 503 status)
- **THEN** the system SHALL retry once after 2 seconds

#### Scenario: Timeout error retries with longer timeout
- **WHEN** a request timeout occurs
- **THEN** the system SHALL retry with increased timeout value

#### Scenario: Generic error handling
- **WHEN** an unexpected error occurs
- **THEN** the system SHALL log the error and return `(card_data, None, None)`

### Requirement: Configure request parameters
The system SHALL set appropriate parameters for chat completion requests.

#### Scenario: Set max tokens
- **WHEN** creating a chat completion
- **THEN** the system SHALL set `max_tokens=150` to limit response length

#### Scenario: Set temperature
- **WHEN** creating a chat completion
- **THEN** the system SHALL set `temperature=0.7` for balanced creativity

#### Scenario: Include model parameter
- **WHEN** creating a chat completion
- **THEN** the system SHALL explicitly specify the `model` parameter

### Requirement: Maintain backward-compatible interface
The system SHALL preserve the existing function signature and return type of `get_card_info()`.

#### Scenario: Function signature unchanged
- **WHEN** `get_card_info(card_name: str)` is called
- **THEN** it SHALL return `Tuple[Dict[str, Any], Optional[str], Optional[str]]`

#### Scenario: Return card data as first element
- **WHEN** `get_card_info()` returns
- **THEN** the first tuple element SHALL be the Scryfall card data dictionary

#### Scenario: Return strategy as second element
- **WHEN** `get_card_info()` returns with successful OpenAI analysis
- **THEN** the second tuple element SHALL be the strategy string or None

#### Scenario: Return tier as third element
- **WHEN** `get_card_info()` returns with successful OpenAI analysis
- **THEN** the third tuple element SHALL be the tier string or None

### Requirement: Import required OpenAI types
The system SHALL import the necessary types and classes from the openai package.

#### Scenario: Import OpenAI client
- **WHEN** the module is loaded
- **THEN** it SHALL import `from openai import OpenAI`

#### Scenario: Import error types
- **WHEN** the module is loaded
- **THEN** it SHALL import `OpenAIError`, `RateLimitError`, `APIConnectionError`, `AuthenticationError`, `InvalidRequestError`, and `APIError` from openai

#### Scenario: Remove deprecated imports
- **WHEN** migrating the code
- **THEN** it SHALL NOT use `import openai` followed by `openai.api_key` pattern
