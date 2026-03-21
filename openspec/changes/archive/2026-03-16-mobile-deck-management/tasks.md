# Tasks: Mobile-Optimized Deck Management

All tasks are tagged `[frontend]`. No backend tasks.

Dependencies are noted per task. Execute in the order listed; tasks within the same group can be parallelized unless they edit the same file.

---

## Group 1 — Foundation: AccessibleModal full-screen prop

### Task 1.1 — Add `fullScreenOnMobile` prop to `AccessibleModal` [frontend]

**File:** `frontend/src/components/AccessibleModal.tsx`

**Change:** Add optional prop `fullScreenOnMobile?: boolean` to the `AccessibleModalProps` interface. When `true`, replace the overlay's static `p-4 flex items-center justify-center` with responsive Tailwind classes that apply padding and centering only at `sm:` and above, and add `max-sm:w-screen max-sm:h-[100dvh] max-sm:!rounded-none` to the panel's inner wrapper (pass via a `panelClassName` mechanism or apply directly as extra classes on the inner `div.relative`).

Implementation approach: the overlay `div` changes from:
```
fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4
```
to (when `fullScreenOnMobile` is true):
```
fixed inset-0 bg-black/50 sm:flex sm:items-center sm:justify-center z-50 sm:p-4
```
The panel wrapper `div.relative` gains `max-sm:w-full max-sm:h-[100dvh]` so it fills the screen on small viewports. No change when `fullScreenOnMobile` is false/absent.

**Acceptance criteria:**
- Existing modal tests pass without modification (prop defaults to `false`).
- When `fullScreenOnMobile={true}`, on a viewport narrower than 640 px the panel fills the screen (no visible outer padding).
- On viewport >= 640 px, behaviour is identical to today regardless of the prop value.

**Dependencies:** None.

---

## Group 2 — Deck grid tile min-height

### Task 2.1 — Ensure deck tiles are thumb-reachable on mobile [frontend]

**File:** `frontend/src/pages/DeckBuilder.tsx`

**Change:** On `DeckCardButton`, change `min-h-[120px]` to `min-h-[100px]` and verify the grid already uses `grid-cols-2` at the smallest breakpoint. No structural change; this is already the case — verify and confirm. Also ensure the "+" add deck tile has the same minimum height.

Note: the current `min-h-[120px]` already exceeds the 44 px requirement. This task is a verification/confirmation step. If any `min-h-[]` is less than 44 px, raise it. If everything is fine, mark as done with a code comment confirming intentional sizes.

**Acceptance criteria:**
- Both `DeckCardButton` and the "+" tile have min-height >= 44 px.
- No visual regression on desktop.

**Dependencies:** None (can be done in parallel with Group 1).

---

## Group 3 — DeckDetailModal mobile layout

### Task 3.1 — Apply full-screen modal on mobile in DeckDetailModal [frontend]

**File:** `frontend/src/components/DeckDetailModal.tsx`

**Change:** Pass `fullScreenOnMobile` to the outer `AccessibleModal`. Add `max-sm:rounded-none max-sm:w-full max-sm:h-full` to the panel div (the `bg-white dark:bg-gray-800 rounded-xl` div). Ensure the panel uses `flex flex-col` and `overflow-hidden` already (it does).

**Acceptance criteria:**
- On viewport < 640 px, the deck detail modal fills the full screen.
- On viewport >= 768 px, the modal renders identically to today.

**Dependencies:** Task 1.1 must be complete.

### Task 3.2 — Hide left image panel on mobile [frontend]

**File:** `frontend/src/components/DeckDetailModal.tsx`

**Change:** Add `hidden md:flex` (or `hidden md:block`) to the left image panel div (`w-64 flex-shrink-0 border-r ...`). The right card list panel already uses `flex-1 overflow-y-auto` and will expand to full width when the image panel is hidden.

**Acceptance criteria:**
- On viewport < 768 px, the image panel is not rendered and the card list occupies full modal width.
- On viewport >= 768 px, the image panel is visible as before.

**Dependencies:** Task 3.1.

### Task 3.3 — Increase card row tap height [frontend]

**File:** `frontend/src/components/DeckDetailModal.tsx`

**Change:** In the `<li>` for each card row, change `py-1` to `py-2.5`. This raises each row to ~44 px. This applies globally (desktop and mobile).

**Acceptance criteria:**
- Card rows in the modal are visually taller; no content is clipped.
- Total deck height with 60-card Commander deck still scrolls correctly.

**Dependencies:** Task 3.1 (same file; do together).

### Task 3.4 — Make remove button always visible on touch mobile [frontend]

**File:** `frontend/src/components/DeckDetailModal.tsx`

**Change:** On the remove `<button>` inside each card row, replace:
```
className="opacity-0 group-hover:opacity-100 ..."
```
with:
```
className="sm:opacity-0 sm:group-hover:opacity-100 ..."
```
This makes the button always visible on viewports below the `sm` breakpoint (< 640 px), while preserving the hover-only behaviour on desktop.

