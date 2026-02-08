## Why

Users need to build and save Commander-style decks from their collection. Today the app only manages a flat card list; there is no way to group cards into named decks, view them by section (Commander, Creatures, etc.), or re-use the same collection across multiple decks. This change adds a dedicated deck-builder experience (alpha) so decks can be created, stored, and viewed with a Moxfield-like layout—without enforcing full Commander rules yet.

## What Changes

- New **Commander / Decks** page in the web dashboard (nav next to Analytics), marked **alpha**.
- **Grid view** of decks: first cell is “+” (add deck), remaining cells are deck cards (~half the size of dashboard stat cards); clicking a deck opens a detail modal.
- **Deck detail modal**: list of cards grouped by type (Commander, Creatures, Sorceries, etc.); large commander image that swaps to the hovered card’s image; **Delete** button to remove the deck; **Add** button opening a second modal to pick cards from the current collection (library).
- **Backend**: new deck and deck-card entities and API (create/list/delete decks; add/remove cards from a deck; optional commander designation).
- **Supporting UX**: remove card from deck, edit deck name; no export/import or Commander validation in alpha.

## Capabilities

### New Capabilities

- `decks`: Persistence and API for decks and deck–card membership. Covers deck CRUD, listing decks, and adding/removing cards to/from a deck; optional commander flag or field for display.
- `deck-builder-ui`: Frontend page (route + nav), grid of deck cards with “+” tile, deck detail modal (sections, big image + hover swap, Delete, Add), and card-picker modal over the collection for “Add”.

### Modified Capabilities

- (none)

## Impact

- **Backend**: New tables (or equivalent) for decks and deck_cards; new routes under e.g. `/api/decks/` and `/api/decks/{id}/cards/`. Depends on existing card and collection model.
- **Frontend**: New route and page component; new nav link; new modals and reuse of existing card image API and card list/filters for the picker.
- **Specs**: New `specs/decks/spec.md` and `specs/deck-builder-ui/spec.md` under the change; no changes to existing spec requirements.
