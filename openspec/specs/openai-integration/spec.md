# OpenAI Integration

Chat Completions API only; reject deprecated Completion. Client init once in CardFetcher; no key → client None, get_card_info returns (card_data, None, None).

**Request:** messages (system: MTG expert, JSON; user: card name/type/oracle/power/toughness), response_format={"type":"json_object"}, model (default gpt-3.5-turbo, OPENAI_MODEL env), max_tokens=150, temperature=0.7. Parse response.choices[0].message.content; require strategy, tier keys; malformed JSON → log warning, return (card_data, None, None). Tier: S|A|B|C|D (case-insensitive); invalid/missing → tier None. Strategy max 500 chars; prompt asks 2–3 sentences.

**Errors:** RateLimitError → retry 3× (1s,2s,4s); then return (card_data, None, None). AuthenticationError → no retry. APIConnectionError → 2 retries 1s. InvalidRequestError → log, no retry. APIError 5xx → retry once 2s. Timeout → retry with longer timeout. Other → log, return (card_data, None, None). Import: openai.OpenAI and error types; no legacy api_key pattern. get_card_info(card_name) → Tuple[Dict, Optional[str], Optional[str]] unchanged.
