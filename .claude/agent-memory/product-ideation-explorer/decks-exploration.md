# Decks Exploration (2026-03-07)

## Overview

Full exploration of the Decks feature area: backend API, frontend UI (grid, detail modal, card picker, import/export), repository, migrations, and tests. Comparing spec requirements to actual implementation.

## What Exists (Spec vs Reality)

### Backend: decks.py (9 endpoints) -- ALL IMPLEMENTED

| Endpoint | Spec | Implemented | Tested |
|----------|------|-------------|--------|
| GET /api/decks/ | Yes | Yes | Yes (2 tests) |
| POST /api/decks/ | Yes | Yes | Yes (2 tests) |
| GET /api/decks/{id} | Yes | Yes | Yes (2 tests) |
| PATCH /api/decks/{id} | Yes | Yes | Yes (2 tests) |
| DELETE /api/decks/{id} | Yes | Yes | Yes (2 tests) |
| POST /api/decks/{id}/cards | Yes | Yes | Yes (3 tests) |
| PATCH /api/decks/{id}/cards/{card_id} | Yes | Yes | Yes (2 tests) |
| DELETE /api/decks/{id}/cards/{card_id} | Yes | Yes | Yes (2 tests) |
| POST /api/decks/{id}/import | Yes | Yes | **ZERO tests** |

Total: 18 route tests in test_decks.py + 1 test for 501 scenario = 19 tests. Import endpoint has ZERO tests.

### Repository: deck_repository.py -- COMPLETE

Methods: create, list_all, get_by_id, get_deck_with_cards, update_name, delete, add_card, remove_card, set_commander, find_card_ids_by_names

- find_card_ids_by_names has 7 dedicated tests in test_deck_repository.py
- Other methods have ZERO direct unit tests (only tested indirectly through route tests)

### Parser: deck_text.py -- COMPLETE

- 13 unit tests in test_deck_text_parser.py covering all edge cases
- Clean, well-tested module

### Migration: 004_decks_tables.sql

- Tables: decks (id, name, created_at, updated_at), deck_cards (deck_id, card_id, quantity, is_commander)
- user_id added later in migration 006
- ON DELETE CASCADE on both FKs (good)
- Indexes on deck_cards.deck_id and deck_cards.card_id

### Frontend Components -- ALL IMPLEMENTED

| Component | File | Exists | Spec Match |
|-----------|------|--------|------------|
| DeckBuilder page | pages/DeckBuilder.tsx | Yes | Yes |
| DeckDetailModal | components/DeckDetailModal.tsx | Yes | Yes |
| DeckCardPickerModal | components/DeckCardPickerModal.tsx | Yes | Yes |
| DeckImportModal | components/DeckImportModal.tsx | Yes | Yes |
| Nav link + alpha badge | Navbar.tsx | Yes | Yes |
| Route /decks | App.tsx | Yes | Yes |

### API Client -- COMPLETE

All 9 deck endpoints have typed client methods in client.ts with proper error handling for 501/404.

## Gaps Between Spec and Implementation

### 1. ZERO tests for import endpoint (CRITICAL gap)
- POST /api/decks/{id}/import is the most complex endpoint (parses text, resolves names, handles skipped cards)
- All route-level import logic is untested
- Risk: regression in parsing/resolution flow goes undetected

### 2. N+1 API call pattern in card picker (PERFORMANCE)
- DeckCardPickerModal.tsx line 82-88: `for (const cardId of selected) { await api.addCardToDeck(deckId, cardId); }`
- Adding 10 cards makes 10 sequential HTTP requests
- Should be a batch endpoint: POST /api/decks/{id}/cards/batch with array body

### 3. No deck description/notes field (MISSING FEATURE)
- Spec doesn't mention it, but every competitor (Moxfield, Archidekt, EDHREC) has a description field
- Useful for: power level notes, strategy summary, rule 0 discussion points, primer text
- Schema change: ALTER TABLE decks ADD COLUMN description TEXT

