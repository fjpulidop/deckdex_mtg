# Tasks: Deck Builder UI Refinement

Ordered, atomic tasks. All tasks are frontend-only or test-only. No backend API or database changes are required.

---

## Task 1 — Verify commander image background rendering in `DeckCardButton`

**Layer:** Frontend
**Files:** `frontend/src/pages/DeckBuilder.tsx`

**Description:**
Read `DeckCardButton` (lines 9–51 of `DeckBuilder.tsx`). Confirm the following are correct as-implemented:
1. The outer `<button>` has `bg-gray-200 dark:bg-gray-700` as its base background.
2. When `commanderImageUrl` is truthy, the inner absolutely-positioned `div` renders with `bg-cover bg-top bg-no-repeat` and `backgroundImage: url(${commanderImageUrl})`.
3. A second inner `div` with `bg-black/55 pointer-events-none` renders as the dark overlay directly after the image div.
4. Text spans carry `text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]` when `commanderImageUrl` is truthy.
5. When `commanderImageUrl` is falsy, no image div and no overlay div render.

If any of these conditions are violated, fix the JSX to match them. If all conditions are met, no code change is needed — the task outcome is the verification itself, documented in the test task below.

**Acceptance criteria:**
- [x] `DeckCardButton` renders the overlay div only when `commanderImageUrl` is a non-empty string
- [x] `DeckCardButton` uses the neutral background when `commanderImageUrl` is null/undefined
- [x] Text is white with drop-shadow when image is present, theme-colored otherwise

---

## Task 2 — Verify mana curve dark mode tick color in `DeckDetailModal`

**Layer:** Frontend
**Files:** `frontend/src/components/DeckDetailModal.tsx`

**Description:**
Read `DeckDetailModal.tsx` lines 302–337. Confirm:
1. The parent wrapper `div` (line 303) carries `dark:text-gray-200` in its className.
2. The `XAxis` component carries `tick={{ fontSize: 9, fill: 'currentColor' }}`.
3. No intermediate element between the parent `div` and `BarChart` resets the CSS `color` property.

`fill: 'currentColor'` in an SVG `<text>` element resolves from the nearest ancestor's CSS `color` property. Tailwind's `dark:text-gray-200` sets `color: #e5e7eb` in dark mode on the parent div, so the SVG tick labels will be light gray. This chain is correct as implemented.

If an intermediate element is found that resets the `color` (e.g., an explicit `text-gray-900`), remove or scope it so the dark mode class propagates.

**If `currentColor` is confirmed not resolving correctly** (visible in manual testing), apply this fix:
- Import `useContext` and `ThemeContext` from `../contexts/ThemeContext`
- Add `const { theme } = useContext(ThemeContext)` near the top of `DeckDetailModal`
- Change the `XAxis` tick prop to `tick={{ fontSize: 9, fill: theme === 'dark' ? '#e5e7eb' : '#4b5563' }}`

**Acceptance criteria:**
- [x] In dark mode, `XAxis` tick labels are light-colored (either via `currentColor` resolving from `dark:text-gray-200`, or via explicit hex value from ThemeContext)
- [x] In light mode, `XAxis` tick labels are dark-colored and readable
- [x] No visual regression in the mana curve chart layout

---

## Task 3 — Add `//Commander` trailing-whitespace edge case test to `test_deck_text_parser.py`

**Layer:** Tests
**Files:** `tests/test_deck_text_parser.py`

**Description:**
The existing `tests/test_deck_text_parser.py` has 13 unit tests. Review the Commander section header parsing tests. Add one test that explicitly documents the trailing-whitespace behavior:

```python
def test_parse_commander_header_trailing_whitespace():
    """//Commander with trailing spaces is still recognized as commander section."""
    text = "//Commander   \n1 Atraxa, Praetors' Voice"
    result = parse_deck_text(text)
    assert len(result) == 1
    assert result[0]["is_commander"] is True
```

The regex `^//\s*commander\s*$` (with `re.IGNORECASE`) already handles this — the test documents the behavior.

Also add one test for `// Commander` (space between `//` and `Commander`) to document that `\s*` after `//` handles internal spaces:

```python
def test_parse_commander_header_internal_space():
    """// Commander (space after //) is recognized as commander section."""
    text = "// Commander\n1 Sol Ring"
    result = parse_deck_text(text)
    assert len(result) == 1
    assert result[0]["is_commander"] is True
```

**Note:** Use `scope="function"` if any fixture is added (project convention). These tests use no fixtures.

**Acceptance criteria:**
- [x] Two new test functions added to `tests/test_deck_text_parser.py`
- [x] Both tests pass with `pytest tests/test_deck_text_parser.py`
- [x] Total test count in the file rises from 13 to 15

---

## Task 4 — Add deck import Commander section API integration test to `tests/test_decks.py`

**Layer:** Tests
**Files:** `tests/test_decks.py`

**Description:**
Add an integration test for `POST /api/decks/{id}/import` that verifies cards under `//Commander` are passed to the repository with `is_commander=True`. Use the existing `deck_client` fixture (which is module-scoped — but per project convention add new test fixtures with `scope="function"`).

Pattern to follow (from existing tests in `test_decks.py`):
- Use `deck_client` fixture to get the test client
- Mock `require_deck_repo` to return a `MagicMock` repository
- Call the import endpoint with a body containing `//Commander\n1 Atraxa, Praetors' Voice\n//Mainboard\n4 Lightning Bolt`
- The repository mock's `import_text` method (or `add_cards_batch` depending on how the route implements import) will capture the call arguments
- Assert that the Atraxa entry has `is_commander=True` and Lightning Bolt has `is_commander=False`

**Read `backend/api/routes/decks.py` first** to see exactly which repository method the import route calls and what arguments it passes, then write the assertion to match.

