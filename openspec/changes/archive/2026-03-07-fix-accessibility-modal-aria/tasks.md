# Tasks: Fix Remaining Accessibility Issues

All changes are frontend-only. No backend, no migrations, no new dependencies.

---

## Task 1: Add i18n keys for DeckCardPickerModal search label

**Files:** `frontend/src/locales/en.json`, `frontend/src/locales/es.json`

**What to do:**

In `en.json`, inside the `"deckCardPicker"` object, add after the `"searchPlaceholder"` key:
```json
"searchLabel": "Search cards"
```

In `es.json`, inside the `"deckCardPicker"` object, add after the `"searchPlaceholder"` key:
```json
"searchLabel": "Buscar cartas"
```

**Acceptance criteria:**
- `t('deckCardPicker.searchLabel')` resolves to `"Search cards"` in English and `"Buscar cartas"`
  in Spanish.
- Both locale files remain valid JSON.

**Dependencies:** None.

---

## Task 2: Add aria-label to DeckCardPickerModal search input

**File:** `frontend/src/components/DeckCardPickerModal.tsx`

**What to do:**

Locate the unlabelled `<input>` element at approximately line 115 (the search input inside the
filter bar). Add `aria-label={t('deckCardPicker.searchLabel')}` to it.

Before:
```tsx
<input
  type="text"
  placeholder={t('deckCardPicker.searchPlaceholder')}
  value={search}
  onChange={(e) => setSearch(e.target.value)}
  className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
/>
```

After:
```tsx
<input
  type="text"
  aria-label={t('deckCardPicker.searchLabel')}
  placeholder={t('deckCardPicker.searchPlaceholder')}
  value={search}
  onChange={(e) => setSearch(e.target.value)}
  className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
/>
```

**Acceptance criteria:**
- The search input has an `aria-label` attribute in the rendered DOM.
- The input still functions identically (typing updates the card list).
- No TypeScript errors (`aria-label` is a valid `InputHTMLAttributes` prop).

**Dependencies:** Task 1 (i18n key must exist before referencing it).

---

## Task 3: Refactor ConfirmModal to use AccessibleModal

**File:** `frontend/src/components/ConfirmModal.tsx`

**What to do:**

This task replaces the hand-rolled dialog implementation with `AccessibleModal`. Read the full
current file before making changes.

**Step 1 — Add import:**
Add `import { AccessibleModal } from './AccessibleModal';` at the top of the file.

**Step 2 — Remove the ESC `useEffect`:**
Delete the entire `useEffect` block that adds/removes a `keydown` listener for the Escape key
(lines 53–60 in the current file). `AccessibleModal` handles this.

**Step 3 — Remove `handleOverlayKeyDown`:**
Delete the `handleOverlayKeyDown` function (lines 64–68). This handler fires Enter on the overlay
to confirm. It is not needed; keyboard users activate the focused Confirm button with Enter/Space.

**Step 4 — Replace the outer `<div>` overlay with `<AccessibleModal>`:**

Current outer structure:
```tsx
if (!isOpen) return null;

return (
  <div
    className="fixed inset-0 bg-black/50 flex items-center justify-center z-[70] p-4"
    onClick={onCancel}
    onKeyDown={handleOverlayKeyDown}
    role="dialog"
    aria-modal="true"
    aria-labelledby="confirm-modal-title"
  >
    <div
      className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-sm w-full p-6 flex flex-col gap-4"
      onClick={e => e.stopPropagation()}
    >
      ...panel content...
    </div>
  </div>
);
```

New structure:
```tsx
return (
  <AccessibleModal
    isOpen={isOpen}
    onClose={onCancel}
    titleId="confirm-modal-title"
    className="z-[70]"
  >
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-sm w-full p-6 flex flex-col gap-4">
      ...panel content (unchanged)...
    </div>
  </AccessibleModal>
);
```

Notes:
- Remove `if (!isOpen) return null;` — `AccessibleModal` handles this internally.
- Remove `role`, `aria-modal`, `aria-labelledby` from the outer element — they are now in
  `AccessibleModal`.
- Remove `onClick={onCancel}` from the outer element — `AccessibleModal` handles overlay click.
- Remove `onClick={e => e.stopPropagation()}` from the inner panel div — `AccessibleModal`'s
  inner panel div handles `stopPropagation`.
- The inner panel `<div>` loses its `onClick` prop entirely.

**Step 5 — Fix prompt label/input association:**

Inside the `{promptLabel && (...)}` block, update the `<label>` and `<input>` as follows:

Current label:
```tsx
<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
  {promptLabel}
</label>
```

Updated label:
```tsx
<label
  htmlFor="confirm-modal-prompt"
  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
>
  {promptLabel}
</label>
```

Current input (no id):
```tsx
<input
  ref={inputRef}
  type="text"
  ...
/>
```

