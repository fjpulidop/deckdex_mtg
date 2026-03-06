## 1. AccessibleModal Core Component

- [x] 1.1 Create `frontend/src/components/AccessibleModal.tsx` with `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, overlay click-to-close, body scroll-lock on mount/unmount
- [x] 1.2 Implement focus trap in AccessibleModal: collect focusable descendants on each Tab keypress, cycle within modal, handle Shift+Tab for reverse cycle
- [x] 1.3 Implement Escape-to-close in AccessibleModal via document keydown listener
- [x] 1.4 Implement auto-focus of first focusable element on modal open (setTimeout 0 to wait for render)
- [x] 1.5 Implement focus restoration: capture `document.activeElement` before opening, restore on close

## 2. Apply AccessibleModal to All Modals

- [x] 2.1 Refactor `CardFormModal.tsx`: replace outer overlay div with `<AccessibleModal>`, add `id` to title heading, pass `titleId`
- [x] 2.2 Refactor `CardDetailModal.tsx`: replace outer overlay div with `<AccessibleModal>`, add `id` to title heading
- [x] 2.3 Refactor `SettingsModal.tsx`: replace outer overlay div with `<AccessibleModal>`, add `id` to title heading
- [x] 2.4 Refactor `ProfileModal.tsx`: replace outer overlay div with `<AccessibleModal>`, add `id` to title heading
- [x] 2.5 Refactor `DeckDetailModal.tsx`: replace outer overlay div with `<AccessibleModal>`, add `id` to title heading
- [x] 2.6 Refactor `DeckCardPickerModal.tsx`: replace outer overlay div with `<AccessibleModal>`, add `id` to title heading
- [x] 2.7 Refactor `DeckImportModal.tsx`: replace outer overlay div with `<AccessibleModal>`, add `id` to title heading
- [x] 2.8 Refactor `ImportListModal.tsx`: replace outer overlay div with `<AccessibleModal>`, add `id` to title heading
- [x] 2.9 Refactor `JobLogModal.tsx`: replace outer overlay div with `<AccessibleModal>`, add `id` to title heading

## 3. role="alert" on Error Containers

- [x] 3.1 Add `role="alert"` to error div in `CardFormModal.tsx`
- [x] 3.2 Add `role="alert"` to error div in `SettingsModal.tsx`
- [x] 3.3 Add `role="alert"` to error div in `ProfileModal.tsx`
- [x] 3.4 Add `role="alert"` to error div in `DeckImportModal.tsx`
- [x] 3.5 Add `role="alert"` to error div in `ImportListModal.tsx`
- [x] 3.6 Add `role="alert"` to error/createError div in `DeckBuilder.tsx` page
- [x] 3.7 Add `role="alert"` to error state in `Dashboard.tsx` page

## 4. aria-label on Icon-Only Buttons

- [x] 4.1 Add `aria-label="Close"` to close (X) buttons in: CardFormModal, CardDetailModal, SettingsModal, ProfileModal, DeckDetailModal, DeckCardPickerModal, DeckImportModal, ImportListModal, JobLogModal
- [x] 4.2 Add `aria-label` to avatar/photo upload button in `ProfileModal.tsx`
- [x] 4.3 Add `aria-label` to social icon links in `frontend/src/components/landing/Footer.tsx`

## 5. Form Label/Input Associations

- [x] 5.1 Add `id` attrs to inputs and `htmlFor` to labels in `CardFormModal.tsx` (name, type, rarity, price, set fields)
- [x] 5.2 Add `id` attrs to inputs and `htmlFor` to labels in `CardDetailModal.tsx` edit form fields
- [x] 5.3 Add `id`/`htmlFor` to display name field in `ProfileModal.tsx`
- [x] 5.4 Add `id`/`htmlFor` to fields in `SettingsModal.tsx`
- [x] 5.5 Add `id`/`htmlFor` to search, price min/max, rarity, type, set inputs in `Filters.tsx`

## 6. CardTable Accessibility

- [x] 6.1 Add `tabIndex={0}`, `onKeyDown` (Enter/Space to sort), and `aria-sort` attribute to each sortable `<th>` in `CardTable.tsx`
- [x] 6.2 Add `tabIndex={0}`, `role="button"`, `aria-label`, and `onKeyDown` (Enter/Space to activate edit) to the quantity display span in `QuantityCell` in `CardTable.tsx`
