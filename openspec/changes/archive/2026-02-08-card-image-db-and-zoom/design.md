## Context

- **Card images today**: Backend `card_image_service.get_card_image(card_id)` checks filesystem (`data/card_images/{id}.jpg`); if missing, fetches card by name from Scryfall, downloads image, writes to filesystem, returns bytes. GET `/api/cards/{id}/image` returns those bytes with Content-Type image/jpeg. The spec allows "configured storage (e.g. filesystem)".
- **Card detail modal**: Displays image with `max-w-[244px] max-h-[340px]`. No click-to-zoom; no special cursor. Image is not interactive.

## Goals / Non-Goals

**Goals:**

- Persist card images in PostgreSQL so they survive restarts and do not require re-downloading from Scryfall each session.
- Keep GET `/api/cards/{id}/image` behavior unchanged from the client's perspective (same URL, same response body and status codes).
- In the card detail modal: allow user to click the image to see it larger in a lightbox; close lightbox by clicking overlay or Escape.
- Use cursor affordances: zoom-in (magnifying glass with +) on the small image, zoom-out (magnifying glass with -) on the lightbox, so it is clear that the image is clickable and that clicking the large image returns to the modal.
- **Newest card first in list:** When the user adds a card (e.g. after Process Cards or Add card), the new card SHALL appear first in the card table by default so it is easy to see that it was added, without having to search. Use the existing `created_at` timestamp; default sort SHALL be by date added descending (newest first). The table SHALL still allow sorting by other columns (name, type, rarity, price).

**Non-Goals:**

- Changing the card image API URL or response format.
- Supporting multiple image sizes or formats in storage (single stored image per card is sufficient).
- Migrating existing filesystem images into the DB in this change (can be a follow-up script or task if desired).

## Decisions

### 1. Where to store card images: database table

- **Chosen:** New table **`card_images`** with columns: `card_id BIGINT PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE`, `content_type TEXT` (e.g. `image/jpeg`), `data BYTEA`. One row per card; store the image bytes and content type. Service logic: on GET image request, SELECT from `card_images` by card_id; if row exists, return data and content_type. If not, fetch from Scryfall, INSERT into `card_images`, then return. No requirement to also write to filesystem; filesystem can be deprecated or kept as a local cache at implementer's choice.
- **Rationale:** Keeps persistence with the rest of the app data (Postgres); backups and restores include images; no dependency on a mounted volume. BYTEA is well-supported in PostgreSQL for blobs of this size (typical card image ~50–200 KB).

### 2. Migration and backward compatibility

- **Chosen:** Add a new SQL migration (e.g. `003_card_images_table.sql`) creating `card_images`. Existing `card_image_service` flow: first check DB for existing image; on miss, fetch from Scryfall, then INSERT into DB and return. Optionally: if filesystem image exists and DB has no row, read from file and INSERT into DB so first request after migration fills the DB (optional, can be a separate backfill task).
- **Rationale:** Clean rollout; no change to API contract. Old deployments without the table can be handled by feature-detection or by requiring the migration to be run (same as other tables).

### 3. Lightbox behavior and size

- **Chosen:** Clicking the card image in the modal opens a **lightbox overlay** (full-viewport or near full-viewport dark backdrop, z-index above the modal). The same image URL is displayed at a larger size (e.g. `max-w-[488px] max-h-[680px]` or responsive equivalent, roughly 2× the modal image). Clicking the overlay (backdrop or the large image) closes the lightbox and returns to the modal. Pressing Escape also closes the lightbox. The modal remains open when the lightbox is closed.
- **Rationale:** Familiar pattern; no need to resize the modal; clear "zoom in / zoom out" mental model.

### 4. Cursor affordances

- **Chosen:** On the **small image** in the card detail modal: use **`cursor: zoom-in`** (Tailwind: `cursor-zoom-in`) so the cursor shows a magnifying glass with + on hover, indicating "click to zoom in". On the **lightbox** (the large image or the clickable overlay area): use **`cursor: zoom-out`** (Tailwind: `cursor-zoom-out`) so the cursor shows a magnifying glass with - on hover, indicating "click to zoom out / return to modal".
- **Rationale:** Native CSS cursors are accessible and widely recognized; no custom cursor assets required. Matches user request for "lupita con +" and "lupita con -".

### 5. Default image size in modal (optional)

- **Chosen:** Implementation MAY increase the default image size in the modal slightly (e.g. from `max-w-[244px]` to `max-w-[280px]` or similar) to make it "less small"; this is optional and must not break layout. Spec does not mandate exact pixels.
- **Rationale:** Improves perceived size without forcing a specific value; implementer can tune.

### 6. Newest card first in list

- **Context:** The `cards` table already has `created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')`. After adding a card, the list refreshes but the new card can appear anywhere (e.g. alphabetically by name), so the user has to search for it.
- **Chosen:** (1) Expose **`created_at`** in the card API response as an ISO timestamp string so the frontend can sort by it. (2) Repository `get_all_cards()` SHALL return cards ordered by **`created_at DESC NULLS LAST, id DESC`** so the default order from the API is newest first. (3) In the card table UI, the **default sort** SHALL be by **created_at descending** (newest first); the table SHALL support an **"Added"** column (sortable, showing the date the card was added) so the user sees why the order is as it is and can re-sort by date if they change to another column. Other sort options (name, type, rarity, price) remain available.
- **Rationale:** No new migration (created_at already exists). Newly added cards appear at the top of the first page, making it easy to confirm additions without searching. When syncing this change to main specs, the web-api-backend spec SHALL require the card response to include `created_at` and the list endpoint to return cards in an order that supports "newest first" (e.g. backend orders by created_at desc); the web-dashboard-ui spec SHALL require the card table default sort to be by date added (created_at) descending and an optional "Added" column.

## Risks / Trade-offs

- **Database size:** Storing images in Postgres increases DB size (e.g. hundreds of MB for thousands of cards). Backups and restores take longer. Acceptable for typical collection sizes; monitor if collection grows very large.
- **Lightbox and modal stacking:** Lightbox must render above the modal (higher z-index) and must not close the modal when closing the lightbox (click/Escape only close the lightbox). Stop propagation on the lightbox content so that clicking "close" does not bubble to the modal overlay (which would close the whole modal).

## Migration Plan

- Run new migration `003_card_images_table.sql` (or next number) before or with deploy. Backend reads/writes `card_images`; existing GET `/api/cards/{id}/image` behavior unchanged. Frontend: add lightbox state and handlers, cursor classes. No data migration from filesystem required in this change; optional backfill can be a follow-up.

## Open Questions

- None. Optional: add a one-off script or admin task to backfill `card_images` from existing `data/card_images/*.jpg` files for already-downloaded images.
