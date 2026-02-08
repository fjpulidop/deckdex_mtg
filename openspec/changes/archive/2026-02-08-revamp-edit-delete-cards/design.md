## Context

The dashboard card table currently has an Actions column with Edit and Delete. Clicking a row opens a read-only card detail modal (image + metadata + "Update price"). Edit and Delete live on the table and do not use the modal, so the user has two entry points and a split experience. The backend already exposes PUT `/api/cards/{id}` and DELETE `/api/cards/{id}` (Postgres-backed); the revamp is primarily frontend UX.

## Goals / Non-Goals

**Goals:**
- Single entry point: open card detail via row click; view, edit, and delete only from the modal.
- Inline edit in the modal: toggle to edit mode, change fields in place, Save or Cancel.
- Delete from the modal with confirmation; on confirm, delete card, close modal, refresh list.
- Remove the Actions column from the card table.

**Non-Goals:**
- No new backend endpoints; reuse existing PUT and DELETE for cards.
- No change to "Update price" behavior in the modal.
- No bulk edit or bulk delete.

## Decisions

**1. Modal state: view vs edit**
- **Decision:** Modal has two modes: view (read-only) and edit (editable fields). Mode is component state (e.g. `isEditing`). Edit button visible in view mode; in edit mode, Edit is replaced by Save and Cancel.
- **Rationale:** Keeps one modal component; no separate edit screen or route. Alternatives: separate edit route (rejected — we want unified experience), always-editable fields (rejected — explicit edit reduces accidental edits).

**2. Which fields are editable**
- **Decision:** Editable fields align with the card model used by PUT (e.g. name, type_line, mana_cost, oracle_text, power, toughness, set_name, set_number, rarity, price_eur). Image is not edited in this flow (card image is from Scryfall/storage). If the modal today shows a subset, make that subset editable; design does not require adding new fields only for edit.
- **Rationale:** Backend PUT accepts the same Card model; frontend sends the same shape. Image is typically derived, not user-editable.

**3. Save and Cancel behavior**
- **Decision:** Save: call PUT `/api/cards/{id}` with current form values, then switch back to view mode and optionally refetch card/list. Cancel: discard in-memory edits, switch back to view mode without API call.
- **Rationale:** Clear semantics; Cancel has no side effects. Optional: show unsaved-changes warning when closing modal in edit mode — can be added later if needed.

**4. Delete confirmation**
- **Decision:** When user clicks Delete, show a confirmation dialog (browser confirm or custom modal): "Are you sure you want to delete this card?" with Yes / No. No → close confirmation, stay in card modal. Yes → call DELETE `/api/cards/{id}`, close card modal, invalidate/refetch card list (and stats) so the card disappears.
- **Rationale:** Prevents accidental delete. Custom dialog preferred for i18n and styling; browser `confirm()` acceptable for MVP.

**5. Actions column removal**
- **Decision:** Remove the Actions column from the card table component entirely. No Edit/Delete buttons on rows. Row click remains the only way to open the card modal.
- **Rationale:** Proposal explicitly requires single entry point; table becomes view-only for actions.

**6. Backend**
- **Decision:** No backend change. Use existing PUT `/api/cards/{id}` (update) and DELETE `/api/cards/{id}` (delete). Both require Postgres (501 if not configured); frontend should handle 501/404/400 and show appropriate message or toast.
- **Rationale:** Endpoints exist and match the desired behavior; revamp is UI-only.

## Risks / Trade-offs

- **Risk:** User in edit mode closes modal (e.g. overlay click) and loses edits. **Mitigation:** Either ignore (simple MVP) or add "You have unsaved changes" warning on close; can be a follow-up.
- **Risk:** 501 when Postgres not configured — user clicks Edit or Delete and sees an error. **Mitigation:** Same as today: show backend error (toast/message); optional future improvement to hide Edit/Delete when backend doesn’t support cards CRUD.
- **Trade-off:** No bulk edit/delete from table. **Acceptance:** Out of scope; single-card flows only.

## Migration Plan

- Frontend-only change: deploy new dashboard build. No data migration. Rollback: revert to previous frontend that still had Actions column and old edit/delete flows (if still in repo) or keep backend as-is.

## Open Questions

- None for MVP. Optional later: unsaved-changes warning when leaving edit mode; hide Edit/Delete when DATABASE_URL not set (if we expose that to the frontend).
