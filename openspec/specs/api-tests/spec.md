# API Tests

Automated tests for backend API (health, stats, cards list) with mocked collection; no DB or Sheets.

### Requirements (compact)

- **Health:** GET /api/health → 200, body has service, version, status (e.g. "DeckDex MTG API", "0.1.0", "healthy").
- **Stats:** GET /api/stats with mocked collection: empty → total_cards 0, total_value 0, average_price 0, last_updated; non-empty → aggregates consistent with mock; with query params (rarity, set_name, etc.) → filtered subset only.
- **Cards list:** GET /api/cards with mock: empty → 200, []; non-empty → array consistent with mock; limit/offset → correct slice; filters → only matching cards (same semantics as stats).
