# Proposal: Cross-Deck Card Allocation Visualization

## Problem Statement

MTG players who maintain multiple Commander decks face a recurring problem: they cannot tell at a glance whether a card in their collection is "committed" to one or more decks, or still available. Today, checking a card's availability requires opening each deck's detail modal individually and scanning the list. For a collector with 10+ decks and a shared pool of 1,000+ cards, this is impractical.

The result: players accidentally build decks around cards already in another deck, or fail to leverage high-value cards sitting unused across the collection.

## Value

This feature delivers a single-screen answer to "where are my cards?" It allows the user to:

- Immediately see which cards are free, committed to one deck, or shared across multiple decks.
- Click any card to learn exactly which decks it belongs to and reallocate in two clicks.
- Make smarter deck-building decisions without context-switching between the deck builder and the collection view.

This is a read-heavy, display-heavy feature with lightweight write actions (remove card from deck). No new data needs to be stored — the allocation state is fully derivable from existing `deck_cards` rows.

## Scope

**In scope:**
- New backend endpoint `GET /api/cards/allocations` returning each card's deck assignments for the current user.
- New frontend page at route `/allocations` with a full card image grid.
- Color-coded status badges on each card tile: green (available / in no deck), orange (in exactly 1 deck), red (in 2+ decks).
- Card detail popover on tile click: shows which deck(s) the card belongs to and a remove-from-deck action per deck.
- Nav link to the new page in the header.
- Backend tests for the new endpoint.
- Frontend tests for the new page and popover.

**Out of scope:**
- Adding cards to decks from this page (use DeckBuilder for that).
- Filtering/sorting the allocation grid beyond the existing collection filters (future iteration).
- Google Sheets support (allocations require Postgres, consistent with all deck features).
- Real-time WebSocket updates (full page refetch after reallocation is acceptable).

## Relationship to Existing Features

The allocation page is a read-only complement to the DeckBuilder (`/decks`). It does not replace any existing screen. It reuses `CardGallery` (or its internals) for the grid, the existing `DeckRepository` for data, and the deck remove-card API that already exists.

## Success Criteria

1. The allocation page loads and renders all collection cards with correct color-coded badges.
2. Clicking a card opens a popover listing assigned decks (0, 1, or many).
3. Removing a card from a deck from the popover calls `DELETE /api/decks/{id}/cards/{card_id}` and the badge updates without a full page reload.
4. Cards in no deck show green; cards in exactly 1 deck show orange; cards in 2+ decks show red.
5. The page is gated by authentication (same as all other data pages).
