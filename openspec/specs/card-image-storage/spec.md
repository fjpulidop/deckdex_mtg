# Card Image Storage

Resolve image by card id: return from DB if stored; else fetch by card name from Scryfall, download, persist to DB, then serve. GET /api/cards/{id}/image contract.

### Requirements (compact)

- **Storage:** PostgreSQL (e.g. card_images by card id). Stored images persist across restarts; DB is authoritative so no repeat Scryfall calls.
- **Flow:** GET /api/cards/{id}/image → lookup by id; if stored → 200 + bytes + Content-Type; if not → get card name, fetch Scryfall, download, store, return 200; no card or image unavailable → 404.