### 4. No format field on decks (MISSING FEATURE)
- Decks have no format (Commander, Standard, Modern, etc.)
- Spec focuses on Commander but schema is format-agnostic without tracking it
- Missing: format-based card count validation (Commander = 100, Standard = 60+15 sideboard)
- Missing: format legality checking (catalog_cards.legalities JSONB exists but unused by decks)

### 5. No sideboard support (MISSING FEATURE)
- deck_cards only has is_commander boolean
- No way to designate sideboard vs mainboard cards
- Import parser treats //Sideboard cards as regular mainboard
- Export only outputs //Commander and //Mainboard sections

### 6. Deck stats are minimal (UX GAP)
- Detail modal shows: total value, mana curve, CMC filter
- Missing: card count total, color identity breakdown, average CMC text, land/nonland ratio
- Competitors show: color pie chart, type distribution, curve stats, card legality warnings

### 7. No deck copy/duplicate (MISSING FEATURE)
- No way to duplicate a deck to iterate on variations
- Common workflow: "clone this deck and swap out 5 cards to try a different strategy"

### 8. No deck tags/categories (MISSING FEATURE)
- No way to organize decks by power level, archetype, or custom tags
- With 10+ decks, the flat grid becomes hard to navigate

### 9. Card quantity management is limited (UX GAP)
- Can add cards (quantity increments via ON CONFLICT DO UPDATE)
- But cannot directly set quantity (e.g., change from 2 to 4)
- No UI to adjust quantity -- only add more or remove entirely

### 10. No card overlap detection across decks (DIFFERENTIATOR)
- "I want to move Sol Ring from Deck A to Deck B but I only own 1 copy"
- No way to see which cards are shared across decks vs which are exclusive
- This is a huge gap in every existing platform

### 11. Export format is basic (MINOR)
- Only MTGO text format
- No Arena format export (uses set codes: "1 Lightning Bolt (2XM) 141")
- No Moxfield CSV, no Archidekt format

### 12. Hardcoded EUR currency (BUG/LIMITATION)
- DeckDetailModal.tsx line 22: `currency: 'EUR'` hardcoded
- Should respect user's currency preference from settings

### 13. No mobile responsiveness in detail modal (UX GAP)
- Left sidebar (w-64) with card image doesn't collapse on mobile
- Header row wraps but gets cluttered on small screens

## Improvement Ideas

### Tier 1: High Impact, Low Effort (do first)

| # | Idea | Value | Effort | Notes |
|---|------|-------|--------|-------|
| 1 | **Test the import endpoint** | High (risk reduction) | Small (~1hr) | Add 5-6 tests: happy path, skipped cards, commander section, empty text, deck not found |
| 2 | **Batch card add endpoint** | High (eliminates N+1) | Small (~2hr) | POST /api/decks/{id}/cards/batch with [{card_id, qty}] array; update picker to use it |
| 3 | **Show total card count in detail header** | Medium (basic info) | Tiny (~15min) | Sum of all card quantities, display next to value |
| 4 | **Respect currency preference** | Medium (correctness) | Small (~30min) | Read from settings context instead of hardcoded EUR |

### Tier 2: High Impact, Medium Effort

| # | Idea | Value | Effort | Notes |
|---|------|-------|--------|-------|
| 5 | **Deck description field** | High (feature completeness) | Medium (~3hr) | Migration + API + UI textarea in modal header |
| 6 | **Deck format field + basic validation** | High (Commander/Standard distinction) | Medium (~4hr) | Migration, format picker in create/edit, card count validation |
| 7 | **Card quantity adjustment UI** | Medium (usability) | Medium (~2hr) | +/- buttons per card row in deck detail |
| 8 | **Deck duplicate/copy** | Medium (workflow) | Small (~2hr) | POST /api/decks/{id}/copy; copies deck + all deck_cards |
| 9 | **Richer deck stats** | Medium (competitive parity) | Medium (~3hr) | Color pie, type distribution, avg CMC, land count |

### Tier 3: High Impact, Large Effort (differentiators)

