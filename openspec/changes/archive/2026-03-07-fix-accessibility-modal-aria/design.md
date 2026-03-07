# Design: Fix Remaining Accessibility Issues

## Impact Analysis

| File | Change type | Reason |
|---|---|---|
| `frontend/src/components/ConfirmModal.tsx` | Refactor | Replace manual dialog impl with `AccessibleModal` wrapper |
| `frontend/src/components/DeckCardPickerModal.tsx` | Small fix | Add `aria-label` to unlabelled search input |
| `frontend/src/components/JobsBottomBar.tsx` | Addition | Add `aria-live="polite"` status region |
| `frontend/src/locales/en.json` | Addition | i18n key `deckCardPicker.searchLabel` |
| `frontend/src/locales/es.json` | Addition | i18n key `deckCardPicker.searchLabel` |

No backend files, no migrations, no new dependencies.

---

## 1. ConfirmModal — Refactor to use AccessibleModal

### Current state

`ConfirmModal` (`frontend/src/components/ConfirmModal.tsx`) implements its own:
- `role="dialog"` / `aria-modal` / `aria-labelledby` on the overlay `<div>`
- ESC key listener (`window.addEventListener('keydown', ...)` in a `useEffect`)
- Manual focus to confirm button or prompt input via `setTimeout` in a `useEffect`
- Overlay `onClick={onCancel}` for click-outside-to-close
- **No body scroll-lock** (missing vs. `AccessibleModal`)

The prompt `<label>` at line 90 has no `htmlFor` attribute, so it is not associated with the
`<input>` at line 93–102.

### Target state

Replace the outer `<div>` overlay with `<AccessibleModal>`. `AccessibleModal` already provides
all dialog semantics, focus trap, ESC, overlay click, scroll-lock, focus restoration, and auto-focus.
The manual `useEffect` hooks for ESC and focus can be deleted. The manual ESC `useEffect` and the
focus `useEffect` are both redundant once `AccessibleModal` is in place.

### Decisions

**Why use `AccessibleModal` as the new outermost wrapper rather than just adding scroll-lock?**
The `accessible-modals` spec is explicit: "Every modal dialog SHALL use `AccessibleModal` as its
outermost wrapper." Piecemeal fixes would leave duplicate logic in two places.

**What about the existing `confirmRef` / `inputRef` and the focus-on-open `useEffect`?**
`AccessibleModal` auto-focuses the first focusable element in the panel. When `promptLabel` is
provided, the first focusable element inside the panel will be the prompt `<input>` (it appears
before the action buttons). When there is no prompt, the Cancel button is first. This matches the
desired behaviour: focus goes to the prompt if present, else to the first action button.

However, the desired focus is the *confirm* button (not cancel) when there is no prompt. The
current code does `confirmRef.current?.focus()`. `AccessibleModal` auto-focuses the *first*
focusable element, which is the Cancel button (it appears before Confirm in DOM order).

Decision: **Keep `confirmRef` and the focus-override `useEffect`**, but remove the ESC `useEffect`
and the overlay/stopPropagation pattern. The focus-override works by calling `.focus()` after
`AccessibleModal` has already auto-focused; the `setTimeout(0)` guarantee in both paths means the
manual focus fires after `AccessibleModal`'s own `setTimeout(0)`, so it wins.

Alternative considered: reorder DOM (Confirm before Cancel). Rejected — this changes tab order
for keyboard users who expect Cancel first when navigating forward.

**Removing `handleOverlayKeyDown` (Enter key on overlay)**: This handler fires Enter on the
overlay to confirm when no prompt is present. With `AccessibleModal` the overlay is the dialog
container; key events on the overlay are unrelated to button activation. This handler is removed;
keyboard users activate the focused Confirm button with Space/Enter natively.

### Structure after refactor

```tsx
export function ConfirmModal({ isOpen, ... onConfirm, onCancel }) {
  // Keep: promptValue state, confirmRef, inputRef
  // Keep: reset-on-open useEffect
  // Keep: focus-override useEffect (confirm button or prompt input)
  // Remove: ESC useEffect
  // Remove: handleOverlayKeyDown

  return (
    <AccessibleModal
      isOpen={isOpen}
      onClose={onCancel}
      titleId="confirm-modal-title"
      className="z-[70]"        // preserve existing z-index
    >
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-sm w-full p-6 flex flex-col gap-4">
        <h2 id="confirm-modal-title" ...>{title}</h2>
        <p ...>{message}</p>
        {promptLabel && (
          <div>
            <label htmlFor="confirm-modal-prompt" ...>{promptLabel}</label>
            <input id="confirm-modal-prompt" ref={inputRef} ... />
          </div>
        )}
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel}>...</button>
          <button ref={confirmRef} onClick={...}>...</button>
        </div>
      </div>
    </AccessibleModal>
  );
}
```

`AccessibleModal` accepts a `className` prop that applies to the overlay. The existing z-index
`z-[70]` (higher than the `z-50` default in `AccessibleModal`) is preserved via `className`.

### Prompt label fix

Add `htmlFor="confirm-modal-prompt"` to the `<label>` and `id="confirm-modal-prompt"` to the
`<input>`. Since `ConfirmModal` is a singleton (only one can be open at a time — it is always
mounted conditionally via `isOpen`), a static id is safe.