Also increase the button's touch target: add `p-3` (replacing `p-1`) so the tap area is 44 × 44 px. This slightly increases the button's visual size on desktop as well; adjust to `sm:p-1 p-3` if that is objectionable.

**Acceptance criteria:**
- On viewport < 640 px, the remove button is always visible on every card row.
- On viewport >= 640 px (sm and up), the remove button is hidden until the row is hovered.
- Clicking/tapping the remove button removes the card as before.

**Dependencies:** Task 3.3 (same file; do together).

### Task 3.5 — Add sticky mobile action bar [frontend]

**File:** `frontend/src/components/DeckDetailModal.tsx`

**Change:** Add a `<div className="md:hidden sticky bottom-0 ...">` bar as a sibling to the scrollable card list area (inside the `flex flex-col` modal). The bar contains four buttons: Add card, Export, Import, Delete deck. Wire each to the same handlers as the header buttons: `setPickerOpen(true)`, `handleExport`, `setImportOpen(true)`, `handleDelete`. Apply `pb-[env(safe-area-inset-bottom,0px)]` (inline style: `{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }`) for notch-safe layout.

Each button: `flex-1 flex items-center justify-center gap-1 py-3 text-sm font-medium`. Delete button: `text-red-600 dark:text-red-400`. Add card button: `text-indigo-600 dark:text-indigo-400`. Export and Import: `text-gray-700 dark:text-gray-200`.

Also hide the header action buttons row on mobile: add `hidden md:flex` to the `<div className="flex items-center gap-2 shrink-0 ml-auto">` that currently wraps Export, Import, Add card, Delete.

Use the i18n keys `deckDetail.mobileActions.addCard`, `deckDetail.mobileActions.export`, `deckDetail.mobileActions.import`, `deckDetail.mobileActions.deleteDeck` for the bar labels.

**Acceptance criteria:**
- On viewport < 768 px, the sticky bar is visible at the bottom of the modal with all four actions.
- On viewport >= 768 px, the bar is hidden and the header actions are visible.
- Tapping each bar button triggers the correct action.
- The bar does not overlap content on notched phones (safe-area padding).

**Dependencies:** Tasks 3.1, 3.2, locale keys from Task 6.1.

---

## Group 4 — Swipe-to-remove hook

### Task 4.1 — Create `useSwipeToRemove` hook [frontend]

**File:** `frontend/src/hooks/useSwipeToRemove.ts` (new file)

**Interface:**
```typescript
export function useSwipeToRemove(
  onRemove: () => void
): {
  containerProps: React.HTMLAttributes<HTMLElement>;
  translateX: number;
  isRevealed: boolean;
}
```

**Behaviour:**
- On `pointerdown`: if `event.pointerType === 'mouse'`, immediately return (no-op). Otherwise, store `startX`, set `pointerId`, call `element.setPointerCapture(pointerId)`.
- On `pointermove`: compute `dx = currentX - startX`. If `Math.abs(dx) > Math.abs(dy) * 1.5` and `dx < 0`, set state `translateX = Math.max(dx, -72)` so the row slides left. Emit a CSS variable / state value.
- On `pointerup` / `pointercancel`: if `translateX <= -72`, call `onRemove()` then reset. Else animate back to 0 (`translateX = 0` with a `transitionDuration` flag set for 200 ms).
- `containerProps` contains `{ onPointerDown, onPointerMove, onPointerUp, onPointerCancel }`.
- `translateX` is the current offset in px (0 when idle).
- `isRevealed` is true when `translateX <= -36` (used to colour the strip red).

**Acceptance criteria:**
- On a touch device, swiping a row >= 72 px left and releasing calls the `onRemove` callback.
- Partial swipe (< 72 px) returns the row to position 0 with a short animation.
- On a mouse device, `containerProps` events are all no-ops (the hook is a no-op branch).
- Unit test: mock pointer events and assert `onRemove` is called after a ≥ 72 px leftward touch sequence.

**Dependencies:** None.

### Task 4.2 — Wire `useSwipeToRemove` into DeckDetailModal card rows [frontend]

**File:** `frontend/src/components/DeckDetailModal.tsx`

**Change:** Import `useSwipeToRemove`. For each card row `<li>`, extract to a sub-component (or use the hook inline per-item via a wrapper component) that calls `useSwipeToRemove(() => handleRemoveCard(card.id!))`. Apply `containerProps` to the `<li>`. Apply `style={{ transform: \`translateX(\${translateX}px)\`, transition: isAnimatingBack ? 'transform 200ms' : undefined }}` to an inner wrapper div. Behind the row, render an absolutely-positioned `<div className="absolute right-0 inset-y-0 w-[72px] bg-red-500 flex items-center justify-center text-white text-xs font-bold rounded-r">Remove</div>` that is shown when `isRevealed`.

The `<li>` itself needs `relative overflow-hidden` to clip the strip.

Note: since the hook is called per-card, extract the card row to a small local component `DeckCardRow` to allow per-row hook invocation (hooks cannot be called in a loop without a wrapper component).