**Acceptance criteria:**
- [x] New test `test_import_deck_commander_section` added to `tests/test_decks.py`
- [x] Test uses `scope="function"` on any new fixtures
- [x] Test asserts `is_commander=True` for cards under `//Commander`
- [x] Test asserts `is_commander=False` for cards under `//Mainboard`
- [x] `pytest tests/test_decks.py` passes with no failures

---

## Task 5 — Add Vitest component test for `DeckCardButton` commander image rendering

**Layer:** Frontend (tests)
**Files:** `frontend/src/pages/DeckBuilder.test.tsx` (new file)

**Description:**
Create `frontend/src/pages/DeckBuilder.test.tsx` with Vitest + React Testing Library tests for the `DeckCardButton` component.

**Setup:** Mock `useCardImage` hook and `useTranslation` at module level. The `DeckCardButton` is not exported from `DeckBuilder.tsx` — it is a file-internal component. Options:
1. Export `DeckCardButton` from `DeckBuilder.tsx` (preferred — add `export function DeckCardButton`)
2. Test `DeckBuilder` page and find `DeckCardButton` via rendered output

Use option 1: add `export` keyword to `DeckCardButton` in `DeckBuilder.tsx`.

**Test cases:**

```typescript
// Mock at top of test file:
vi.mock('../hooks/useCardImage', () => ({
  useCardImage: vi.fn(),
}));

describe('DeckCardButton', () => {
  it('renders background image and overlay when commanderImageUrl is set', () => {
    (useCardImage as ReturnType<typeof vi.fn>).mockReturnValue({ src: 'blob:http://test/image' });
    const deck = { id: 1, name: 'Test Deck', card_count: 30, commander_card_id: 42 };
    render(<DeckCardButton deck={deck} onClick={() => {}} />);
    const bgDiv = document.querySelector('[style*="background-image"]');
    expect(bgDiv).not.toBeNull();
    const overlay = document.querySelector('.bg-black\\/55');
    expect(overlay).not.toBeNull();
  });

  it('renders neutral background and no overlay when commanderImageUrl is null', () => {
    (useCardImage as ReturnType<typeof vi.fn>).mockReturnValue({ src: null });
    const deck = { id: 2, name: 'No Commander', card_count: 0, commander_card_id: null };
    render(<DeckCardButton deck={deck} onClick={() => {}} />);
    const bgDiv = document.querySelector('[style*="background-image"]');
    expect(bgDiv).toBeNull();
    const overlay = document.querySelector('.bg-black\\/55');
    expect(overlay).toBeNull();
  });

  it('shows white text with drop-shadow when image is present', () => {
    (useCardImage as ReturnType<typeof vi.fn>).mockReturnValue({ src: 'blob:http://test/img' });
    const deck = { id: 3, name: 'Commander Deck', card_count: 10, commander_card_id: 5 };
    render(<DeckCardButton deck={deck} onClick={() => {}} />);
    const nameSpan = screen.getByText('Commander Deck');
    expect(nameSpan.className).toContain('text-white');
  });
});
```

**Acceptance criteria:**
- [x] `frontend/src/pages/DeckBuilder.test.tsx` created
- [x] `DeckCardButton` exported from `DeckBuilder.tsx`
- [x] Three tests pass: image present, image absent, white text when image present
- [x] `npm run test` (or `npx vitest run`) passes for this file

---

## Task 6 — Add Vitest component test for mana curve dark mode structural correctness in `DeckDetailModal`

**Layer:** Frontend (tests)
**Files:** `frontend/src/components/DeckDetailModal.test.tsx` (new file, or append to existing if one exists)

**Description:**
Create (or augment) a test file for `DeckDetailModal`. This test verifies the structural properties of the mana curve that enable dark mode readability, rather than pixel color (which requires a browser).

**Check first:** Run `Glob` for `DeckDetailModal.test.tsx` — if it exists, append to it.

**Test case:**

```typescript
describe('DeckDetailModal mana curve dark mode', () => {
  it('mana curve wrapper carries dark:text-gray-200 class for currentColor inheritance', () => {
    // Render the modal with a mocked deck that has cards
    // Assert the wrapper div has the expected class
    render(<DeckDetailModal deckId={1} onClose={() => {}} onDeleted={() => {}} />);
    // Wait for the deck to load (mock useQuery to return immediately)
    const curveWrapper = document.querySelector('.deck-detail-mana-curve');
    expect(curveWrapper).not.toBeNull();
    expect(curveWrapper?.className).toContain('dark:text-gray-200');
  });
});
```

The `deck-detail-mana-curve` className is already present on the wrapper div (line 303 of `DeckDetailModal.tsx`) — this test documents and protects the dark mode contract.

**Note on mocking:** `DeckDetailModal` calls `api.getDeck` via `useQuery`. Mock at the module level:
```typescript
vi.mock('../api/client', () => ({
  api: { getDeck: vi.fn().mockResolvedValue({ name: 'Test', cards: [] }) },
}));
```

**Acceptance criteria:**
- [x] Test file created (or test appended to existing file)
- [x] Test asserts `.deck-detail-mana-curve` div is present and carries `dark:text-gray-200`
- [x] Test passes with `npx vitest run`
- [x] No existing tests broken

---

## Execution Order

```
Task 3 → independent (parser unit tests, no deps)
Task 4 → independent (API integration test, no deps)
Task 1 → Task 5 (export DeckCardButton first, then test it)
Task 2 → Task 6 (verify/fix first, then write structural test)
```

Tasks 3 and 4 can be done in parallel with Tasks 1, 2, 5, 6. Tasks 5 and 6 must follow their respective code verification tasks (1 and 2) since the export and any fixes must exist before the tests can be written.