---

## 2. DeckCardPickerModal — Label the search input

### Current state

`frontend/src/components/DeckCardPickerModal.tsx` line 115–121:
```tsx
<input
  type="text"
  placeholder={t('deckCardPicker.searchPlaceholder')}
  value={search}
  onChange={(e) => setSearch(e.target.value)}
  className="..."
/>
```

No `aria-label`, no `id`, no `<label>` element. The `placeholder` key is
`deckCardPicker.searchPlaceholder` = "Search cards...".

### Target state

Add `aria-label={t('deckCardPicker.searchLabel')}` to the input. A visible `<label>` element is
not added because the modal header already names the context ("Add cards from collection") and the
placeholder provides visual context. Adding a visible label would create visual clutter in the
compact filter bar. `aria-label` is the appropriate mechanism for inputs in toolbars/compact UIs
where a visible label would be redundant.

New i18n key:
- `en.json`: `"deckCardPicker": { ..., "searchLabel": "Search cards" }`
- `es.json`: `"deckCardPicker": { ..., "searchLabel": "Buscar cartas" }`

Note: the existing key `deckCardPicker.searchPlaceholder` ("Search cards...") is kept as-is for
the placeholder. The label uses a slightly shorter form without ellipsis.

---

## 3. JobsBottomBar — aria-live region for job status

### Current state

`frontend/src/components/JobsBottomBar.tsx` has no `aria-live` regions. The `statusText` string
in `ActiveJobEntry` (line 65) updates every second with progress percentage and is computed from
`progress`, `complete`, `summary`. Screen readers receive no announcements when status changes.

### Target state

Add a visually hidden `aria-live="polite"` region to `ActiveJobEntry` that announces meaningful
status changes: job completion (completed / cancelled / failed). Progress percentage is **not**
announced on every tick — that would be extremely noisy. Only terminal state transitions are
announced.

Implementation pattern — visually hidden but readable by screen readers:
```tsx
<span
  className="sr-only"
  aria-live="polite"
  aria-atomic="true"
>
  {isFinished ? statusText : ''}
</span>
```

Using `aria-atomic="true"` ensures the full status string is announced as one unit when it
changes. The region is empty while the job is running, so no intermediate progress ticks are
announced. When `isFinished` flips to `true`, the completed status text is inserted and announced
once.

**Why `polite` not `assertive`?** Job completion is not urgent — the user is likely doing
something else on the page. `assertive` interrupts whatever the screen reader is currently saying,
which would be rude for a background job finishing. `polite` waits for the current utterance to
finish.

**Why not announce progress?** The progress value (`38% — 15/40`) changes every second. Announcing
it would make the app unusable for screen reader users. Screen readers can query the live value
when needed, but we should not push every tick.

**Tailwind `sr-only` class**: already present in the project (Tailwind v4, confirmed by other
usage patterns in the codebase). The class renders as `position: absolute; width: 1px; height: 1px;
overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border-width: 0`.

---

## Data Flow: No changes

All three fixes are pure UI / ARIA attribute additions. No API calls, no state shape changes, no
new hooks, no context changes.

---

## Edge Cases and Risks

### ConfirmModal focus-override timing race

`AccessibleModal`'s auto-focus runs inside `setTimeout(0)`. The `ConfirmModal` focus-override
`useEffect` also uses `setTimeout(0)`. Both are scheduled as microtasks after the same render.
React runs effects in component tree order (parent before child, outer before inner). Since
`AccessibleModal` contains `ConfirmModal`'s content, `AccessibleModal`'s effect runs first, then
`ConfirmModal`'s. The `ConfirmModal` setTimeout fires *after* `AccessibleModal`'s, meaning
`ConfirmModal`'s focus wins. This is the desired outcome. However, this relies on effect ordering
being stable. If this ever becomes an issue, increasing `ConfirmModal`'s timeout to `10ms` would
make the ordering explicit.

### ConfirmModal with both promptLabel and auto-focus

When `promptLabel` is set, `AccessibleModal` would auto-focus the first focusable element, which
is the prompt `<input>` (it appears before buttons in DOM order). The `ConfirmModal` focus
override also focuses `inputRef` in this case. These two focus calls both target the same element
— no conflict.

### Static id "confirm-modal-prompt"

Only one `ConfirmModal` can be open at a time (callers use it as a conditional render based on a
boolean state). The static id `confirm-modal-prompt` is safe. If future code mounts two
`ConfirmModal` instances simultaneously (unlikely), the ids would collide. A `useId()` hook could
be used to generate unique ids if needed — but this is out of scope.

### aria-live region on initial render

The `aria-live` span initialises with empty content. Screen readers do not announce an empty
string change. It only announces when `isFinished` becomes `true` and `statusText` is non-empty.
This is correct.

### JobsBottomBar: multiple concurrent jobs

Each `ActiveJobEntry` renders its own `aria-live` span. If two jobs finish simultaneously,
screen readers queue the announcements. This is acceptable behaviour.

### ConfirmModal prompt key name

The id `confirm-modal-prompt` is added to the DOM only when `promptLabel` is set. The `<label>`
`htmlFor="confirm-modal-prompt"` must always match the input's `id` when both are rendered — this
is guaranteed since both are inside the same conditional block.
