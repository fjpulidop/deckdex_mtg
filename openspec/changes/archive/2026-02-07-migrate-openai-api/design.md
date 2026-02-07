## Context

The application currently uses OpenAI's deprecated Completion API (`text-davinci-003` model) via the legacy `openai==0.27.8` SDK. OpenAI has deprecated this API and will discontinue it, requiring migration to the modern Chat Completions API.

**Current Implementation** (`deckdex/card_fetcher.py` lines 156-197):
- Module-level API key configuration: `openai.api_key = self.openai_api_key`
- Direct call: `openai.Completion.create(engine="text-davinci-003", prompt=..., max_tokens=150, temperature=0.7)`
- Single string prompt with formatting instructions
- Response parsing via regex: `re.search(r"Strategy: (.*?)(?:\n|$)", response.choices[0].text)`
- Generic exception handling with silent failure (returns None values)

**Constraints**:
- Must maintain backward compatibility with `get_card_info()` function signature
- Must minimize testing costs during development (mock-heavy testing strategy)
- Must preserve existing behavior for consumers in `magic_card_processor.py`
- Must handle missing API key gracefully (optional feature)
- Must work with existing error handling patterns in the codebase

**Stakeholders**:
- Card analysis functionality (strategy and tier generation)
- Cost management (testing and production usage)
- Future maintainability (using modern, supported APIs)

## Goals / Non-Goals

**Goals:**
- Migrate to OpenAI Chat Completions API with modern SDK (v1.30.0+)
- Improve reliability by replacing regex parsing with structured JSON outputs
- Implement granular error handling for better observability and retry logic
- Reduce operational costs by using more efficient models (gpt-3.5-turbo vs text-davinci-003)
- Make model selection configurable for future flexibility
- Maintain 100% backward compatibility with existing interfaces

**Non-Goals:**
- Changing the function signature or return type of `get_card_info()`
- Implementing caching of OpenAI responses (can be added later)
- Supporting multiple LLM providers (OpenAI only for now)
- Modifying the content or format of strategy/tier outputs
- Changing how `magic_card_processor.py` consumes the function
- Adding new analysis fields beyond strategy and tier

## Decisions

### Decision 1: Use JSON Mode Instead of Regex Parsing

**Chosen**: OpenAI JSON mode (`response_format={"type": "json_object"}`)

**Rationale**:
- OpenAI guarantees valid JSON output in JSON mode, eliminating regex brittleness
- Native JSON parsing with `json.loads()` is more robust than regex patterns
- Easier to extend with additional fields in the future (e.g., deck archetypes, combo pieces)
- Better error handling (JSONDecodeError is specific, regex failure is silent)
- Industry best practice for structured LLM outputs

**Alternatives Considered**:
- **Keep regex parsing**: Simple migration path, but maintains fragility and parsing bugs
- **Function calling / tools**: Over-engineered for simple key-value extraction
- **XML format**: Less ergonomic than JSON, no native OpenAI support

**Trade-offs**: Requires prompt to explicitly request JSON format, adds JSON parsing dependency

### Decision 2: Use gpt-3.5-turbo as Default Model

**Chosen**: `gpt-3.5-turbo` with configurable override via `OPENAI_MODEL` environment variable

**Rationale**:
- Comparable quality to `text-davinci-003` for structured analysis tasks
- ~24x cheaper ($0.0015/1K output tokens vs $0.02/1K tokens)
- Faster response times (1-2s vs 2-4s)
- Native support for Chat Completions and JSON mode
- Aligns with OpenAI's recommended migration path

**Alternatives Considered**:
- **gpt-4**: Superior analysis quality but 40x more expensive and slower; overkill for tier rating
- **gpt-4-turbo**: Better balance but still 10x more expensive than gpt-3.5-turbo
- **Fixed model**: Less flexible; env var allows A/B testing and upgrades without code changes

**Trade-offs**: Quality slightly lower than GPT-4, but acceptable for card tier classification

### Decision 3: Implement Retry Logic with tenacity

**Chosen**: Use existing `tenacity` library (already in requirements.txt) for exponential backoff

**Rationale**:
- Library already present in project dependencies (no new dependency)
- Declarative retry configuration with decorators
- Built-in exponential backoff and jitter support
- Handles multiple exception types cleanly
- Standard pattern in Python ecosystem

**Alternatives Considered**:
- **Manual retry loops**: More control but boilerplate and error-prone
- **OpenAI SDK built-in retries**: Limited customization, less explicit

**Trade-offs**: Adds decorator indirection, but significantly improves reliability

### Decision 4: Separate System and User Messages

**Chosen**: Use two-message format with distinct system and user roles

**Rationale**:
- System message establishes persistent context ("You are an MTG expert...")
- User message contains variable task data (card details)
- Aligns with OpenAI best practices for Chat Completions
- Easier to modify prompts independently (role vs task)
- Better model adherence to output format instructions

**Alternatives Considered**:
- **Single user message**: Simpler but less effective prompt engineering
- **Multi-turn conversation**: Unnecessary complexity for single-shot analysis

**Trade-offs**: Slightly more verbose prompt construction, marginal token cost increase

### Decision 5: Initialize Client Once in __init__

**Chosen**: Create `self.openai_client` during `CardFetcher.__init__()` with None if no API key

