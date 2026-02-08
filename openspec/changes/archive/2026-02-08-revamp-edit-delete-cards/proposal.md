## Why

The current edit and delete flows are split: the card table has an Actions column with Edit and Delete buttons that operate outside the card detail modal, while opening a row opens a read-only detail modal. This creates a fragmented experience and two different entry points for viewing vs editing. Unifying view, edit, and delete into a single card detail modal simplifies the mental model and keeps the user in one place.

## What Changes

- **BREAKING:** Remove the Actions column from the card table. Edit and Delete will no longer be available from the table.
- Add Edit and Delete actions inside the card detail modal (the modal opened when the user clicks a table row).
- In the modal: default is read-only view. When the user clicks Edit, text fields become editable in place (no separate window). The Edit button becomes Save, and a Cancel button appears. Save persists changes and returns to read-only; Cancel discards changes and returns to read-only.
- Delete in the modal: when the user clicks Delete, show a confirmation ("Are you sure you want to delete this card?"). No keeps the user in the modal; Yes deletes the card, closes the modal, and updates the list so the card disappears.
- Existing "Update price" behavior in the modal remains; Edit/Delete are additional actions.

## Capabilities

### New Capabilities

None. This change only modifies existing capabilities.

### Modified Capabilities

- **card-detail-modal:** Add requirements for Edit and Delete actions inside the modal; inline edit mode with Save and Cancel; delete confirmation (Yes/No). Modal remains the single place for viewing, editing, and deleting a card (and updating price).
- **web-dashboard-ui:** Remove the requirement or behavior that provides Edit/Delete in the card table (Actions column). Table rows remain clickable to open the card detail modal; the table no longer shows an Actions column.

## Impact

- **Frontend — card table:** Remove the Actions column and any Edit/Delete handlers that live on table rows.
- **Frontend — card detail modal:** Add Edit and Delete buttons; implement view vs edit mode (read-only vs editable fields), Save and Cancel for edit; implement delete confirmation dialog and delete flow (close modal and refresh list on confirm).
- **Backend:** If card update (PATCH/PUT) and card delete (DELETE) endpoints do not exist, they must be added or specified; the new UI will call them on Save and on delete confirm. If they already exist, the frontend will use them from the modal.
