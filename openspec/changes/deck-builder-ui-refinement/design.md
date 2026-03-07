## Change Summary

This change hardens three specific areas of the deck builder UI that were functionally implemented but lacked explicit verification and test coverage: (1) commander card image background rendering on deck tiles, (2) mana curve chart axis label readability in dark mode, and (3) deck import `//Commander` section header round-trip correctness. The implementation is almost entirely frontend-focused; the only backend-adjacent work is augmenting existing parser unit tests.

## Impact Analysis

### Layers Affected

**Frontend (`frontend/src/`)**
- `pages/DeckBuilder.tsx` — `DeckCardButton` component: `useCardImage` hook result drives the background image style and dark overlay; verify the image URL is non-null and the `bg-black/55` overlay renders over it correctly
- `components/DeckDetailModal.tsx` — `BarChart` > `XAxis` `tick` prop uses `fill: 'currentColor'`; the parent wrapper has `dark:text-gray-200` which must propagate into SVG `currentColor`; verify this chain works; if not, fix with explicit `fill` value in dark mode

**Tests (`tests/`)**
- `tests/test_deck_text_parser.py` — already has 13 unit tests covering Commander section header; review for any missing edge cases (e.g., `// Commander` with internal space variants, Windows CRLF line endings)
- New test additions for any gaps found

**No backend changes.** `deckdex/importers/deck_text.py` is complete and tested. No API endpoints change.

## Implementation Design

### 1. Commander Card Image Background (`DeckBuilder.tsx` — `DeckCardButton`)

**Current implementation (lines 9–51):**
```
useCardImage(deck.commander_card_id ?? null)
```
The hook returns `{ src: commanderImageUrl }`. When `commanderImageUrl` is a non-null string, the component renders:
- An absolutely-positioned inner `div` with `bg-cover bg-top bg-no-repeat` and `backgroundImage: url(...)` — covers the full tile
- A second `div` with `bg-black/55` dark overlay
- Text labels with `text-white drop-shadow-[...]` when image is present

**Analysis:** This implementation is correct and complete. The design covers all spec requirements:
- Image-as-background with top alignment: `bg-top`
- Uniform dark overlay: `bg-black/55`
- Readable text: white text + drop shadow
- No-commander fallback: `bg-gray-200 dark:bg-gray-700` on the outer button when `commanderImageUrl` is falsy

**Verification task:** The acceptance criterion is a Vitest + React Testing Library test that renders `DeckCardButton` with a mock `useCardImage` returning a URL, asserts the background-image style is applied, and asserts the overlay div is present. A second test renders with `commanderImageUrl === null` and asserts the overlay is absent.

**Edge cases to test:**
- `commander_card_id` is `null` (no commander assigned) → no background image, neutral tile
- `useCardImage` returns `{ src: null }` (image fetch failed) → same as no commander
- `useCardImage` returns a valid blob URL → background image renders with overlay

### 2. Mana Curve Dark Mode Axis Label Visibility (`DeckDetailModal.tsx`)

**Current implementation (lines 302–337):**
The outer wrapper div has class `dark:text-gray-200` which sets `color` in CSS. The `XAxis` tick uses `fill: 'currentColor'` — SVG `fill` inherits from CSS `color`. This is the correct pattern for SVG text color in Recharts.

**Why `currentColor` works here:** Recharts renders `XAxis` tick labels as SVG `<text>` elements. When `fill` is set to `currentColor`, the SVG text color resolves from the nearest ancestor's CSS `color` property. The parent div carries `dark:text-gray-200` (light gray in dark mode), so in dark mode the ticks will be light gray and readable.

**Potential failure point:** If the chart container (`ResponsiveContainer`) is rendered inside an SVG context that doesn't inherit from the parent `div`, `currentColor` may fall back to the SVG default (`black`). The `className` on the parent `div` (line 303) is `deck-detail-mana-curve flex items-center gap-1.5 flex-1 min-w-[140px] h-8 shrink-0 text-gray-600 dark:text-gray-200`. Recharts `ResponsiveContainer` renders a `div` then an SVG inside it — the CSS `color` on the outer div flows through to the SVG `currentColor`. This is a supported pattern.

