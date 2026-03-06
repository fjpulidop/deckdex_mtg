# Accessibility Exploration - DeckDex MTG Frontend

Date: 2026-03-06
Status: Complete exploration, no code changes

## Executive Summary

The DeckDex frontend has a **mixed accessibility posture**. A few components (ConfirmModal, CardFormModal combobox, Filters color toggles, CardTable keyboard navigation) show genuine ARIA awareness. However, the majority of modals lack `role="dialog"` and focus traps, most form inputs lack associated labels, error messages are not announced to screen readers, and there are zero `aria-live` regions in the entire codebase. The issues below are ranked by impact and effort to fix.

---

## What Is Already Done Well

These patterns should be preserved and used as templates:

1. **ConfirmModal** -- the gold standard modal in this codebase:
   - `role="dialog"`, `aria-modal="true"`, `aria-labelledby="confirm-modal-title"`
   - Auto-focuses confirm button or prompt input on open
   - Escape key to close
   - Overlay click to close

2. **CardFormModal combobox** -- proper ARIA combobox pattern:
   - `role="combobox"`, `aria-expanded`, `aria-autocomplete="list"`, `aria-controls`
   - `aria-activedescendant` tracks highlighted suggestion
   - Suggestion list has `role="listbox"`, items have `role="option"` + `aria-selected`
   - Full keyboard navigation (ArrowUp/Down, Enter, Escape)

3. **Filters color toggles** -- `aria-pressed` on each color button

4. **CardTable** -- keyboard navigation with Arrow keys, Enter to select, focus ring on rows, `tabIndex={0}` on rows

5. **ThemeToggle** -- proper `aria-label` with context-aware text

6. **Navbar mobile menu** -- `aria-label="Toggle mobile menu"`, `aria-expanded` on toggle button, Escape to close

7. **CardDetailModal** -- `role="alert"` on save error message, `aria-label` on close button, `aria-hidden` on decorative skeleton loaders

---

## Critical Findings (High Priority)

### C1. Most modals missing `role="dialog"`, `aria-modal`, `aria-labelledby`

**Components affected:**
- CardFormModal
- CardDetailModal
- SettingsModal
- ProfileModal
- DeckDetailModal
- DeckCardPickerModal
- DeckImportModal
- ImportListModal
- JobLogModal
- LandingNavbar GitHub modal

Only ConfirmModal has these attributes. All other modals are just `<div>` overlays with no dialog semantics.

**Impact: HIGH** -- Screen reader users cannot identify these as dialogs, cannot navigate to/from them properly.
**Effort: LOW** -- Add 3 attributes to the outer overlay div + an `id` on the heading element. Pattern already established in ConfirmModal.

### C2. No focus trap in any modal

No modal traps focus within itself. When a modal is open, Tab key can move focus to elements behind the modal overlay. This affects all 10+ modals.

**Impact: HIGH** -- Keyboard-only users can interact with hidden content behind modals.
**Effort: MEDIUM** -- Need a reusable focus trap utility (e.g., `useFocusTrap` hook or use a library like `@headlessui/react` Dialog). Apply to all modals.

### C3. Zero `aria-live` regions in the entire codebase

No dynamic content updates are announced to screen readers:
- Job progress updates (percentage, completion)
- Error messages appearing after form submissions
- Success messages (import complete, card saved, price updated)
- Loading states transitioning to results
- Filter result count changes
- Insight results appearing

**Impact: HIGH** -- Screen reader users are completely unaware of asynchronous updates.
**Effort: MEDIUM** -- Add `aria-live="polite"` to error containers, success messages, job progress. Add `aria-live="assertive"` for critical errors. Consider a toast/notification system with live regions.

### C4. Error messages not announced (missing `role="alert"`)

Only one component (CardDetailModal save error) uses `role="alert"`. All other error displays are just styled divs:

- CardFormModal error div (line 215)
- SettingsModal error div (line 113)
- ProfileModal error and nameError
- DeckImportModal mutation error
- ImportListModal error
- Import page error
- DeckBuilder createError
- Dashboard error state

**Impact: HIGH** -- Screen reader users do not know when form submissions fail.
**Effort: LOW** -- Add `role="alert"` to all error message containers.

---

## Major Findings (Medium Priority)

