## Context

The dashboard shows a table of cards (name, type, rarity, price, set) with pagination and sort. Cards come from Postgres via GET /api/cards; each row has optional Edit/Delete. There is no way to view full card details or artwork without leaving the table. Scryfall exposes card images via `image_uris` on the card object; our `deckdex/card_fetcher` already fetches card data by name (exact then fuzzy) but does not persist or serve images. Storing every card image at import time would be costly for large collections; on-demand fetch-and-store keeps import fast and only stores images that users actually view.

## Goals / Non-Goals

**Goals:**

- Make table rows clickable (except Edit/Delete) and open a read-only detail modal.
- Show card image (from backend) and structured card data (name, type, mana cost, oracle text, P/T, set, rarity, price) in a Scryfall-like layout.
- Backend: resolve image by card id; if not stored, fetch from Scryfall by card name, save to filesystem, then serve; subsequent requests serve from storage.

**Non-Goals:**

- Editing card data from the detail modal (edit stays in existing form modal).
- Choosing which Scryfall printing/set when multiple match the same name (first match is acceptable for v1).
- Double-faced card UI (show one face only for v1; backend can use first face’s image).
- Image format selection (e.g. normal vs large); use one format consistently (e.g. `normal` or `large`).

## Decisions

### 1. Where to store card images

- **Decision:** Store images on the **filesystem** under a dedicated directory (e.g. `data/card_images/`), one file per card id (e.g. `{id}.jpg`).
- **Rationale:** No schema change, simple to implement, easy to serve (read file and stream). Backup/restore can include the directory. If we need to move to object storage or DB later, the API contract (GET by id) stays the same.
- **Alternatives considered:** Table with BLOB or path column (adds migration and complexity); object storage (overkill for single-server v1).

### 2. Image endpoint and route order

- **Decision:** Add GET `/api/cards/{id}/image` where `id` is the surrogate card id (integer). Register this route so it is matched for path `/api/cards/{id}/image` and does not conflict with GET `/api/cards/{card_id_or_name}` (e.g. mount image route with a more specific path or define `/image` sub-path).
- **Rationale:** RESTful and clear: “card resource’s image”. Frontend can request image with card id it already has from the list/detail.
- **Implementation note:** In FastAPI, define the route with path `/api/cards/{id}/image` and ensure it is evaluated before the generic `/api/cards/{card_id_or_name}` (e.g. more specific route first, or use a router prefix like `/api/cards` and route `/{id}/image` before `/{card_id_or_name}`).

### 3. Scryfall image URL and format

- **Decision:** Use Scryfall’s `image_uris['normal']` (or `['large']`) from the card object returned by `CardFetcher.search_card(name)`. Save as JPEG (or keep extension from URL). Single-faced cards have `image_uris` at top level; double-faced: use first face’s `image_uris` for v1.
- **Rationale:** `normal`/`large` are good for modal display; no auth required for Scryfall’s public API. Storing after download avoids repeated Scryfall requests for the same card.

### 4. Frontend modal and image loading

- **Decision:** New component (e.g. `CardDetailModal`) receives the selected `Card`; it displays DB fields in a fixed layout and loads the image via GET `/api/cards/{card.id}/image` (as `img` src or via fetch and blob URL). Show placeholder/skeleton while loading; on error (e.g. 404 or 5xx) show a fallback message or icon.
- **Rationale:** Keeps modal presentational; Dashboard (or parent) owns “which card is selected” and passes it in. Using `img src="/api/cards/123/image"` is simple and benefits from browser caching.

### 5. Edit/Delete vs row click

- **Decision:** Row has `onClick` to open detail modal. Edit and Delete buttons call `event.stopPropagation()` so clicking them does not open the detail modal.
- **Rationale:** Standard UX: row = view details, buttons = actions. Prevents accidental navigation when intending to edit or delete.

## Risks / Trade-offs

- **Scryfall rate limits:** Public API allows ~10 req/s. On-demand fetch is one request per first view per card; acceptable for typical usage. Mitigation: existing retry/backoff in CardFetcher; if we add bulk “prefetch” later, we would need to throttle.
- **Wrong printing for duplicate names:** Same card name can have multiple printings. We do not pass set to Scryfall for v1, so the first match may not match the user’s set. Mitigation: document; future improvement could pass set_name or set_id to narrow search.
- **Disk usage:** Images stored indefinitely. Mitigation: optional cleanup job or “delete images for deleted cards” can be added later; not required for MVP.
- **404 on image:** Card exists but Scryfall fetch fails (e.g. name typo, API down). Mitigation: return 404 or 503 with clear behavior; modal shows error state so user knows image is unavailable.

## Migration Plan

- No DB migrations required (images on filesystem).
- Deploy: ensure `data/card_images/` (or chosen path) is writable by the backend process; directory can be created on first write.
- Rollback: remove new route and frontend modal/row click; no data migration to revert.

## Open Questions

- None blocking. Optional follow-ups: double-faced card both faces in modal; set-aware Scryfall lookup; cache headers for GET image (e.g. long max-age once stored).