**Verification approach:** Write a Vitest test with `@testing-library/react` that renders `DeckDetailModal` in a mock dark-mode context (set `document.documentElement.classList.add('dark')`), renders the mana curve, and asserts that XAxis tick elements have `fill="currentColor"` (they always will since that's the prop) AND that the parent div has the `dark:text-gray-200` class. The actual color resolution is a CSS concern that requires a browser to evaluate; we validate the structural correctness, not pixel color.

**If a fix is needed:** Replace `fill: 'currentColor'` with a conditional: pass a `tickColor` prop computed from `isDark ? '#e5e7eb' : '#4b5563'` using the `ThemeContext`. The `ThemeContext` at `frontend/src/contexts/ThemeContext.tsx` exposes the current theme. This is the fallback if `currentColor` inheritance proves unreliable.

### 3. Deck Import Commander Section Header Round-Trip (`DeckImportModal.tsx`)

**Current implementation:**
- `DeckImportModal` takes pasted text and calls `api.importDeckText(deckId, deckText)` via `useMutation`
- The backend endpoint (`POST /api/decks/{id}/import`) calls `parse_deck_text` from `deckdex/importers/deck_text.py`, then matches names against the collection and calls `DeckRepository.add_cards_batch`
- `parse_deck_text` correctly sets `is_commander: True` for cards under a `//Commander` header (verified in 13 existing unit tests in `tests/test_deck_text_parser.py`)

**Gap:** No integration test exercises the full round-trip: paste text with `//Commander` → submit → deck shows card in Commander section. The existing tests are unit tests of the parser only.

**Verification approach:** Add a test to `tests/test_decks.py` using the existing `deck_client` fixture pattern (which mocks `require_deck_repo` and `get_current_user_id`). The test calls `POST /api/decks/{id}/import` with a body containing `//Commander\n1 Atraxa, Praetors' Voice`, mocks the repository's `import_text` method to capture the parsed cards, and asserts that the captured call included `is_commander=True` for the Atraxa entry.

**Existing parser edge cases — review `test_deck_text_parser.py`:**
All 13 tests pass as written. The following edge cases are already covered:
- `//Commander` (exact) → `is_commander: True`
- `//COMMANDER` (uppercase) → `is_commander: True` (case-insensitive regex)
- `//Commander` followed by `//Sideboard` → resets `is_commander` to `False`
- `// This is a comment` (non-Commander header) → skipped, `is_commander` stays `False`
- Windows CRLF: `splitlines()` in Python handles `\r\n` correctly — no additional test needed
- `// Commander` (space after `//`): the regex is `^//\s*commander\s*$` which matches this — covered

**One gap found:** No test for `//Commander ` with trailing whitespace after `Commander`. The regex `^//\s*commander\s*$` (with `\s*` at end) handles this — but an explicit test is good for documentation.

## Architectural Decisions

### Decision: Use `currentColor` for mana curve ticks rather than ThemeContext

`currentColor` is the simpler approach and consistent with how SVG inherits from CSS. It requires no React state and no `ThemeContext` import in `DeckDetailModal`. The fallback to explicit ThemeContext-driven color is only needed if browser testing confirms `currentColor` fails to resolve correctly. We document both approaches and implement the fix only if the verification test reveals a structural problem.

### Decision: Frontend component tests with Vitest + RTL, not Playwright e2e

The remaining gaps are component-level concerns (overlay presence, class inheritance, import mock). Playwright e2e would require a running backend + database. Vitest + React Testing Library with mocked API calls is the correct tool for verifying component rendering behavior in isolation, matching the existing test infrastructure pattern.

### Decision: Add integration test in `tests/test_decks.py` for import Commander path

The existing `test_deck_text_parser.py` covers parser logic thoroughly. The missing test is at the API route level: that the route correctly passes `is_commander` from parsed results to the repository. This belongs in `tests/test_decks.py` alongside the other deck API integration tests, using the same `deck_client` fixture.

## Risks and Edge Cases

- **`useCardImage` async behavior in tests:** The hook uses blob URLs from an async image fetch. RTL tests must mock `useCardImage` at the module level (via `vi.mock`) to return a synchronous value. Pattern: `vi.mock('../hooks/useCardImage', () => ({ useCardImage: () => ({ src: 'blob:test-url' }) }))`
- **Dark mode CSS in jsdom:** jsdom does not execute Tailwind CSS. Tests verifying dark mode cannot assert computed color; they must assert structural correctness (presence of `dark:text-gray-200` class, `fill="currentColor"` prop) and leave color resolution to manual/browser verification.
- **Import test fixture scope:** Per project conventions, all pytest fixtures with MagicMock must use `scope="function"` to avoid cross-test pollution.
- **`parse_deck_text` trailing-whitespace edge case:** The regex `\s*` already handles this; the test is documentation-only, not a bug fix.
