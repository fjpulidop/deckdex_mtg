## 1. Backend – card image storage and endpoint

- [x] 1.1 Define filesystem path for card images (e.g. `data/card_images/`) and ensure directory is created on first write (or at app startup)
- [x] 1.2 Implement helper: given card id, check if image file exists; if not, get card by id from repo (name), call CardFetcher.search_card(name), get image URL from image_uris (normal or large), download image, save to `{images_dir}/{id}.jpg` (or appropriate extension), return file path or bytes
- [x] 1.3 Add GET `/api/cards/{id}/image` route that returns image for card id (use helper); return 404 if card not found or image unavailable; ensure route is matched before generic GET `/api/cards/{card_id_or_name}` (e.g. register more specific path first)
- [x] 1.4 Handle double-faced cards: use first face's image_uris when card has card_faces

## 2. Frontend – API client and card detail modal

- [x] 2.1 Add API client method to get card image URL or blob for a card id (e.g. `getCardImageUrl(id)` returning URL string for use in `img` src, or equivalent)
- [x] 2.2 Create CardDetailModal component: accepts card (Card), onClose callback; layout: image area (left) and text block (right); request image via GET `/api/cards/{card.id}/image` (e.g. as img src); show loading state while image loads; show fallback (message/icon) on image error; display name, type_line, mana_cost, description, power, toughness, set_name, set_number, rarity, price from card
- [x] 2.3 Style modal for Scryfall-like presentation (image + structured text), responsive; close on overlay click and via close button

## 3. Frontend – table row click and dashboard wiring

- [x] 3.1 CardTable: add optional prop `onRowClick?: (card: Card) => void`; on each `<tr>`, add onClick that calls `onRowClick?.(card)`; on Edit and Delete buttons, add `onClick={e => e.stopPropagation()}` so row click does not fire
- [x] 3.2 Dashboard: add state for selected card for detail view (e.g. `detailCard: Card | null`); when `onRowClick(card)` is called, set selected card and show CardDetailModal; when modal closes, clear selected card
- [x] 3.3 Pass `onRowClick` from Dashboard to CardTable; render CardDetailModal when detailCard is set, passing card and onClose