### M1. Form inputs missing label associations

Most `<label>` elements use visual proximity but lack `htmlFor`/`id` associations:

**Properly associated (2 instances):**
- DeckCardPickerModal: `htmlFor="picker-type"`, `htmlFor="picker-sort"`

**Missing associations (all other form fields):**
- CardFormModal: name, type, rarity, price, set fields -- labels exist but no `htmlFor`/`id`
- CardDetailModal edit form: 10 fields -- labels exist but no `htmlFor`/`id`
- ConfirmModal prompt input -- label exists but no `htmlFor`/`id`
- ProfileModal display name -- label exists but no `htmlFor`/`id`
- SettingsModal textarea -- no label at all (just placeholder)
- Filters: search input, price min/max -- no labels (placeholder only)
- Filters: rarity/type/set selects -- no labels at all

**Impact: MEDIUM** -- Screen readers may not associate labels with inputs. Click-on-label-to-focus also broken.
**Effort: LOW** -- Add `id` to inputs, `htmlFor` to labels. ~30 instances.

### M2. Interactive elements lacking accessible names

- LanguageSwitcher -- wraps language names in `<span>` elements inside a `<button>` but has only `title` (from i18n), no `aria-label`
- DeckDetailModal export/import/add/delete buttons -- text only, which is fine, but the deck name inline edit button uses deck name text as its accessible name which is ambiguous
- SettingsModal close button (X icon) -- no `aria-label`
- ProfileModal close button (X icon) -- no `aria-label`
- ProfileModal avatar upload button -- no `aria-label` describing what clicking does
- LandingNavbar mobile menu button -- no `aria-label`
- LandingNavbar GitHub modal close button -- no `aria-label`
- JobsBottomBar pill toggle -- no `aria-label` or `aria-expanded`
- ActiveJobs cancel/view-log buttons -- text-only (OK for sighted), but cancel button text "Stop" is generic
- DeckDetailModal card remove button -- has good `aria-label={`Remove ${card.name}`}` (well done)

**Impact: MEDIUM** -- Icon-only buttons are inaccessible. Text buttons are mostly OK.
**Effort: LOW** -- Add `aria-label` to icon-only buttons (~10 instances).

### M3. Sortable table headers using `<th>` with `onClick` but no keyboard support

CardTable headers are sortable via click, but:
- No `role="button"` or `tabIndex={0}` on `<th>` elements
- No keyboard handler (Enter/Space to sort)
- No `aria-sort` attribute indicating current sort direction
- Sort direction indicated only by Unicode arrows (up/down)

**Impact: MEDIUM** -- Keyboard users cannot sort the table. Screen readers don't know sort state.
**Effort: LOW** -- Add `tabIndex={0}`, `onKeyDown`, `role="columnheader"` with `aria-sort`.

### M4. QuantityCell in CardTable -- click-to-edit with no keyboard trigger

The quantity value is a `<span>` with `onClick` to enter edit mode. No keyboard way to activate it.

**Impact: MEDIUM** -- Keyboard users cannot edit card quantities.
**Effort: LOW** -- Add `tabIndex={0}`, `role="button"`, `onKeyDown` for Enter/Space.

### M5. ActionButtons hardcoded English text

ActionButtons component has hardcoded strings: "Process Cards", "Starting...", "Update Prices", "New added cards (with only the name)", "All cards", "Actions". These bypass the i18n system.

**Impact: MEDIUM** -- Not an a11y issue per se, but affects non-English screen reader users.
**Effort: LOW** -- Replace with `t()` calls.

---

## Minor Findings (Lower Priority)

### L1. Lightbox overlays use `role="button"` on the backdrop

CardDetailModal and DeckDetailModal lightbox overlays use `role="button"` + `tabIndex={0}` on the full-screen backdrop div. This is semantically incorrect -- a dismiss overlay is not a button. Should use a proper dialog pattern instead, or at minimum `role="presentation"`.

**Impact: LOW** -- Screen readers announce the backdrop as "button", confusing.
**Effort: LOW** -- Change to proper pattern.

### L2. Color contrast concerns in dark mode

