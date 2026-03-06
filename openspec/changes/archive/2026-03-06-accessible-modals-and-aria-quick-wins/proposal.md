## Why

The DeckDex frontend has ~10 modal dialogs and numerous interactive elements that are completely inaccessible to screen reader and keyboard-only users: modals lack `role="dialog"` and focus trapping, error messages are not announced, icon-only buttons have no accessible names, and sortable table headers cannot be activated via keyboard. A reusable `<AccessibleModal>` wrapper and targeted ARIA attribute additions will resolve the highest-impact issues with minimal effort.

## What Changes

- **New `AccessibleModal` wrapper component** (`frontend/src/components/AccessibleModal.tsx`): encapsulates `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus trap (Tab key confined within modal), Escape to close, auto-focus first focusable element, restore focus to trigger on close, overlay click to close.
- **Apply `<AccessibleModal>` to all existing modals**: CardFormModal, CardDetailModal, SettingsModal, ProfileModal, DeckDetailModal, DeckCardPickerModal, DeckImportModal, ImportListModal, JobLogModal, LandingNavbar GitHub modal.
- **Add `role="alert"`** to all error message containers (~10 components).
- **Add `aria-label`** to all icon-only buttons: close X buttons in every modal, LanguageSwitcher, avatar upload in ProfileModal, landing footer social links, etc. (~10 targets).
- **Add `htmlFor`/`id` associations** to label/input pairs in CardFormModal, CardDetailModal, ProfileModal, ConfirmModal, SettingsModal, and Filters (~30 fields).
- **Add `aria-sort` + keyboard support** to CardTable sortable column headers (tabIndex, onKeyDown Enter/Space, aria-sort attribute).
- **Add keyboard trigger** (tabIndex, role="button", onKeyDown) to QuantityCell click-to-edit in CardTable.

## Non-goals

- `aria-live` regions for dynamic content (separate change)
- Color contrast fixes (high effort, systematic audit needed)
- Chart accessibility / data table fallbacks (high effort)
- Menu keyboard navigation with arrow keys
- i18n fixes for hardcoded strings in ActionButtons
- Tab role semantics for toggle interfaces

## Capabilities

### New Capabilities
- `accessible-modals`: Reusable `AccessibleModal` wrapper component with full keyboard/screen-reader support, applied to all modal dialogs in the app.

### Modified Capabilities
- `web-dashboard-ui`: ARIA improvements to CardTable (sortable headers, QuantityCell), error role="alert", icon button aria-labels, label/input associations.

## Impact

- **Frontend only**: No backend or core changes.
- **New file**: `frontend/src/components/AccessibleModal.tsx`
- **Modified components**: CardFormModal, CardDetailModal, SettingsModal, ProfileModal, DeckDetailModal, DeckCardPickerModal, DeckImportModal, ImportListModal, JobLogModal, LandingNavbar, CardTable, Filters, CollectionInsights, landing/Footer
- **No new dependencies**: Focus trap implemented natively (no external library)
- **No API changes**, no migration required
- **TypeScript strict**: All new code must pass `tsc --noEmit`
