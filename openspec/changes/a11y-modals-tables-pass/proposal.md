# Proposal: Accessibility Pass — Modals and Tables

## What

A targeted accessibility sweep across the frontend to close the remaining WCAG 2.1 AA gaps
identified through direct codebase inspection. The previous change
(`2026-03-07-fix-accessibility-modal-aria`) delivered the `AccessibleModal` wrapper and migrated
all modals to use it. This pass addresses what that work did not cover:

1. **Missing `aria-label` on `DeckCardPickerModal` search input** — The i18n key
   `deckCardPicker.searchLabel` was added to both locale files as part of the previous change, but
   the `<input>` at `DeckCardPickerModal.tsx` line 113 was never updated to consume it. The input
   remains identified only by its placeholder.

2. **Crop sub-modal in `ProfileModal` is not an `AccessibleModal`** — The crop tool rendered
   inside `ProfileModal.tsx` (lines 217–281) is a raw `<div role="dialog">` with no focus trap,
   no body scroll-lock (the outer `AccessibleModal` is still mounted and owns the lock), and relies
   on a manually registered `document.addEventListener` for ESC. This is inconsistent with the
   accessible-modals spec which requires every dialog to use `AccessibleModal`.

3. **Image lightboxes in `CardDetailModal` and `DeckDetailModal` lack dialog semantics** — Both
   components render a full-screen overlay (fixed inset-0, z-[60]) as `role="button"` rather than
   `role="dialog"`. A lightbox is a dialog: it blocks page interaction, traps focus, and should be
   dismissed by Escape. Using `role="button"` means screen readers cannot identify it as a dialog,
   focus is not trapped, and body scroll remains unlocked while the lightbox is open.

4. **`DeckImportModal` textarea has no accessible label** — The textarea at `DeckImportModal.tsx`
   line 52 uses only a `placeholder` attribute. Placeholders disappear on input and are not a
   substitute for a label under WCAG 1.3.1 (Info and Relationships).

5. **`SettingsModal` file input for collection import has no accessible label** — The `<input
   type="file">` at `SettingsModal.tsx` line 216 has no `aria-label` and no associated `<label>`
   element. Screen readers may announce it only as "Choose file" with no context about what it is
   for.

## Why

These gaps represent concrete WCAG 2.1 AA failures:

- **WCAG 1.3.1 Info and Relationships** — form controls must be programmatically associated with
  labels (affects items 1, 4, 5).
- **WCAG 4.1.2 Name, Role, Value** — interactive UI components must have accessible names and
  correct roles (affects items 2, 3).
- **WCAG 2.1.1 Keyboard** — all functionality must be operable via keyboard. Lightboxes rendered
  as `role="button"` do not provide focus trapping (affects item 3).
- **WCAG 2.4.3 Focus Order** — dialogs must trap focus within themselves (affects items 2, 3).

The crop sub-modal and lightboxes are the most severe: they are visually modal (they block the
rest of the page) but are not programmatically modal, meaning keyboard users can Tab out of them
and screen reader users receive no announcement that a dialog is open.

## Scope

Frontend only. No backend changes. No migrations. No new npm packages.

Files changed:
- `frontend/src/components/DeckCardPickerModal.tsx` — add `aria-label` to search input
- `frontend/src/components/ProfileModal.tsx` — replace crop sub-modal with `AccessibleModal`
- `frontend/src/components/CardDetailModal.tsx` — replace image lightbox with `AccessibleModal`
- `frontend/src/components/DeckDetailModal.tsx` — replace image lightbox with `AccessibleModal`
- `frontend/src/components/DeckImportModal.tsx` — add visible or screen-reader label to textarea
- `frontend/src/components/SettingsModal.tsx` — add accessible label to collection import file input
- `frontend/src/locales/en.json` — add i18n keys for new labels
- `frontend/src/locales/es.json` — add i18n keys for new labels

## What is Confirmed Already Done

The following were targets in the previous a11y pass and are already correct in the code:

- All modals (`CardFormModal`, `ConfirmModal`, `DeckDetailModal`, `CardDetailModal`,
  `SettingsModal`, `ProfileModal`, `DeckCardPickerModal`, `DeckImportModal`, `ImportListModal`,
  `JobLogModal`) use `AccessibleModal` as their outermost wrapper.
- `CardTable.tsx` — all sortable headers already have `aria-sort` (lines 229, 241, 252, 263, 274,
  285) and keyboard activation via `onKeyDown` (Enter/Space).
- `CardTable.tsx` — keyboard row navigation (`ArrowUp/Down/Enter`) is already implemented.
- `QuantityCell` in `CardTable.tsx` — already has `role="button"`, `tabIndex={0}`,
  `aria-label={t('cardTable.editQtyLabel', ...)}`, and `onKeyDown` handling.
- `JobsBottomBar.tsx` — already has `aria-live="polite"` + `aria-atomic="true"` + `sr-only`
  span for terminal job status announcements.
- `ConfirmModal.tsx` — already uses `AccessibleModal`, has `htmlFor="confirm-modal-prompt"` on
  the label and `id="confirm-modal-prompt"` on the input.
- `DeckCardPickerModal.tsx` — the i18n key `deckCardPicker.searchLabel` already exists in both
  locale files but the `aria-label` attribute is missing from the input element itself.

## Success Criteria

- `DeckCardPickerModal` search `<input>` has `aria-label={t('deckCardPicker.searchLabel')}`.
- `ProfileModal` crop sub-modal uses `AccessibleModal` with focus trap, ESC, and a proper title.
- `CardDetailModal` image lightbox is wrapped in `AccessibleModal` with `role="dialog"` semantics,
  or alternatively is rendered as a true dialog (not `role="button"`).
- `DeckDetailModal` image lightbox receives the same fix as `CardDetailModal`.
- `DeckImportModal` textarea has a programmatically associated label.
- `SettingsModal` collection import file input has an accessible label.
- No existing visual or keyboard behaviour regresses: ESC closes, overlays dismiss, focus traps
  work, focus is restored on close.
- All new i18n strings are present in both `en.json` and `es.json`.