**Rationale**:
- Fail-fast on initialization errors (invalid API key format)
- Avoids repeated client instantiation overhead
- Clear separation: initialization vs usage
- Aligns with class-based design pattern already in use
- Enables single log message when OpenAI is disabled

**Alternatives Considered**:
- **Lazy initialization on first call**: Delays errors, harder to test
- **Module-level client**: Less testable, global state issues

**Trade-offs**: Slightly earlier failure if API key is malformed, but that's desirable

### Decision 6: Granular Exception Handling

**Chosen**: Catch specific OpenAI exception types with different handling strategies

**Exception Strategy**:
```
RateLimitError (429)       → Retry 3x with exponential backoff
APIConnectionError         → Retry 2x with fixed delay
AuthenticationError (401)  → Fail fast, log critical, no retry
InvalidRequestError (400)  → Log error with details, no retry
APIError (500, 502, 503)   → Retry 1x after delay
Timeout                    → Retry with increased timeout
JSONDecodeError            → Log warning, return None values
Generic Exception          → Log error, return None values
```

**Rationale**:
- Different error types require different handling strategies
- Rate limits are transient and should be retried
- Auth errors indicate configuration issues (no point retrying)
- Server errors may be transient (limited retries)
- JSON errors indicate prompt/model issues (should not retry)
- Preserves existing graceful degradation behavior

**Alternatives Considered**:
- **Catch-all exception handling**: Simpler but loses observability and retry optimization
- **Propagate all errors**: Breaks existing behavior, impacts consumers

**Trade-offs**: More verbose error handling code, but significantly better debugging and reliability

## Risks / Trade-offs

**[Risk] OpenAI JSON mode not guaranteed for all models**
→ **Mitigation**: Document minimum model version (gpt-3.5-turbo-1106+) in code comments and validate at runtime with helpful error message

**[Risk] Breaking changes in future OpenAI SDK versions**
→ **Mitigation**: Pin to `openai>=1.30.0,<2.0.0` in requirements.txt; monitor deprecation notices

**[Risk] JSON parsing failures if model ignores format instructions**
→ **Mitigation**: Graceful degradation to None values; log warnings for investigation; JSON mode makes this unlikely

**[Risk] Rate limits during batch processing (100+ cards)**
→ **Mitigation**: Exponential backoff with 3 retries; existing 0.05s delay between cards helps; consider adding configurable rate limiting

**[Risk] Cost increase if model selection is misconfigured**
→ **Mitigation**: Default to gpt-3.5-turbo; log model selection at startup; document env var in README

**[Risk] Test mocks may not accurately reflect real API behavior**
→ **Mitigation**: Include 1 integration test with real API call (minimal cost); document expected response format

**[Risk] Tier validation may reject valid future additions**
→ **Mitigation**: Log invalid tiers but set to None (graceful); easy to extend valid set in code

**[Trade-off] JSON mode requires explicit prompt instructions**
→ **Accepted**: Small prompt overhead (~10 tokens) for guaranteed structured output

**[Trade-off] Retry logic increases latency on failures**
→ **Accepted**: Better to retry and succeed than fail immediately; exponential backoff limits max delay

**[Trade-off] More complex error handling code**
→ **Accepted**: Improved observability and reliability justify complexity; centralized in one method

## Migration Plan

**Phase 1: Update Dependencies**
1. Update `requirements.txt`: `openai>=1.30.0`
2. Run `pip install -r requirements.txt` in dev environment
3. Verify no dependency conflicts

**Phase 2: Implement Changes**
1. Modify `deckdex/card_fetcher.py`:
   - Update imports (add OpenAI client and exception types)
   - Add client initialization in `__init__`
   - Rewrite `get_card_info()` method with new API
   - Add `_validate_analysis()` helper method for tier validation
   - Add `_call_openai()` method with retry logic using tenacity
2. Update `tests/test_card_fetcher.py`:
   - Modify mock patches for new SDK structure
   - Add tests for JSON parsing
   - Add tests for specific exception types
   - Update assertions for new response structure

**Phase 3: Testing**
1. Run unit tests with mocks (no API calls): `pytest tests/test_card_fetcher.py`
2. Run single integration test with real API key (1 card, ~$0.0001)
3. Manual smoke test with 5 diverse cards (creature, planeswalker, instant, artifact, land)
4. Verify Google Sheets integration still works end-to-end

**Phase 4: Deployment**
1. Update `.env` documentation with `OPENAI_MODEL` variable
2. Monitor first 100 production API calls for errors
3. Validate cost reduction vs previous model

**Rollback Strategy**:
- Git revert is sufficient (single PR, no database changes)
- No data migration required (stateless API change)
- Environment variables are additive (OPENAI_MODEL optional)

## Open Questions

**Q: Should we add caching for repeated card analyses?**
- Decision: No, out of scope for this migration. Can be added later if cost becomes an issue.
- Caching would require: key generation (card name + model version), storage backend (Redis/file), TTL policy

**Q: Should we support custom prompt templates via configuration?**
- Decision: No, keep prompts in code for this version. Prompt engineering is stable for tier classification.
- Could be added later if users request different analysis styles

**Q: Should we add metrics/telemetry for OpenAI usage?**
- Decision: Not in initial implementation. Existing logging is sufficient.
- Future enhancement: could track (model, tokens, latency, cost) per request