Several Tailwind classes use opacity-based colors that may fail WCAG AA contrast:
- `text-gray-400 dark:text-gray-500` -- gray-500 on gray-800 background is approximately 3.5:1 (fails AA for normal text)
- `text-slate-400` on dark backgrounds in landing page
- `text-gray-500 dark:text-gray-400` for secondary text -- borderline at 4.4:1
- Disabled button states use `opacity-50` which reduces all contrast by half
- Filter chip remove buttons use `text-blue-800 dark:text-blue-200` which is likely fine

**Impact: MEDIUM** (affects all low-vision users) -- But effort to audit every color combination is HIGH.
**Effort: HIGH** -- Needs systematic audit with contrast checker. Could start with just `text-gray-500` on dark backgrounds.

### L3. Loading spinners have no text alternative

Multiple components use CSS-animated spinners (border-based) with no accessible text:
- Login page spinner
- Import page resolve/progress spinners
- CollectionInsights executing spinner
- DeckCardPickerModal "loading" text is present (good)

Some have adjacent text (good), some don't.

**Impact: LOW** -- Most spinners have nearby text. A few don't.
**Effort: LOW** -- Add `aria-label="Loading"` or sr-only text.

### L4. Import page step indicator not accessible

The step indicator (circles 1-6) conveys progress visually but has no textual/ARIA representation:
- No `aria-current="step"` on current step
- No `role="progressbar"` or equivalent
- Step labels not visible (just numbers)

**Impact: LOW** -- Sighted users can see progress; screen reader users get nothing.
**Effort: LOW** -- Add sr-only step labels and `aria-current`.

### L5. Landing page motion/animation has no reduced-motion support

Framer Motion animations (Hero, BentoGrid, FinalCTA) don't respect `prefers-reduced-motion`. Users with motion sensitivity or vestibular disorders may be affected.

**Impact: LOW** -- Landing page is not the core app experience.
**Effort: LOW** -- Framer Motion supports `useReducedMotion()` hook.

### L6. Tab-like interfaces missing `role="tablist"`

ImportListModal and Import page have file/text toggle buttons that act as tabs, but:
- No `role="tablist"` on container
- No `role="tab"` on buttons
- No `role="tabpanel"` on content
- No `aria-selected` on active tab

Same for JobsBottomBar active/history tabs.

**Impact: LOW** -- These work as buttons but semantics are incorrect for screen readers.
**Effort: LOW** -- Add tab ARIA roles.

### L7. Charts are not accessible

All Recharts-based visualizations (Analytics page, DeckDetailModal mana curve) have no text alternatives:
- No `role="img"` with `aria-label` describing the chart
- No data table fallback
- Click-to-filter on chart elements has no keyboard equivalent

**Impact: MEDIUM** for analytics-focused users, but **LOW** overall since charts are supplementary.
**Effort: HIGH** -- Would need hidden data tables or aria descriptions for each chart.

### L8. Dropdown menus lack `role="menu"` semantics

Navbar user menu dropdown, ActionButtons process scope dropdown:
- No `role="menu"` on container
- No `role="menuitem"` on items
- No arrow key navigation within menu
- Navbar user menu does have Escape-to-close (good)

**Impact: LOW** -- These work as click targets, but navigation within is mouse-only.
**Effort: MEDIUM** -- Need keyboard nav within menus.

---

## Prioritized Improvement Roadmap

### Tier 1: Quick Wins (1-2 hours total, massive impact)

| # | Fix | Impact | Effort | Components |
|---|-----|--------|--------|------------|
| 1 | Add `role="dialog"`, `aria-modal`, `aria-labelledby` to all modals | HIGH | LOW | 10 modals |
| 2 | Add `role="alert"` to all error message containers | HIGH | LOW | ~10 components |
| 3 | Add `aria-label` to all icon-only buttons (close X, etc.) | MEDIUM | LOW | ~10 buttons |
| 4 | Add `htmlFor`/`id` to all label/input pairs | MEDIUM | LOW | ~30 fields |
| 5 | Add `aria-sort` + keyboard support to CardTable headers | MEDIUM | LOW | 1 component |

### Tier 2: Moderate Effort (half day, significant impact)