| # | Idea | Value | Effort | Notes |
|---|------|-------|--------|-------|
| 10 | **Cross-deck card overlap detection** | Very High (unique differentiator) | Large (~8hr) | "Cards used in multiple decks" view; warning when total deck demand > owned copies |
| 11 | **Sideboard support** | High (format correctness) | Medium (~5hr) | New is_sideboard flag or board_type enum on deck_cards; UI sections; export/import |
| 12 | **Format legality warnings** | High (competitive play) | Medium (~5hr) | Cross-ref deck cards with catalog_cards.legalities JSONB; show warnings per card |
| 13 | **Deck tags/categories** | Medium (organization) | Medium (~4hr) | New deck_tags table; tag picker in deck edit; filter grid by tag |

### Tier 4: Nice to Have

| # | Idea | Value | Effort | Notes |
|---|------|-------|--------|-------|
| 14 | **Arena format export** | Low-Medium | Small (~1hr) | Add set code + collector number to export lines |
| 15 | **Mobile-responsive detail modal** | Medium | Medium (~3hr) | Collapse sidebar on mobile, stack layout |
| 16 | **Deck playtest/goldfish mode** | High but Epic | Epic (~40hr+) | Draw hands, simulate turns -- out of scope for now |
| 17 | **Deck card image preview in picker** | Medium | Small (~2hr) | Show card image on hover in the picker modal |

## Key Bugs Found

1. **N+1 card add** (DeckCardPickerModal.tsx:82-88): Sequential await in for-loop, one API call per card
2. **Hardcoded EUR** (DeckDetailModal.tsx:22): Should use settings currency
3. **No import endpoint tests**: Most complex endpoint with zero coverage

## Architecture Notes

- DeckRepository uses raw SQLAlchemy text() queries, not ORM -- consistent with rest of codebase
- add_card uses ON CONFLICT DO UPDATE to handle re-adds (increments quantity) -- good pattern
- set_commander properly unsets all other commanders first in a single transaction
- import endpoint does single-query name resolution via find_card_ids_by_names -- efficient
- But then loops through parsed cards calling add_card one at a time (could batch)

## Competitive Comparison

| Feature | Moxfield | Archidekt | DeckDex |
|---------|----------|-----------|---------|
| Deck CRUD | Yes | Yes | Yes |
| Card sections by type | Yes | Yes | Yes |
| Commander designation | Yes | Yes | Yes |
| Import/Export text | Yes | Yes | Yes |
| Mana curve | Yes | Yes | Yes |
| Deck description | Yes | Yes | **No** |
| Format selection | Yes | Yes | **No** |
| Sideboard | Yes | Yes | **No** |
| Format legality check | Yes | Yes | **No** |
| Card quantity adjust | Yes | Yes | **No** (add only) |
| Deck copy/clone | Yes | Yes | **No** |
| Tags/categories | Folders | Categories | **No** |
| Cross-deck card tracking | **No** | **No** | **No** (opportunity!) |
| Collection-aware (own cards only) | **No** | **No** | **Yes** (differentiator!) |
| Price tracking per deck | Basic | Basic | Yes (with value total) |

## Key Differentiator Opportunity

DeckDex's biggest differentiator is that decks reference YOUR collection. No other major platform does this. This enables:
- "Can I build this deck with cards I own?" -- automatic
- Cross-deck card conflict detection ("You put Sol Ring in 3 decks but only own 1")
- Budget gap analysis ("This deck needs $47 more in cards you don't own")
- Trade list generation from deck wishlists

These are uniquely valuable to Commander players who maintain multiple physical decks from a single collection.

## Recommended Priority Order

1. Test import endpoint (risk reduction, ~1hr)
2. Batch card add endpoint (N+1 fix, ~2hr)
3. Deck description + format fields (feature completeness, ~4hr)
4. Card quantity adjustment UI (~2hr)
5. Cross-deck card overlap detection (differentiator, ~8hr)
6. Richer deck stats (~3hr)
7. Sideboard support (~5hr)
