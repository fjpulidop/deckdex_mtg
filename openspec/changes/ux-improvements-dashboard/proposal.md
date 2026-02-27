## Why

Four small pain points chip away at the daily usability of the dashboard:

1. **No color filter.** The backend already supports `color_identity` filtering but the UI never exposes it. MTG players think in colors first; having to mentally map colors to type/set filters is friction.
2. **Browser dialogs break the experience.** Three spots use `window.confirm()` or `window.prompt()`: card deletion (`CardDetailModal`), deck deletion (`DeckDetailModal`), and new-deck naming (`DeckBuilder`). Native browser dialogs cannot be styled, block the thread, and feel jarring in an otherwise polished UI.
3. **Paginating the card table loses your scroll position.** After clicking "Next" or "Previous" the content stays wherever it was — the user has to scroll back up manually every time.
4. **No keyboard navigation in the card table.** Power users with large collections have no way to navigate rows without a mouse. Arrow keys and Enter are the natural affordance.

## What Changes

- **Color filter toggle bar:** A row of five color-symbol toggles (W/U/B/R/G) is added to `Filters`. Selecting one or more passes a comma-separated `color_identity` param to GET `/api/cards` and GET `/api/stats` (existing params, zero backend work).
- **Confirmation modal component:** A small, reusable `ConfirmModal` replaces all three `window.confirm`/`window.prompt` call-sites. For deck naming it doubles as a prompt (controlled input inside the modal).
- **Scroll-to-top on page change:** `CardTable` scrolls the table container (or `window`) to the top whenever `currentPage` changes.
- **Keyboard navigation in `CardTable`:** The table body becomes keyboard-focusable; `ArrowUp`/`ArrowDown` move focus between rows; `Enter` fires `onRowClick` for the focused row.

## Capabilities

### New Capabilities

- *(none — all changes are within existing capabilities)*

### Modified Capabilities

- **web-dashboard-ui:** `Filters` gains a color toggle bar; `CardTable` gains scroll-to-top on page change and keyboard row navigation; `CardDetailModal`, `DeckDetailModal`, and `DeckBuilder` replace native dialogs with `ConfirmModal`.

## Impact

- **Frontend only.** No backend or DB changes required.
- Files touched: `Filters.tsx`, `CardTable.tsx`, `CardDetailModal.tsx`, `DeckDetailModal.tsx`, `DeckBuilder.tsx` (page). New file: `ConfirmModal.tsx`.
- No new npm dependencies; color symbols rendered as styled text/emoji or existing Tailwind classes (same approach as rarity badges).
