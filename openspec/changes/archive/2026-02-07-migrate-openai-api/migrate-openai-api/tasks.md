## 1. Update Dependencies

- [x] 1.1 Update `requirements.txt` to change `openai==0.27.8` to `openai>=1.30.0`
- [x] 1.2 Install updated dependencies with `pip install -r requirements.txt`
- [x] 1.3 Verify no dependency conflicts in installed packages

## 2. Update Imports in card_fetcher.py

- [x] 2.1 Remove old import `import openai`
- [x] 2.2 Add `from openai import OpenAI` import
- [x] 2.3 Add exception imports: `from openai import OpenAIError, RateLimitError, APIConnectionError, AuthenticationError, InvalidRequestError, APIError`
- [x] 2.4 Add `import json` for JSON parsing
- [x] 2.5 Add `from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type` for retry logic

## 3. Initialize OpenAI Client in CardFetcher.__init__

- [x] 3.1 Remove line `self.openai_api_key = os.getenv("OPENAI_API_KEY")` 
- [x] 3.2 Add client initialization: `self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None`
- [x] 3.3 Add `self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")` for configurable model
- [x] 3.4 Add info log when client is None: `logger.info("OpenAI API key not found, card analysis will be disabled")`

## 4. Create Validation Helper Method

- [x] 4.1 Add `_validate_analysis()` method that takes a dict result
- [x] 4.2 Extract and validate `strategy` field (truncate to 500 chars if needed)
- [x] 4.3 Extract and validate `tier` field (must be S/A/B/C/D, case-insensitive)
- [x] 4.4 Log warning if tier is invalid and set to None
- [x] 4.5 Return tuple `(strategy, tier)` with validated values

## 5. Create Retry-Wrapped OpenAI Call Method

- [x] 5.1 Add `_call_openai()` method that takes messages list
- [x] 5.2 Add `@retry` decorator with `stop_after_attempt(3)`, `wait_exponential(min=1, max=10)`, `retry_if_exception_type(RateLimitError)`
- [x] 5.3 Call `self.openai_client.chat.completions.create()` with model, messages, response_format, max_tokens, and temperature
- [x] 5.4 Return the response object
- [x] 5.5 Log warning with attempt number on RateLimitError retry

## 6. Rewrite get_card_info() Method

- [x] 6.1 Keep existing `card_data = self.search_card(card_name)` call
- [x] 6.2 Add early return `if not self.openai_client: return card_data, None, None`
- [x] 6.3 Remove old `import openai` and `openai.api_key` lines from try block
- [x] 6.4 Remove old `openai.Completion.create()` call
- [x] 6.5 Build card_text string (name, type_line, oracle_text, power/toughness, loyalty)
- [x] 6.6 Create system_message dict with role "system" and content describing MTG expert that returns JSON
- [x] 6.7 Create user_message dict with role "user" and content with card analysis request and JSON format instructions
- [x] 6.8 Call `response = self._call_openai([system_message, user_message])`
- [x] 6.9 Parse JSON: `result = json.loads(response.choices[0].message.content)`
- [x] 6.10 Call `strategy, tier = self._validate_analysis(result)`
- [x] 6.11 Return `(card_data, strategy, tier)`

## 7. Add Granular Exception Handling

- [x] 7.1 Add `except AuthenticationError` block: log critical error, return (card_data, None, None)
- [x] 7.2 Add `except RateLimitError` block (after retries exhausted): log error, return (card_data, None, None)
- [x] 7.3 Add `except InvalidRequestError as e` block: log error with details, return (card_data, None, None)
- [x] 7.4 Add `except APIConnectionError` block: log error, return (card_data, None, None)
- [x] 7.5 Add `except APIError` block: log error, return (card_data, None, None)
- [x] 7.6 Add `except json.JSONDecodeError` block: log warning about malformed JSON, return (card_data, None, None)
- [x] 7.7 Update generic `except Exception` block to catch any other errors

## 8. Update Test Mocks in test_card_fetcher.py

