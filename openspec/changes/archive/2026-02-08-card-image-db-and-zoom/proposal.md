## Why

Today card images are downloaded from Scryfall on demand and stored on the filesystem. If the app runs in an environment where that directory is not persistent (e.g. ephemeral containers), images are re-downloaded every session. Storing images in the database ensures they persist with the rest of the collection and survive restarts and redeploys. Separately, the card image in the detail modal is relatively small and there is no way to view it larger; users want to click to see a zoomed view and to have clear cursor hints (zoom-in on the thumbnail, zoom-out on the enlarged view) that the image is interactive.

## What Changes

- **Card image storage in database**: The system SHALL store card images in PostgreSQL (e.g. a `card_images` table) once they are downloaded from Scryfall. GET `/api/cards/{id}/image` SHALL read from the database when an image exists for that card id; when it does not, the system SHALL fetch from Scryfall, store the image in the database, then return it. Images SHALL persist across sessions and deployments. The existing filesystem path MAY remain as an optional cache or be removed per design.
- **Card detail modal: image zoom and cursors**: The card image in the detail modal SHALL be clickable. Clicking it SHALL open a lightbox (overlay) showing the same image at a larger size (e.g. roughly twice the modal size). The lightbox SHALL close on click (returning to the modal) or on Escape. The small image in the modal SHALL show a zoom-in cursor (e.g. `cursor: zoom-in` / magnifying glass with +) on hover to indicate it can be enlarged. The large image in the lightbox SHALL show a zoom-out cursor (e.g. `cursor: zoom-out` / magnifying glass with -) on hover to indicate that clicking will return to the modal. The modal MAY show the image slightly larger by default (e.g. increased max-width) as a non-breaking improvement.

## Capabilities

### New Capabilities

- **card-image-storage (backend)**: Persist card images in the database (e.g. `card_images` table) so that once an image is fetched from Scryfall it is stored and served from the DB on subsequent requests, without re-downloading.
- **card-detail-modal (frontend)**: Image zoom: click on the card image to open a lightbox with a larger view; close by clicking the overlay or pressing Escape. Cursor affordances: zoom-in on the small image, zoom-out on the lightbox image.

### Modified Capabilities

- **card-image-storage**: Storage SHALL be database-first (or database-only for new writes); the GET `/api/cards/{id}/image` contract (response body and status codes) remains unchanged.
- **card-detail-modal**: The modal SHALL display the card image with zoom-in cursor on hover and SHALL support opening a lightbox with a larger image on click; the lightbox SHALL display the image with zoom-out cursor and SHALL close on click or Escape.

## Impact

- **Backend**: New migration for `card_images` table (e.g. `card_id` PK/FK, `content_type`, `data` BYTEA). Card image service: read from DB first; on miss, fetch from Scryfall and insert into DB (and optionally write to filesystem or not). No change to the HTTP API shape.
- **Frontend**: CardDetailModal: state for lightbox open/closed; make image clickable; render lightbox overlay when open (large image, dark backdrop); apply `cursor: zoom-in` to the modal image and `cursor: zoom-out` to the lightbox image/image area; handle Escape to close lightbox.
- **Main specs (sync on archive)**: When archiving this change, sync the following deltas into the main specs: (1) **card-image-storage** — persist images in database; (2) **card-detail-modal** — image zoom (lightbox) and cursor affordances; (3) **web-api-backend** — card response includes `created_at`, list ordered by newest first; (4) **web-dashboard-ui** — card table default sort by date added (created_at desc), "Added" column sortable. Main spec files: `openspec/specs/card-image-storage/spec.md`, `openspec/specs/card-detail-modal/spec.md`, `openspec/specs/web-api-backend/spec.md`, `openspec/specs/web-dashboard-ui/spec.md`.

- **Newest card first in list**: When the user adds a card (e.g. after Process Cards or Add card), the new card SHALL appear first in the card table by default so it is easy to see that it was added. The system SHALL use the existing `created_at` timestamp on the cards table and SHALL order the list by creation date descending by default (newest first). The card table MAY still allow sorting by other columns (name, type, rarity, price); the default sort SHALL be by date added (newest first).