| # | Fix | Impact | Effort | Notes |
|---|-----|--------|--------|-------|
| 6 | Add `aria-live` regions for dynamic content | HIGH | MEDIUM | Jobs, errors, results, filter counts |
| 7 | Focus trap for all modals | HIGH | MEDIUM | Reusable hook or library |
| 8 | Keyboard support for QuantityCell | MEDIUM | LOW | Add role="button", onKeyDown |
| 9 | Tab semantics for toggle interfaces | LOW | LOW | ImportListModal, JobsBottomBar |
| 10 | Step indicator accessibility | LOW | LOW | Import page |

### Tier 3: Longer-term Improvements

| # | Fix | Impact | Effort | Notes |
|---|-----|--------|--------|-------|
| 11 | Reduced-motion support | LOW | LOW | Framer Motion hook |
| 12 | Color contrast audit | MEDIUM | HIGH | Full systematic review needed |
| 13 | Chart accessibility | MEDIUM | HIGH | Data tables, aria descriptions |
| 14 | Menu keyboard navigation | LOW | MEDIUM | Arrow keys in dropdowns |

---

## Architectural Recommendation

Consider creating a reusable `<Modal>` wrapper component that encapsulates:
- `role="dialog"` + `aria-modal="true"` + `aria-labelledby`
- Focus trap (trap Tab within modal)
- Escape key to close
- Auto-focus first focusable element
- Restore focus to trigger element on close
- Overlay click to close

This would replace the repeated `<div className="fixed inset-0 bg-black/50 ...">` pattern used in 10+ modals, making all of them accessible with zero per-modal effort.

Similarly, a reusable `<Alert>` component with `role="alert"` + `aria-live="assertive"` could replace all the ad-hoc error display divs.

---

## Files Reviewed

### Components (37 files)
- `components/Navbar.tsx` -- ESC support, aria-label on user menu, aria-expanded on mobile toggle
- `components/CardFormModal.tsx` -- Excellent combobox ARIA, missing dialog role
- `components/ConfirmModal.tsx` -- Gold standard: dialog role, auto-focus, ESC
- `components/CardDetailModal.tsx` -- role="alert" on error, missing dialog role
- `components/Filters.tsx` -- aria-pressed on colors, missing label associations
- `components/CardTable.tsx` -- Keyboard nav, missing sortable header a11y
- `components/SettingsModal.tsx` -- role="switch" on toggle (good), missing dialog role, missing X aria-label
- `components/CollectionInsights.tsx` -- Missing combobox ARIA on search input
- `components/DeckDetailModal.tsx` -- aria-label on some buttons, missing dialog role
- `components/DeckCardPickerModal.tsx` -- htmlFor on 2 selects (good), missing dialog role
- `components/DeckImportModal.tsx` -- Missing dialog role
- `components/ImportListModal.tsx` -- Missing dialog role
- `components/JobLogModal.tsx` -- Missing dialog role
- `components/JobsBottomBar.tsx` -- Missing aria-expanded on toggle
- `components/ActiveJobs.tsx` -- No ARIA issues (uses text buttons)
- `components/ThemeToggle.tsx` -- Good: aria-label
- `components/LanguageSwitcher.tsx` -- title only, no aria-label
- `components/ProfileModal.tsx` -- Missing dialog role, missing aria-labels
- `components/ActionButtons.tsx` -- Hardcoded English strings
- `components/landing/Hero.tsx` -- Decorative, minor issues
- `components/landing/BentoGrid.tsx` -- Decorative, minor issues
- `components/landing/BentoCard.tsx` -- Decorative
- `components/landing/FinalCTA.tsx` -- Decorative
- `components/landing/Footer.tsx` -- Social links missing aria-labels
- `components/landing/LandingNavbar.tsx` -- Missing mobile menu aria-label, GitHub modal missing dialog role
- `components/analytics/ChartCard.tsx` -- No chart a11y
- `components/insights/InsightResponse.tsx` -- Structural component, no issues

### Pages (7 files)
- `pages/Dashboard.tsx` -- Orchestrator, no direct a11y issues
- `pages/DeckBuilder.tsx` -- Good: aria-label on add deck button
- `pages/Analytics.tsx` -- Chart a11y gaps
- `pages/Import.tsx` -- Step indicator not accessible, AutocompleteInput missing ARIA
- `pages/Landing.tsx` -- Wrapper, no issues
- `pages/Login.tsx` -- No dark mode styles (minor), otherwise OK
- `App.tsx` -- Routing, no issues