**Acceptance criteria:**
- Swiping a card row on a touch device reveals a red strip and removes the card on full swipe.
- Partial swipe returns to position 0.
- On desktop (mouse), rows look and behave exactly as before (no red strip, hover remove button works).
- No regression on existing `DeckDetailModal` tests.

**Dependencies:** Tasks 4.1, 3.1–3.4.

---

## Group 5 — DeckCardPickerModal and DeckImportModal mobile

### Task 5.1 — Make DeckCardPickerModal full-screen on mobile [frontend]

**File:** `frontend/src/components/DeckCardPickerModal.tsx`

**Changes:**
1. Pass `fullScreenOnMobile` to the `AccessibleModal`.
2. Add `max-sm:rounded-none max-sm:w-full max-sm:h-full` to the panel div.
3. Card list buttons: change `py-2` to `py-3`.
4. Footer "Add to Deck" button: add `w-full sm:w-auto` so it fills the footer row on mobile.
5. The filters row (`flex flex-wrap items-center gap-3`) already wraps; verify it remains accessible on a 390 px viewport. No structural change needed beyond confirming inputs have sufficient height.

**Acceptance criteria:**
- On viewport < 640 px, picker fills the screen.
- On viewport >= 640 px, picker renders with existing `max-w-2xl max-h-[80vh]`.
- "Add to Deck" is full-width on mobile.
- Card rows are at least 44 px tall.

**Dependencies:** Task 1.1.

### Task 5.2 — Make DeckImportModal full-screen on mobile [frontend]

**File:** `frontend/src/components/DeckImportModal.tsx`

**Changes:**
1. Pass `fullScreenOnMobile` to the `AccessibleModal`.
2. Add `max-sm:rounded-none max-sm:w-full max-sm:h-full max-sm:max-w-none` to the panel div.
3. Add `flex-1` to the body `<div className="px-6 py-4 flex flex-col gap-4">` so it grows to fill available height.
4. Add `flex-1` to the `<textarea>` (remove fixed `h-48` on mobile via `sm:h-48 h-auto flex-1`).

**Acceptance criteria:**
- On viewport < 640 px, import modal fills the screen; textarea expands to fill available space.
- On viewport >= 640 px, modal renders with existing `max-w-lg`; textarea retains its `h-48`.

**Dependencies:** Task 1.1.

---

## Group 6 — i18n

### Task 6.1 — Add mobile action bar locale keys [frontend]

**Files:** `frontend/src/locales/en.json`, `frontend/src/locales/es.json`

**Change:** Add the following keys nested under `"deckDetail"`:

```json
"mobileActions": {
  "addCard": "Add",
  "export": "Export",
  "import": "Import",
  "deleteDeck": "Delete"
}
```

Spanish equivalents in `es.json`:
```json
"mobileActions": {
  "addCard": "Añadir",
  "export": "Exportar",
  "import": "Importar",
  "deleteDeck": "Eliminar"
}
```

**Acceptance criteria:**
- Both locale files are valid JSON after the change.
- Keys are nested correctly under the existing `deckDetail` object.
- No other existing keys are modified.

**Dependencies:** None.

---

## Group 7 — Tests

### Task 7.1 — Unit test for `useSwipeToRemove` [frontend]

**File:** `frontend/src/hooks/__tests__/useSwipeToRemove.test.ts` (new file)

**Tests:**
1. Mouse pointerdown → `onRemove` never called, `translateX` stays 0.
2. Touch pointerdown + pointermove 80 px left + pointerup → `onRemove` called once.
3. Touch pointerdown + pointermove 40 px left + pointerup → `onRemove` not called, `translateX` returns to 0.
4. Touch pointerdown + pointermove more horizontal than vertical (passes axis-lock) → captured; opposite (more vertical) → not captured.

Use Vitest + `@testing-library/react` with `renderHook`. Simulate pointer events via `fireEvent` or direct calls to the returned handlers.

**Acceptance criteria:**
- All four test cases pass.
- No `scope="module"` fixture issues (pure hook, no fixtures needed).

**Dependencies:** Task 4.1.

### Task 7.2 — DeckDetailModal: verify mobile remove button visibility [frontend]

**File:** `frontend/src/components/__tests__/DeckDetailModal.test.tsx` (existing file)

**Change:** Add one test that renders `DeckDetailModal` and asserts the remove button for a card row does not have `opacity-0` as an unconditional class (i.e. the class is now `sm:opacity-0 sm:group-hover:opacity-100`). This is a snapshot/class-check test, not a visual test.

**Acceptance criteria:**
- New test passes.
- No existing tests broken.

**Dependencies:** Task 3.4.

### Task 7.3 — Smoke test: DeckCardPickerModal "Add to Deck" is full-width on mobile [frontend]

**File:** `frontend/src/components/__tests__/DeckCardPickerModal.test.tsx` (new or existing)

If no test file exists, create one. Add a test that renders the picker and asserts the "Add to Deck" button has the class `w-full` in its class list.

**Acceptance criteria:**
- Test passes.
- No existing tests broken.

**Dependencies:** Task 5.1.
