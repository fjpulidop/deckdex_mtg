## Why

Users cannot quickly view full card details and artwork from the collection table. Downloading all card images on import would be expensive and slow; showing details and artwork on demand (on row click) improves UX and keeps storage and import cost low by fetching and persisting images only when a user opens a card.

## What Changes

- Table rows in the cards table become clickable (excluding clicks on Edit/Delete).
- Clicking a row opens a read-only modal showing that card’s details in a Scryfall-style layout: card image on one side, structured text (name, type, mana cost, oracle text, P/T, set, rarity, price) on the other, using data from our database.
- Card image is loaded on demand: backend looks up by card id; if no image is stored, it fetches the card by name from Scryfall, downloads the image, stores it (filesystem), then serves it. Subsequent views for that card use the stored image.
- New backend endpoint: GET `/api/cards/{id}/image` returns the card image (or 404 if card missing / image unavailable after fetch attempt).

## Capabilities

### New Capabilities

- **card-detail-modal**: Modal that displays a single card’s data (from our API) plus its image (from the image endpoint), in a Scryfall-like layout (image left, text right). Handles loading and error states.
- **card-image-storage**: Backend behavior to resolve card image by id: return stored image if present; otherwise fetch card by name via Scryfall, download image, persist to filesystem, then serve. Includes the GET endpoint contract and storage location.

### Modified Capabilities

- **web-dashboard-ui**: Table rows are clickable to open the card detail modal; Edit/Delete buttons must not trigger row click (e.g. stopPropagation). Dashboard wires the table to the new modal and image API.
- **web-api-backend**: New requirement to provide GET `/api/cards/{id}/image` that returns the card’s image (by id), with on-demand fetch-from-Scryfall-and-store when not yet stored.

## Impact

- **Frontend:** `CardTable.tsx` (row click, optional callback), new `CardDetailModal` (or equivalent), `Dashboard.tsx` (state and wiring). API client: new method for GET card image.
- **Backend:** New route under cards (e.g. `/api/cards/{id}/image`), use of existing `CardFetcher` (Scryfall) and collection repo to get card name by id; new filesystem directory for stored images (e.g. `data/card_images/`).
- **Dependencies:** No new external dependencies; Scryfall public API and existing `deckdex/card_fetcher` are sufficient for image URLs.
