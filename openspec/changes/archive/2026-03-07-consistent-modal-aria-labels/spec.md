# Change: consistent-modal-aria-labels

## Summary

Add a consistent, accessible close button to the `AccessibleModal` wrapper component and update the 5 modals that are missing aria-labels on their close buttons.

## Problem

Modal close buttons lack `aria-label` attributes in these components:
- `CardFormModal` - no close button at all (only a Cancel button)
- `ConfirmModal` - does not use `AccessibleModal`; no explicit close button (relies on ESC/overlay)
- `DeckCardPickerModal` - has a Cancel button but no aria-label on it
- `DeckImportModal` - has a Cancel button but no aria-label on it
- `ImportListModal` - has a Cancel button but no aria-label on it

## Solution

### AccessibleModal changes

Add optional `showCloseButton?: boolean` prop. When `true`, render an `X` icon button (from `lucide-react`) in the top-right corner of the modal panel with:
- `aria-label={t('common.close')}`
- Consistent styling matching `ProfileModal`/`SettingsModal` pattern
- `onClick={onClose}` handler

The close button is rendered inside the inner `<div>` (the panel wrapper), positioned absolutely at top-right.

Note: `onClose` already exists on `AccessibleModalProps` — no new prop needed for the handler.

### Modal updates

Pass `showCloseButton={true}` to `AccessibleModal` in:
- `CardFormModal`
- `DeckCardPickerModal`
- `DeckImportModal`
- `ImportListModal`

`ConfirmModal` does not use `AccessibleModal` and has semantic Cancel/Confirm buttons — no change needed.

## Files affected

- `frontend/src/components/AccessibleModal.tsx` — add `showCloseButton` prop + button render
- `frontend/src/components/CardFormModal.tsx` — pass `showCloseButton={true}`
- `frontend/src/components/DeckCardPickerModal.tsx` — pass `showCloseButton={true}`
- `frontend/src/components/DeckImportModal.tsx` — pass `showCloseButton={true}`
- `frontend/src/components/ImportListModal.tsx` — pass `showCloseButton={true}`
