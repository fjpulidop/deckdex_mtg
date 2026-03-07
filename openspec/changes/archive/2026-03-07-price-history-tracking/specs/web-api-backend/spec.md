# Web API Backend — Delta Spec

This delta adds the price history endpoint to the web API backend spec.

## New Endpoint: GET /api/cards/{id}/price-history

**Router file:** `backend/api/routes/cards.py`

**Auth:** Required (same as all `/api/cards/` endpoints — `get_current_user_id` dependency).

**Path params:**
- `id` (int): Surrogate card id.

**Query params:**
- `days` (int, default 90, ge=1, le=365): Time window in days.

**Success response (200):**
```json
{
  "card_id": 42,
  "currency": "eur",
  "points": [
    {
      "recorded_at": "2026-01-01T12:00:00+00:00",
      "price": 3.50,
      "source": "scryfall",
      "currency": "eur"
    }
  ]
}
```
`points` is ordered oldest-first. Empty array if no history exists.

**Error responses:**
- `404`: Card does not exist or does not belong to the requesting user.
- `501`: PostgreSQL not configured (`DATABASE_URL` not set).
- `500`: Unexpected server error.

**Pydantic models:**
- `PriceHistoryPoint`: `recorded_at: str`, `price: float`, `source: str`, `currency: str`
- `PriceHistoryResponse`: `card_id: int`, `currency: str`, `points: list[PriceHistoryPoint]`

**Route ordering constraint:** Must be registered before the `/{card_id_or_name}` catch-all route in `cards.py`. Convention already followed by `/{id}/image`.

**Repository delegation:** Route calls `repo.get_price_history(id, days=days)` — no business logic in the route.
