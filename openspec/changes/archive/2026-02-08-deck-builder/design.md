## Context

- The app has a single collection of cards (Postgres when `DATABASE_URL` is set; otherwise Google Sheets). Cards are served via `GET /api/cards` and related endpoints; there is no concept of "deck" today.
- Frontend: React (Vite), Dashboard (card list + filters), Analytics, Settings. Nav is a header with links; new pages get a new route and a link.
- Card images: `GET /api/cards/{id}/image` (Scryfall fetch + cache). Frontend uses `api.getCardImageUrl(id)`.
- This change introduces decks as a new domain: decks reference cards from the existing collection (by card id). No multi-tenant or per-user isolation in scope; single global list of decks.

## Goals / Non-Goals

**Goals:**

- Persist decks and deck–card membership; expose REST API for deck CRUD and add/remove cards.
- New dashboard page (Commander / Decks, alpha) with grid of decks, deck detail modal (sections, big image + hover, Delete, Add), and card-picker modal from collection.
- Support: create deck (name), list decks, open deck, delete deck, add cards from collection, remove card from deck, edit deck name.

**Non-Goals:**

- Commander rules enforcement (100 cards, color identity, etc.); export/import; duplicate deck; multiple libraries or per-user decks; sharing or public URLs.

## Decisions

1. **Data model (backend)**  
   - **Decision:** Two new concepts: `deck` (id, name, created_at, updated_at) and `deck_card` (deck_id, card_id, quantity, optional is_commander). Store in Postgres (new tables) when DATABASE_URL is set; no deck support when collection is Sheets-only (or document 501/fallback in API).  
   - **Rationale:** Keeps decks independent of the existing collection repo; reuses same DB and connection pattern.  
   - **Alternatives:** Store decks in JSON in a single row (simpler but awkward for querying); separate microservice (overkill for alpha).

2. **Commander display**  
   - **Decision:** One card per deck can be marked as commander (`is_commander` on deck_card, or a `commander_card_id` on deck). Default "big image" in the modal is that card; if none, use first card or placeholder.  
   - **Rationale:** Explicit designation avoids ambiguous "first legend" logic and supports partner/background later.  
   - **Alternatives:** Infer from type (first "Legendary Creature"); no commander (always first card).

3. **Sections (Commander, Creatures, etc.)**  
   - **Decision:** Derive sections in backend or frontend from existing `Card.type` (e.g. split on "—", take first segment: "Creature", "Sorcery", "Legendary Creature"). Commander section = cards with `is_commander` (or deck.commander_card_id). No stored section order in DB.  
   - **Rationale:** No schema change; type is already on card.  
   - **Alternatives:** Store section per deck_card (more flexible, more complexity); fixed section list in UI only.

4. **API shape**  
   - **Decision:** REST under `/api/decks`: `GET/POST /api/decks`, `GET/PATCH/DELETE /api/decks/{id}`, `GET/POST/DELETE /api/decks/{id}/cards` (POST body: card_id, quantity?, is_commander?). **PATCH /api/decks/{id}/cards/{card_id}** with body `{ is_commander?: boolean }` to set or unset commander (when true, all other deck_cards for that deck are set is_commander=false). List deck returns deck + card count or embedded card list; GET deck by id returns deck + cards (with full card payload for UI).  
   - **Rationale:** Matches existing REST style; PATCH deck for name; DELETE deck_card by card_id; explicit PATCH deck_card for commander avoids add/remove tricks.  
   - **Alternatives:** GraphQL (not used elsewhere); single RPC endpoint (inconsistent with rest of API).

5. **Frontend structure**  
   - **Decision:** New page component (e.g. `DeckBuilder` or `CommanderDecks`), route `/decks` or `/commander`, nav link next to Analytics with "alpha" badge. Modals: `DeckDetailModal` (sections, big image + price on hover, Delete, Add), `DeckCardPickerModal` (reuse cards API + search/filters, select cards to add). **From deck detail:** reuse `CardDetailModal` when user clicks a card row (same as Dashboard: view, edit, update price, delete). Deck list rows: quantity left of name, mana cost with `ManaText` icons right; legendary creatures show "Set as Commander" (persisted via PATCH deck card). Grid: CSS grid or flex; first tile "+", rest deck cards (deck name, optional commander thumbnail).  
   - **Rationale:** Mirrors Dashboard + Analytics pattern; reuse `api.getCards`, `api.getCardImageUrl`, `CardDetailModal`, `ManaText`; explicit Set as Commander for legendary creatures.  
   - **Alternatives:** Single-page with tabs (different from current nav); inline list instead of grid (does not match described UX).

