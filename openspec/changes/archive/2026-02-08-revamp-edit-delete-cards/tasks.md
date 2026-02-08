## 1. Remove Actions column from card table

- [x] 1.1 Remove the Actions column from the card table component (no Edit/Delete buttons on rows)
- [x] 1.2 Ensure row click is the only way to open the card detail modal from the table

## 2. Card detail modal: Edit and Delete actions

- [x] 2.1 Add Edit and Delete buttons to the card detail modal (visible when card has id; hide when card has no id)
- [x] 2.2 Add view vs edit mode state (e.g. isEditing); default to view mode when modal opens
- [x] 2.3 In view mode show Edit and Delete; when user clicks Edit switch to edit mode and replace Edit with Save and Cancel buttons
- [x] 2.4 In edit mode make displayed card fields editable in place (name, type line, mana cost, oracle text, power, toughness, set name, set number, rarity, price as per card model)
- [x] 2.5 On Save call PUT /api/cards/{id} with current form values; on success return to view mode and refresh card/list as needed
- [x] 2.6 On Cancel discard edits and return to view mode without API call
- [x] 2.7 On Delete show confirmation dialog ("Are you sure you want to delete this card?" with Yes/No); No closes confirmation and keeps modal open
- [x] 2.8 On delete confirmation Yes call DELETE /api/cards/{id}, close the card detail modal, and invalidate/refetch card list and stats so the card disappears
- [x] 2.9 Handle API errors (501, 404, 400) for update and delete with user-visible message or toast

## 3. Verification and cleanup

- [x] 3.1 Verify Update price button still works in the modal and remains visible alongside Edit and Delete when card has id
- [x] 3.2 Remove or refactor any separate Edit card modal / edit flow that was triggered from the table so all editing goes through the card detail modal