- [x] 8.1 Remove `import openai` from test file
- [x] 8.2 Add `from openai import OpenAI` import
- [x] 8.3 Change `@patch("openai.Completion.create")` to `@patch.object(OpenAI, "chat")`
- [x] 8.4 Update mock setup in `test_get_card_info_with_openai` to mock `client.chat.completions.create()`
- [x] 8.5 Update mock response structure to use `message.content` instead of `text`
- [x] 8.6 Change mock return value to include JSON string: `{"strategy": "This is a test strategy.", "tier": "A"}`
- [x] 8.7 Update `self.card_fetcher.openai_api_key` to `self.card_fetcher.openai_client` in test setup
- [x] 8.8 Mock client as `MagicMock()` instance instead of string API key

## 9. Add New Tests for JSON Parsing

- [x] 9.1 Add test for malformed JSON response (JSONDecodeError handling)
- [x] 9.2 Add test for invalid tier value validation
- [x] 9.3 Add test for missing tier key in JSON response
- [x] 9.4 Add test for missing strategy key in JSON response
- [x] 9.5 Add test for strategy truncation (>500 chars)

## 10. Add New Tests for Exception Handling

- [x] 10.1 Add test for RateLimitError with retry behavior
- [x] 10.2 Add test for AuthenticationError (no retry)
- [x] 10.3 Add test for InvalidRequestError (no retry)
- [x] 10.4 Add test for APIConnectionError
- [x] 10.5 Add test for generic APIError

## 11. Run Tests

- [x] 11.1 Run unit tests: `pytest tests/test_card_fetcher.py -v`
- [x] 11.2 Verify all tests pass
- [x] 11.3 Check test coverage for new error handling paths

## 12. Integration Testing

- [ ] 12.1 Set OPENAI_API_KEY in test environment (SKIPPED - requires real API key)
- [ ] 12.2 Create integration test with real API call for one card (e.g., "Lightning Bolt") (SKIPPED - requires real API key)
- [ ] 12.3 Verify JSON response format (SKIPPED - requires real API key)
- [ ] 12.4 Verify strategy and tier are valid values (SKIPPED - requires real API key)
- [ ] 12.5 Check cost of test run (~$0.0001) (SKIPPED - requires real API key)

## 13. Manual Smoke Testing

- [ ] 13.1 Test with a creature card (e.g., "Tarmogoyf") - verify power/toughness included (SKIPPED - requires real API key)
- [ ] 13.2 Test with a planeswalker card (e.g., "Jace, the Mind Sculptor") - verify loyalty included (SKIPPED - requires real API key)
- [ ] 13.3 Test with an instant card (e.g., "Lightning Bolt") - verify basic text handling (SKIPPED - requires real API key)
- [ ] 13.4 Test with an artifact card (e.g., "Sol Ring") - verify type handling (SKIPPED - requires real API key)
- [ ] 13.5 Test with a land card (e.g., "Island") - verify minimal text handling (SKIPPED - requires real API key)
- [ ] 13.6 Verify all responses have valid tier values (S/A/B/C/D) (SKIPPED - requires real API key)

## 14. End-to-End Testing

- [ ] 14.1 Run full processing with `use_openai=True` on small batch (5 cards) (SKIPPED - requires real API key)
- [ ] 14.2 Verify Google Sheets columns populated correctly (strategy, tier) (SKIPPED - requires real API key)
- [ ] 14.3 Verify no regressions in Scryfall data fetching (SKIPPED - requires real API key)
- [ ] 14.4 Verify error handling for cards not found (SKIPPED - requires real API key)

## 15. Check Linter and Code Quality

- [x] 15.1 Run linter on modified files
- [x] 15.2 Fix any linting errors
- [x] 15.3 Verify type hints are correct
- [x] 15.4 Check for unused imports

## 16. Documentation

- [x] 16.1 Add docstring comments for new methods (`_validate_analysis`, `_call_openai`)
- [x] 16.2 Update inline comments explaining JSON mode usage
- [x] 16.3 Document OPENAI_MODEL environment variable in code comments
- [x] 16.4 Update README.md if it documents OpenAI integration (add OPENAI_MODEL variable)

## 17. Verify Cost Reduction

- [x] 17.1 Calculate estimated cost for 100 cards with gpt-3.5-turbo
- [x] 17.2 Compare against previous text-davinci-003 costs
- [x] 17.3 Document cost savings in commit message or PR description
