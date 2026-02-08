## 1. Backend – Data and repository

- [x] 1.1 Add migration or startup SQL: create tables `decks` (id, name, created_at, updated_at) and `deck_cards` (deck_id, card_id, quantity, is_commander)
- [x] 1.2 Implement deck repository (or extend storage layer): create, get by id, list all (with commander_card_id), update name, delete deck; add/remove deck_card; get deck with cards (join to collection for full card payload)
- [x] 1.3 Wire deck repository in API dependencies (only when Postgres available); return 501 or clear error for deck endpoints when Postgres is not configured

## 2. Backend – Deck API routes

- [x] 2.1 Add router under /api/decks: GET /api/decks (list, each item includes commander_card_id), POST /api/decks (body: name), GET /api/decks/{id} (deck + cards; 404), PATCH /api/decks/{id} (name; 404), DELETE /api/decks/{id} (204)
- [x] 2.2 Add POST /api/decks/{id}/cards (body: card_id, quantity?, is_commander?) and DELETE /api/decks/{id}/cards/{card_id}; validate card_id exists in collection (404 if not)
- [x] 2.3 GET /api/cards: support query params type (substring match on type line) and color_identity (comma-separated WUBRG; card must contain all); list URL /api/cards/?... for correct route match

## 3. Frontend – API client and route

- [x] 3.1 Add deck API methods to frontend client: getDecks, getDeck(id), createDeck(name), updateDeck(id, { name }), deleteDeck(id), addCardToDeck(deckId, cardId, opts?), removeCardFromDeck(deckId, cardId)
- [x] 3.2 Add route /decks (or /commander) and nav link with "alpha" badge in App and header (Dashboard, Analytics, Decks, Settings)

## 4. Frontend – Deck builder page and grid

- [x] 4.1 Create DeckBuilder (or CommanderDecks) page component: fetch GET /api/decks, show grid with first cell "+" (add deck), rest deck tiles (name, optional thumbnail/count)
- [x] 4.2 On "+" click: create deck (name prompt or default), then open deck detail modal or refresh grid; on deck tile click open deck detail modal for that deck
- [x] 4.3 Handle 501 or no-deck-support: show message or hide Decks link when backend indicates decks unavailable
- [x] 4.4 Deck tile background: when deck has commander, use commander card image as full-tile background (top-aligned), uniform dark overlay for readability; list API returns commander_card_id

## 5. Frontend – Deck detail modal

- [x] 5.1 Create DeckDetailModal: receive deck id, fetch GET /api/decks/{id}; display cards grouped by section (Commander, Creature, Sorcery, etc.) from card type
- [x] 5.2 Large image area: default commander (or first card); on card row hover swap to that card image (use existing getCardImageUrl)
- [x] 5.3 Add Delete button: call DELETE /api/decks/{id}, close modal, refresh grid; Add button opens card picker modal
- [x] 5.4 Add per-card remove (e.g. remove icon) and deck name edit (input + PATCH); persist and refresh list/title
- [x] 5.5 Header in one row: title, total deck value, mana curve chart, CMC filter chip (when active), Add card / Delete Deck buttons; dark mode: mana curve axis labels readable (scoped CSS)

## 6. Frontend – Card picker modal and polish

- [x] 6.1 Create DeckCardPickerModal: reuse GET /api/cards (search/filters), multi-select cards; on confirm call POST /api/decks/{id}/cards for each; close picker and refresh deck detail list
- [x] 6.2 Picker: Cancel/Close and Escape close only picker; focus and accessibility (optional focus trap)
- [x] 6.3 Responsive and theme (light/dark) for new page and modals; match existing Dashboard/Analytics style
- [x] 6.4 Picker filters: type (dropdown: Any, Creature, Instant, Sorcery, etc.) and colour (WUBRG mana icons, toggle; cursor pointer); backend GET /api/cards supports type (substring) and color_identity (all selected)
- [x] 6.5 Picker list: each row shows mana cost with ManaText icons on the right; sort by Name, Mana cost (low→high), Mana cost (high→low); request uses /api/cards/?... so list route matches

## 7. Set as Commander and deck list UX

- [x] 7.1 Backend: add set_commander(deck_id, card_id) in deck repo and PATCH /api/decks/{id}/cards/{card_id} (body: is_commander)
- [x] 7.2 Frontend: api.setDeckCardCommander(deckId, cardId); in DeckDetailModal show "Set as Commander" for legendary creatures (type contains Legendary + Creature), call API and refresh
- [x] 7.3 Deck list row: quantity left of name, mana cost with ManaText icons to the right; hover preview shows image and price below image
- [x] 7.4 Open CardDetailModal when clicking a card row (reuse Dashboard modal with same options); on card deleted from collection remove from deck view / refresh
