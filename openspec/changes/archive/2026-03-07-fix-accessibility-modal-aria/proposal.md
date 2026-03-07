# Proposal: Fix Remaining Accessibility Issues

## What

Three targeted accessibility gaps remain in the frontend after the initial accessible-modals
implementation:

1. **ConfirmModal does not use AccessibleModal** — it is the last modal in the application that
   rolls its own dialog semantics (focus trap, ESC handler, scroll-lock). It duplicates logic
   already centralised in `AccessibleModal` and is missing body scroll-lock entirely.

2. **No `aria-live` regions anywhere in the codebase** — dynamic content updates (job progress,
   status changes, result counts) are invisible to screen readers. When a job completes or a
   filter produces a new card count, assistive technology receives no announcement.

3. **DeckCardPickerModal search input has no label** — the search `<input>` at line 115 of
   `DeckCardPickerModal.tsx` is identified only by its `placeholder` attribute. Placeholder text
   is not a substitute for a label: it disappears when the user types and is announced
   inconsistently across screen reader / browser combinations.

   Additionally, the `ConfirmModal` prompt `<label>` (line 90) has no `htmlFor`/`id` pair, so
   it is not programmatically associated with its `<input>`.

## Why

The `accessible-modals` spec (section "All modals use AccessibleModal") explicitly requires every
modal to use `AccessibleModal`. `ConfirmModal` is called from three places
(`CardDetailModal`, `DeckDetailModal`, `DeckBuilder`) and is the last non-compliant modal.

The `web-dashboard-ui` spec (section "Form label/input associations") requires all `<label>`
elements to be associated via `htmlFor`/`id`. Both the picker search input and the confirm prompt
input violate this today.

`aria-live` regions are a foundational screen-reader primitive. The jobs bar and filter result
count are the two highest-traffic dynamic regions — these are the surfaces users interact with
most frequently and are currently completely silent to assistive technology.

## Scope

Frontend only. No backend changes. No new API endpoints. No migration. No new npm packages.

Files changed:
- `frontend/src/components/ConfirmModal.tsx` — refactor to use `AccessibleModal`
- `frontend/src/components/DeckCardPickerModal.tsx` — add `aria-label` to search input
- `frontend/src/components/JobsBottomBar.tsx` — add `aria-live` status region
- `frontend/src/locales/en.json` — add i18n key for search input label
- `frontend/src/locales/es.json` — add i18n key for search input label

## Success Criteria

- `ConfirmModal` renders `AccessibleModal` as its outermost wrapper; all manual focus/ESC/scroll
  logic is removed from `ConfirmModal` itself.
- The prompt `<label>` inside `ConfirmModal` has a matching `htmlFor`/`id` on the `<input>`.
- `DeckCardPickerModal` search `<input>` has an `aria-label` (or visible `<label>` with matching
  `id`).
- `JobsBottomBar` contains at least one `aria-live="polite"` region that announces job status
  changes and completion to screen readers.
- No existing visual behaviour or keyboard behaviour regresses: ESC closes, overlay click closes,
  focus is trapped, focus is restored on close, confirmations still fire correctly.
- All i18n strings for new labels are present in both `en.json` and `es.json`.
