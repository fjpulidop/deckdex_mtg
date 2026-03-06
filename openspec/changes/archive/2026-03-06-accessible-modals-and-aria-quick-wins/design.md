## Context

The DeckDex frontend has 10+ modal dialogs implemented as bare `<div className="fixed inset-0 ...">` overlays. Only `ConfirmModal` has proper accessibility attributes (`role="dialog"`, `aria-modal`, `aria-labelledby`, Escape-to-close, auto-focus). All other modals are invisible to screen readers as dialog contexts and allow focus to escape to content behind them.

Additionally, error messages, icon-only buttons, and form label associations are missing throughout the codebase. The CardTable sortable headers and QuantityCell click-to-edit have no keyboard equivalents.

## Goals / Non-Goals

**Goals:**
- Create a single reusable `AccessibleModal` wrapper that provides full dialog ARIA semantics and focus management, then apply it to all 10 modals.
- Add `role="alert"` to all error containers so screen readers announce them automatically.
- Add `aria-label` to all icon-only buttons.
- Associate all form labels to their inputs via `htmlFor`/`id`.
- Make CardTable sortable headers keyboard-operable with `aria-sort`.
- Make QuantityCell keyboard-operable.

**Non-Goals:**
- `aria-live` regions (separate change)
- Color contrast improvements (requires systematic audit)
- Chart accessibility (data table fallbacks)
- Dropdown/menu keyboard navigation (arrow keys)
- i18n for ActionButtons hardcoded strings

## Decisions

### Decision 1: Build `AccessibleModal` natively, not via a library

**Options considered:**
- A) Use `@headlessui/react` Dialog (battle-tested, but adds a dependency)
- B) Use `focus-trap-react` for the focus trap only (still a dependency)
- C) Implement natively with a `useFocusTrap` hook

**Choice: C — native implementation.**

Rationale: The focus trap logic is ~30 lines and well-understood. Adding a headless UI library to solve one concern adds bundle weight and dependency maintenance overhead. The ConfirmModal already demonstrates the pattern (Escape-to-close, auto-focus) without any library; we extend that pattern to a reusable component.

The focus trap implementation:
1. On mount, collect all focusable elements within the modal panel.
2. Add a `keydown` listener on `document`: when Tab is pressed, cycle within the collected elements; when Escape is pressed, call `onClose`.
3. On unmount, remove the listener and restore focus to the trigger element.

Focusable selector (standard): `button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])`.

### Decision 2: `AccessibleModal` owns the overlay and panel structure

**Options considered:**
- A) Wrapper only around the existing overlay div (each modal keeps its own overlay)
- B) `AccessibleModal` renders the overlay + centers the panel; children are the panel content

**Choice: B — full overlay ownership.**

Rationale: All modals share the same `fixed inset-0 bg-black/50 flex items-center justify-center` overlay pattern. Centralizing it eliminates duplication and ensures `onClick={onClose}` (overlay dismiss) is always present. Children provide only the panel content.

### Decision 3: `aria-labelledby` requires caller to provide a title ID

`AccessibleModal` accepts a `titleId` prop. Each modal passes the `id` of its title heading. This is the same pattern used in ConfirmModal (`aria-labelledby="confirm-modal-title"`).

### Decision 4: Apply `role="alert"` directly on error divs, not a wrapper component

A shared `<ErrorAlert>` component would be cleaner long-term, but for this change we add `role="alert"` inline to existing error divs. This minimizes the diff and avoids premature abstraction. Each div already has the right text content.

## Risks / Trade-offs

- **Focus trap and dynamic content**: If a modal renders async content after mount (e.g., a loading spinner that becomes a form), the focusable element list captured on mount may be stale. Mitigation: Capture focusable elements on each Tab keypress, not just on mount.
- **z-index stacking**: If two modals are open simultaneously (e.g., ConfirmModal on top of DeckDetailModal), the outer modal's Tab listener may conflict. Mitigation: `AccessibleModal` uses `document` listener with `event.stopPropagation()` only on its own container; nested modals will each register their own listener. The innermost modal's z-index (`z-[70]` for ConfirmModal) naturally wins visually. This is an acceptable trade-off given the app's localhost scope.
- **Scroll lock**: Modals currently don't lock body scroll. Adding it in `AccessibleModal` would be a behaviour change but is correct accessibility practice. Decision: add `overflow: hidden` to `document.body` while modal is open, restore on close.