6. **Deck grid tile – commander as background**  
   - **Decision:** Each deck tile in the grid uses the commander's card image as full-tile background (when the deck has a commander). Image is top-aligned (`bg-top`) so the top of the art is visible. A uniform dark overlay (`bg-black/55`) covers the whole tile so the deck name and card count remain readable; no separate "top 50%" band. List decks API returns `commander_card_id` so the frontend can build the image URL without an extra request per deck.  
   - **Rationale:** Makes decks visually identifiable at a glance; single overlay avoids alignment issues.  
   - **Alternatives:** Centered thumbnail; gradient only on top half (abandoned due to displacement).

7. **Deck detail modal – header layout**  
   - **Decision:** Single row in the modal header: deck title (editable), total deck value (€), mana curve bar chart (CMC 0–7+), optional CMC filter chip, and buttons (Add card, Delete Deck). All aligned with `flex`; curve labels visible in dark mode via scoped CSS for `.deck-detail-mana-curve`.  
   - **Rationale:** Keeps stats and actions in one place; dark mode fix ensures curve axis labels are readable.  
   - **Alternatives:** Two-row header (rejected in favour of one row).

8. **Add cards picker – filters and list UX**  
   - **Decision:** Picker includes: (1) **Filters:** type (dropdown: Any, Creature, Instant, Sorcery, etc.) and colour (WUBRG using existing mana symbol icons, toggle multiple; cursor pointer on icons). Backend `GET /api/cards` supports `type` (substring match on type line) and `color_identity` (comma-separated; card must contain all selected colours). (2) **List:** each row shows checkbox, name, optional type, and **mana cost with ManaText icons** on the right. (3) **Sort:** dropdown "Sort by" with Name, Mana cost (low→high), Mana cost (high→low); sorting is client-side using `cmc`. Picker requests use path `/api/cards/?...` (trailing slash) so the list route matches.  
   - **Rationale:** Type and colour filters plus CMC sort make it easy to find cards; mana icons match the rest of the app.  
   - **Alternatives:** No filters (poor for large collections); letter labels for colours (replaced by icons for consistency).

9. **When Postgres is not available**  
   - **Decision:** Deck endpoints return 501 or 404 with a clear message that decks require Postgres (or hide nav link when a health/settings endpoint indicates no deck support).  
   - **Rationale:** Avoids partial state (decks in memory or not persisted).  
   - **Alternatives:** In-memory decks (lost on restart); disable only deck creation but allow read (adds complexity).

## Risks / Trade-offs

- **Risk:** Section derivation from `type` may not match every card (e.g. "Legendary Creature — Elf" vs "Creature"). **Mitigation:** Use a small, known set of labels (Commander, Creature, Sorcery, Instant, Enchantment, Artifact, Planeswalker, Land, Other); default to "Other" when no match.
- **Risk:** Modal-on-modal (Add on top of Deck detail) can confuse focus and Escape. **Mitigation:** Escape closes only the top modal; explicit "Cancel" / "Close" on picker; optional focus trap in picker.
- **Trade-off:** No Commander validation in alpha — users can add 200 cards or wrong colors. **Mitigation:** Label page "alpha"; optional future badge "99 cards" or warning without blocking.

## Migration Plan

- Add migration (or startup SQL) to create `decks` and `deck_cards` tables when using Postgres. No change to existing card or collection tables. Deploy backend then frontend; no rollback of card data. If we need to remove feature: drop deck routes and tables in a later change.

## Open Questions

- Confirm route path: `/decks` vs `/commander` for the new page.
- Whether to show "Decks require Postgres" in UI when DATABASE_URL is unset (e.g. in Settings or a banner on the Decks page).
