# Accessibility Modals Exploration (2026-03-07)

## Context
Explored all modal components to assess remaining accessibility gaps after the AccessibleModal wrapper was implemented and adopted across the codebase.

## What Exists (Done Well)
- **AccessibleModal wrapper** (`frontend/src/components/AccessibleModal.tsx`) is well-implemented with:
  - `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
  - Full focus trap (Tab cycling within modal, handles dynamic content)
  - Escape key to close
  - Auto-focus first focusable element on open
  - Focus restoration to previous element on close
  - Body scroll-lock while open
  - Overlay click to close
  - Optional consistent close button with `aria-label`
- **All 9 spec-listed modals** now use AccessibleModal:
  - CardFormModal, CardDetailModal, SettingsModal, ProfileModal, DeckDetailModal, DeckCardPickerModal, DeckImportModal, ImportListModal, JobLogModal
- **Label associations** in modals are mostly good -- CardFormModal, CardDetailModal, DeckCardPickerModal, ProfileModal all use `htmlFor`/`id` pairs
- **role="alert"** on error messages is widely adopted (CardFormModal, ImportListModal, DeckImportModal, DeckDetailModal, CardDetailModal, ProfileModal, SettingsModal)
- **aria-sort** on CardTable sortable columns implemented
- **aria-pressed** on DeckCardPickerModal color filter buttons
- **role="switch"** with `aria-checked` on SettingsModal toggle

## Gaps Found

### GAP 1: ConfirmModal does NOT use AccessibleModal (HIGH)
- File: `frontend/src/components/ConfirmModal.tsx`
- Has its own inline `role="dialog"` / `aria-modal` / escape handling
- MISSING: focus trap (Tab can escape the modal)
- MISSING: focus restoration on close
- MISSING: body scroll-lock
- Has `aria-labelledby="confirm-modal-title"` but hardcoded ID (collision risk if two ConfirmModals)
- Label on prompt input lacks `htmlFor`/`id` association (line 90-102)
- The spec lists 9 modals to use AccessibleModal but does NOT list ConfirmModal -- likely an oversight since ConfirmModal predates the spec

### GAP 2: ProfileModal crop sub-modal does NOT use AccessibleModal (MEDIUM)
- File: `frontend/src/components/ProfileModal.tsx` lines 221-285
- Has inline `role="dialog"`, `aria-modal`, `aria-labelledby` -- correct semantics
- MISSING: focus trap (Tab can escape to parent modal or page)
- MISSING: focus restoration when crop sub-modal closes
- MISSING: body scroll-lock (parent modal already locks, but still incorrect pattern)
- Has its own Escape handler but uses `stopPropagation` to prevent parent from closing -- this pattern would need careful handling if refactored to AccessibleModal

### GAP 3: Zero aria-live regions in entire codebase (MEDIUM)
- No `aria-live="polite"` or `aria-live="assertive"` anywhere
- Dynamic content updates (loading states, result counts, success messages) are invisible to screen readers
- Key locations needing aria-live:
  - DeckCardPickerModal: search results count updates as user types
  - ImportListModal: "resolving..." status
  - SettingsModal: success messages after save (scryfallMessage, importFileResult)
  - Card count / filter results on Dashboard

### GAP 4: DeckCardPickerModal search input has no label (LOW-MEDIUM)
- Line 115-121: `<input type="text" placeholder=...>` with no `<label>` or `aria-label`
- Placeholder text is not a substitute for a label (disappears on input, not read by all screen readers)

### GAP 5: SettingsModal file inputs have no accessible labels (LOW)
- Line 126-131: Scryfall JSON file input -- no label
- Line 216-222: Import collection file input -- no label
- Both use `type="file"` with only `accept` and `className`

### GAP 6: ImportListModal textarea has no label (LOW)
- Line 100-106: textarea for pasting card list has `placeholder` but no `<label>` or `aria-label`

### GAP 7: No accessibility tests for AccessibleModal (LOW-MEDIUM)
- Zero tests for AccessibleModal component
- Zero tests verifying focus trap, Escape handling, or ARIA attributes
- Only a11y-related test: CardGallery.test.tsx checks `aria-label` on tiles
- Risk: regressions could silently break a11y without anyone noticing

### GAP 8: ThemeToggle and Navbar have hardcoded English aria-labels (LOW)
- `ThemeToggle.tsx`: `aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}` -- not using i18n
- `Navbar.tsx`: `aria-label="User menu"` and `aria-label="Toggle mobile menu"` -- not using i18n

## Improvement Ideas

| # | Idea | Value | Complexity | Impact/Effort |
|---|------|-------|------------|---------------|
| 1 | Refactor ConfirmModal to use AccessibleModal | High | Small | **HIGH** |
| 2 | Refactor ProfileModal crop sub-modal to use AccessibleModal | Medium | Medium | Medium |
| 3 | Add aria-live regions for dynamic content | Medium | Small | **HIGH** |
| 4 | Add aria-label to DeckCardPickerModal search input | Medium | Tiny | **HIGH** |
| 5 | Add labels to SettingsModal file inputs | Low | Tiny | Medium |
| 6 | Add label/aria-label to ImportListModal textarea | Low | Tiny | Medium |
| 7 | Write AccessibleModal unit tests (focus trap, ESC, ARIA) | Medium | Medium | Medium |
| 8 | Fix hardcoded English aria-labels in ThemeToggle/Navbar | Low | Tiny | Medium |

## Recommended Top Pick
**Idea #1: Refactor ConfirmModal to use AccessibleModal** -- it is the only modal in the entire app that still rolls its own dialog implementation. It is missing focus trap, focus restoration, and scroll-lock. The fix is small: replace the outer div with `<AccessibleModal>`, remove the duplicate Escape/overlay-click logic, add an `id` to the prompt input and `htmlFor` to its label. This also eliminates the hardcoded `confirm-modal-title` ID collision risk. Combined with Idea #4 (add `aria-label` to search input) and Idea #3 (add aria-live to a few key locations), these three together form a tight, high-impact, low-effort accessibility sprint.
