## Why

OpenAI's Completion API (using `text-davinci-003`) is deprecated and will be discontinued. The application currently uses `openai==0.27.8` with the legacy `openai.Completion.create()` interface, which is no longer maintained. We must migrate to the modern Chat Completions API with the latest SDK to ensure continued functionality and access to improved models.

## What Changes

- **Update OpenAI SDK**: Migrate from `openai==0.27.8` to `openai>=1.30.0`
- **Switch API Paradigm**: Replace Completion API (`openai.Completion.create()`) with Chat Completions API (`client.chat.completions.create()`)
- **Adopt JSON Mode**: Replace regex-based response parsing with structured JSON outputs for reliability
- **Update Model**: Transition from `text-davinci-003` to `gpt-3.5-turbo` (with configurable model selection)
- **Enhance Error Handling**: Implement granular exception handling for rate limits, API errors, authentication failures, and invalid responses
- **Refactor Response Parsing**: Remove regex-based parsing in favor of native JSON parsing with validation
- **Update Tests**: Modify all OpenAI-related test mocks to match new SDK structure

## Capabilities

### New Capabilities
- `openai-integration`: Comprehensive specification for OpenAI API integration including authentication, request/response formats, error handling, retry logic, and JSON mode usage for MTG card analysis

### Modified Capabilities
- `api-spec`: Update OpenAI section to reflect modern Chat Completions API, JSON mode requirements, and new error handling patterns

## Impact

**Files Modified**:
- `deckdex/card_fetcher.py`: Complete rewrite of `get_card_info()` method (lines 156-197)
  - Change imports from `import openai` to `from openai import OpenAI, OpenAIError, ...`
  - Replace module-level API key setting with client instantiation
  - Convert single prompt string to messages list (system + user roles)
  - Enable JSON mode in API call
  - Replace regex parsing with `json.loads()`
  - Add specific exception handling for various OpenAI error types
- `requirements.txt`: Update `openai==0.27.8` to `openai>=1.30.0`
- `tests/test_card_fetcher.py`: Update test mocks for new SDK structure
  - Change from `@patch("openai.Completion.create")` to `@patch.object(OpenAI, "chat")`
  - Update mock return values to match new response structure (`message.content` instead of `text`)

**APIs Affected**:
- OpenAI integration: Complete API change from Completion to Chat Completions
- Function signature preserved: `get_card_info()` still returns `Tuple[Dict, Optional[str], Optional[str]]`

**Dependencies**:
- OpenAI Python SDK major version upgrade (breaking changes in SDK)
- No impact on Scryfall or Google Sheets integrations

**Backward Compatibility**:
- External interface unchanged: `get_card_info()` maintains same return type
- Internal consumers (`magic_card_processor.py`) require no changes
- Google Sheets columns (game_strategy, tier) remain identical

**Cost Impact**:
- Cost reduction: `gpt-3.5-turbo` is ~24x cheaper than `text-davinci-003`
- Minimal testing cost: Strategy uses mocks for 99% of tests, 1 real API call for integration test
