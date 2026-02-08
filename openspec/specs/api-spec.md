# API & Integration

**External:** Scryfall (card data/pricing; respect rate limits, backoff). Google Sheets v4 (batchGet/batchUpdate; Service Account). OpenAI optional (strategy/tier) — see [openai-integration](openai-integration/spec.md); Chat Completions API, JSON mode, SDK ≥1.30.

**Internal/CLI:** process_cards(names, use_openai, update_prices) → report {fetched, enriched, updated_rows, errors}; update_prices(force_all); enrich_cards(card_ids). Card payload: id, name, prices, game_strategy, tier. Report: counts + errors[] with name, reason.

**Errors:** not_found, rate_limited, transient_error, permission_denied. Retry with backoff for transient; fail fast for auth. Observability: CLI summaries, optional JSON; verbose toggle.