Updated input (with id):
```tsx
<input
  id="confirm-modal-prompt"
  ref={inputRef}
  type="text"
  ...
/>
```

**Step 6 — Verify focus-override useEffect is still present:**

The `useEffect` that focuses the confirm button or prompt input on open (lines 43–50) must remain.
It overrides `AccessibleModal`'s auto-focus to point to the correct element. Do not remove it.

**Final shape of ConfirmModal.tsx imports section:**
```tsx
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AccessibleModal } from './AccessibleModal';
```

**Acceptance criteria:**
- `ConfirmModal` renders an `AccessibleModal` as its root element.
- The `<label>` inside `{promptLabel && ...}` has `htmlFor="confirm-modal-prompt"`.
- The `<input>` inside `{promptLabel && ...}` has `id="confirm-modal-prompt"`.
- No ESC `useEffect` exists in `ConfirmModal` — pressing ESC still closes the modal (via
  `AccessibleModal`).
- No `handleOverlayKeyDown` function exists.
- No `role="dialog"`, `aria-modal`, `aria-labelledby` on any `<div>` inside `ConfirmModal`.
- When opened without a prompt, focus lands on the Confirm button.
- When opened with a prompt, focus lands on the prompt input.
- Clicking the overlay closes the modal.
- Body scroll is locked while the modal is open.
- Focus returns to the triggering element when the modal closes.
- TypeScript compiles without errors.
- `npm run lint` passes.

**Dependencies:** None (can be done in parallel with Tasks 1–2, but `AccessibleModal` must exist
at its current path — it does).

---

## Task 4: Add aria-live region to JobsBottomBar

**File:** `frontend/src/components/JobsBottomBar.tsx`

**What to do:**

Inside the `ActiveJobEntry` function component's JSX return, add a visually hidden `aria-live`
span that contains the terminal status text only when the job is finished.

Locate the outermost `<div>` returned by `ActiveJobEntry` (the `border-l-4` div). Immediately
before the closing tag of this div, add:

```tsx
{/* Screen reader announcement for job terminal state */}
<span
  className="sr-only"
  aria-live="polite"
  aria-atomic="true"
>
  {isFinished ? statusText : ''}
</span>
```

The `statusText` variable is already computed in `ActiveJobEntry` (line 65 in the current file):
```ts
const statusText = isCancelled
  ? t('jobsBar.cancelled')
  : isError
  ? t('activeJobs.status.failed')
  : isFinished
  ? t('jobsBar.completed')
  : `${Math.round(progress.percentage)}% — ${progress.current}/${progress.total}`;
```

When `isFinished` is false, the span content is `''` — no announcement. When `isFinished` becomes
true, the span content becomes the terminal status string (e.g. "Completed", "Cancelled",
"Failed"), which the screen reader announces politely.

**Acceptance criteria:**
- A `<span aria-live="polite" aria-atomic="true" className="sr-only">` exists inside each
  `ActiveJobEntry` render.
- The span is empty (`''`) while the job is running.
- The span contains the terminal status text when `isFinished === true`.
- The span is visually hidden (Tailwind `sr-only` class).
- No visual layout change — the span is zero-size.
- TypeScript compiles without errors.
- `npm run lint` passes.

**Dependencies:** None (independent of Tasks 1–3).

---

## Task 5: Verify no regressions with manual testing checklist

**Files:** None (testing task, no code changes)

**What to verify:**

### ConfirmModal
- Open any confirmation dialog (e.g., delete a card in the card detail modal, delete a deck in
  the deck builder, create a new deck with the prompt variant).
- [ ] Focus lands on the Confirm button when no prompt is shown.
- [ ] Focus lands on the prompt input when `promptLabel` is set (create new deck flow).
- [ ] Clicking the prompt label text moves focus to the input.
- [ ] Pressing Escape closes the dialog without confirming.
- [ ] Clicking outside the modal panel closes it.
- [ ] Page scroll is locked while the modal is open (no scrolling in the background).
- [ ] After closing (either path), focus returns to the button that opened the modal.
- [ ] Confirming calls the correct action (card is deleted, deck is created, etc.).
- [ ] Pressing Enter on the focused Confirm button submits.

### DeckCardPickerModal
- Open the deck card picker from a deck detail view.
- [ ] Inspect the search input's DOM — it has `aria-label="Search cards"`.
- [ ] Typing in the search input filters the card list.

### JobsBottomBar
- Trigger a price update job from the dashboard toolbar.
- [ ] Inspect the `ActiveJobEntry` DOM — a `sr-only` span with `aria-live="polite"` is present.
- [ ] While the job is running, the `aria-live` span is empty.
- [ ] After the job completes, the `aria-live` span contains the status text (e.g. "Completed").

**Dependencies:** Tasks 1–4 must all be complete.
