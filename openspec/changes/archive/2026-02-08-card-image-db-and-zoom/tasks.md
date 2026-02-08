# Tasks: Card image DB storage and modal image zoom

## 1. Database migration

- [x] 1.1 Add migration (e.g. `003_card_images_table.sql`) creating table `card_images` with `card_id BIGINT PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE`, `content_type TEXT`, `data BYTEA`.
- [x] 1.2 Document or run migration so the backend can use the table (e.g. in setup docs or CI).

## 2. Backend: card image service

- [x] 2.1 In card image service (e.g. `get_card_image`): when handling a request for a card id, first query `card_images` for that card_id; if a row exists, return its `data` and `content_type` (status 200).
- [x] 2.2 When no row exists: keep existing flow (look up card by id, get name, fetch from Scryfall, download image). After obtaining image bytes and content type, INSERT into `card_images` (card_id, content_type, data), then return the image. Optionally remove or keep filesystem write; design allows DB-only.
- [x] 2.3 Ensure 404 is returned when card does not exist or image cannot be obtained (unchanged behavior).

## 3. Frontend: card detail modal – lightbox and cursors

- [x] 3.1 Add state for lightbox open/closed (e.g. `imageLightboxOpen: boolean`). When the user clicks the card image (in the modal), set lightbox open. Render a lightbox overlay when open: full-viewport or near full-viewport dark backdrop, z-index above the modal, containing the same image at larger size (e.g. max-w-[488px] max-h-[680px] or responsive equivalent).
- [x] 3.2 Lightbox close: on click of the overlay (backdrop or large image), set lightbox closed. Add keydown listener for Escape to close the lightbox (and ensure it does not close the modal). Use stopPropagation where needed so that closing the lightbox does not bubble to the modal’s overlay click (which would close the modal).
- [x] 3.3 Apply `cursor-zoom-in` (Tailwind) to the card image in the modal so that hovering shows the zoom-in cursor (magnifying glass with +).
- [x] 3.4 Apply `cursor-zoom-out` (Tailwind) to the lightbox overlay or the large image so that hovering shows the zoom-out cursor (magnifying glass with -).
- [x] 3.5 Optional: slightly increase default image size in the modal (e.g. max-w-[280px]) if layout allows.

## 5. Newest card first in list

- [x] 5.1 Expose `created_at` (ISO timestamp string) in the card API response and in the repository `_row_to_card` mapping so the frontend receives it.
- [x] 5.2 In the card table, set default sort to "date added" (created_at) descending so newly added cards appear first; support sorting by created_at (date comparison) alongside existing columns.

## 4. Verification

- [ ] 4.1 Verify GET `/api/cards/{id}/image` returns 200 with image when image exists in DB; after first request, second request does not hit Scryfall (e.g. by checking logs or network). Verify 404 for non-existent card id.
- [ ] 4.2 Verify in UI: open card detail modal, hover image → zoom-in cursor; click image → lightbox opens with larger image; hover lightbox → zoom-out cursor; click or Escape → lightbox closes, modal stays open.
