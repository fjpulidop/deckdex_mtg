## Why

The deck builder UI is functionally complete in its major features (deck grid, detail modal, card picker, import), but three specific gaps remain that affect visual quality and correctness: commander card image backgrounds on deck tiles need end-to-end verification, mana curve axis label contrast in dark mode must be confirmed readable, and the deck import text parser's handling of the `//Commander` section header needs an integration test verifying the full round-trip from paste to deck state. These gaps prevent the deck builder from being considered shippable to the alpha audience.

## What Changes

- Verify and, if needed, fix commander card image background rendering with dark overlay in `DeckCardButton` in `DeckBuilder.tsx`
- Verify and, if needed, fix mana curve `XAxis` tick color inheritance in dark mode in `DeckDetailModal.tsx` (the `currentColor` approach against the parent's `dark:text-gray-200` class)
- Validate `//Commander` section header parsing end-to-end by adding a frontend test that exercises `DeckImportModal` submitting text with a `//Commander` section and asserting the imported card is flagged `is_commander: true`
- Add a pytest integration test for the `parse_deck_text` Commander section header path (unit tests already exist in `tests/test_deck_text_parser.py`; verify coverage is sufficient or add edge cases)
- Add a dark-mode visibility test for the mana curve chart label rendering

## Non-goals

- No new API endpoints — all backend parsing is already implemented in `deckdex/importers/deck_text.py`
- No new UI features — this is verification and hardening only
- No backend changes to `DeckRepository` or deck routes
- No changes to `DeckCardPickerModal.tsx` or `DeckImportModal.tsx` logic (only tests)

## Capabilities

### New Capabilities

None. All capabilities are already specced under `deck-builder-ui`.

### Modified Capabilities

- `deck-builder-ui`: Add explicit acceptance criteria for commander image background behavior (no-image fallback), dark mode mana curve axis label readability, and import Commander section header round-trip behavior. These were implied but not given explicit scenarios in the original spec.

## Impact

- `frontend/src/pages/DeckBuilder.tsx` — `DeckCardButton` component: verify `commanderImageUrl` loading and overlay rendering
- `frontend/src/components/DeckDetailModal.tsx` — `BarChart`/`XAxis` dark mode tick color: confirm `currentColor` propagation from Tailwind parent class works in practice
- `frontend/src/locales/en.json` / `es.json` — no changes expected
- `tests/test_deck_text_parser.py` — review existing coverage; add any missing edge cases for `//Commander` header with trailing whitespace variants
- New frontend test file covering dark mode mana curve and import Commander round-trip
