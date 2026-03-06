## Context

The "Import list" button in CardTable currently navigates to `/import`. We want it to open a modal (like CardFormModal) where the user pastes a list or drops a file. On submit, the modal calls `api.importResolve()`, then navigates to `/import` with the resolved data in route state so the Import page skips straight to the review step.

## Goals / Non-Goals

**Goals:**
- Modal with file/text tabs following CardFormModal overlay pattern
- On submit: resolve → navigate to `/import` with pre-resolved data
- Import page detects route state and skips to review step

**Non-Goals:**
- Full import wizard inside the modal
- New backend endpoints
- Changes to steps 3–6 of the import wizard

## Decisions

### 1. ImportListModal as standalone component
Create `frontend/src/components/ImportListModal.tsx` following the CardFormModal pattern: fixed overlay, click-outside-to-close, `onClose` prop. Dashboard manages open/close state via `useState`.

**Alternative considered:** Reuse CardFormModal with different content — rejected, too different in purpose and UI.

### 2. Pass resolved data via React Router state
Use `navigate('/import', { state: { resolveData } })` to pass the `ResolveResponse` to the Import page. The Import page checks `location.state?.resolveData` on mount — if present, sets `resolveData` and jumps to review step, clearing state to avoid stale data on refresh.

**Alternative considered:** Global state (context/store) — rejected as overkill for a one-shot handoff. Route state is the standard React Router pattern for this.

### 3. Tab toggle for file/text input modes
Reuse the same tab toggle pattern already in the Import page upload step. File tab has drag-and-drop zone; text tab has textarea. Share the same styling.

### 4. Loading state inside modal
While `importResolve` runs, show a spinner/loading state inside the modal (disable submit, show progress text). On error, show error message inside modal. On success, close modal and navigate.

### 5. Dashboard state: extend cardModal to include 'import'
Change `cardModal` state from `null | 'add'` to `null | 'add' | 'import'`. The `onImport` callback sets `cardModal` to `'import'` instead of navigating.

## Risks / Trade-offs

- [Low risk] Route state lost on page refresh → acceptable, user can restart from `/import` upload step. We clear state after consuming it.
- [Low risk] Large resolve response in route state → fine for typical imports (hundreds of cards), React Router handles this in memory.
