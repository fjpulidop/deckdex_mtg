# Design: Mobile-Optimized Deck Management

## Context

The deck builder UI consists of four components:

1. `DeckBuilder.tsx` — page with the deck grid and `DeckCardButton` tiles.
2. `DeckDetailModal.tsx` — modal opened per deck; two-column layout (image panel left, card list right); sticky header with action buttons.
3. `DeckCardPickerModal.tsx` — multi-select card picker opened from the detail modal.
4. `DeckImportModal.tsx` — text-paste import modal opened from the detail modal.

All four sit inside `AccessibleModal` which wraps a `div.relative` around an arbitrary `children` panel. The overlay is `fixed inset-0 bg-black/50 flex items-center justify-center p-4`. The panel sizing is currently controlled entirely by the `children` themselves (e.g. `max-w-4xl w-full max-h-[90vh]`).

The goal is to make every piece of this flow touch-friendly on small viewports while leaving the desktop path byte-for-byte identical.

## Goals

- Touch targets: every interactive element reachable with a thumb must be at minimum 44 × 44 px (WCAG 2.5.5 AAA / Apple HIG / Material guidelines).
- Full-screen modals on `< md` (< 768 px): no padding wasted on an overlay backdrop when the viewport itself is small.
- Persistent remove action on mobile: `opacity-0 group-hover` pattern is mouse-only; on mobile the remove button must be always visible or accessible via swipe.
- One-handed operation: primary actions (Add, Export, Import, Delete) must be reachable from a bottom action bar on mobile.
- No new npm dependencies.
- No backend API changes.

## Non-Goals

- Drag-and-drop reordering of cards within a deck (out of scope for this change).
- Native mobile app or PWA manifest changes.
- Swipe-to-navigate between decks.

## Decisions

### 1. Full-screen modal via `AccessibleModal` `fullScreenOnMobile` prop

**Choice:** Add an optional `fullScreenOnMobile?: boolean` prop to `AccessibleModal`. When `true` and the viewport is below the `md` breakpoint, the overlay loses its `p-4 items-center justify-center` centering and the panel gets `w-full h-full rounded-none` so it fills the screen entirely. On `>= md` the component is completely unchanged.

Implementation: use a Tailwind responsive variant approach. The overlay div gets class `sm:p-4 sm:items-center sm:justify-center` (replacing the unconditional ones) and the panel wrapper gets `max-sm:w-full max-sm:h-full max-sm:rounded-none` applied via the `className` prop that callers pass through.

**Why not a separate `FullScreenModal` component:** The accessible behavior (focus trap, scroll lock, Escape key) is already in `AccessibleModal`. Duplicating it would create drift. A single boolean prop is the minimal change.

**Alternatives considered:**
- CSS-only (no prop change, override via className string): fragile—caller would have to fight the overlay's own `p-4 flex` classes from outside. Rejected.
- Separate `MobileModal` component: duplication of focus trap logic. Rejected.

### 2. Sticky bottom action bar in `DeckDetailModal` on mobile

**Choice:** On `< md`, the four action buttons (Export, Import, Add card, Delete deck) are moved out of the header row and into a sticky `bottom-0 safe-area-inset-bottom` bar. The bar is rendered as a `div.md:hidden` sibling to the scrollable content area. On `>= md`, the existing header row with `div.hidden md:flex items-center gap-2 ml-auto` is shown. Both coexist in the DOM; Tailwind visibility classes select the correct one per breakpoint.

**Why not a single row that reflows:** On very narrow screens (390 px) the header already contains title, total value, and mana curve. Adding four more buttons causes wrapping. A dedicated bar keeps the header clean and puts primary actions at thumb reach.

**Tap target size:** each bar button gets `flex-1 flex items-center justify-center gap-1 py-3 text-sm font-medium` giving ≥ 44 px height. Delete button retains its red color to preserve the destructive affordance.

### 3. Swipe-to-remove via `useSwipeToRemove` hook

**Choice:** Implement a custom hook `useSwipeToRemove(onRemove: () => void)` that returns `{ containerProps, revealStyle }`. It attaches `onPointerDown` / `onPointerMove` / `onPointerUp` / `onPointerCancel` to the card row `<li>`. When the pointer starts with `pointerType !== 'mouse'` (i.e. touch or stylus), it tracks horizontal delta. At ≥ 72 px leftward swipe the row translates left via a CSS `transform: translateX(${delta}px)` and a red "Remove" strip (`w-[72px] bg-red-500`) slides in from the right edge. On pointer up: if delta ≥ 72 px, call `onRemove()` and reset; else spring back (set `transition: transform 200ms` and reset to 0). On mouse pointer: hook is a no-op (returns empty props and no style).

This avoids any third-party library and uses only the Pointer Events API (universally supported). The hook does not affect keyboard or mouse users at all.

**Why not long-press-to-reveal:** Long-press is often claimed by the browser (context menu on Android Chrome). Horizontal swipe does not conflict with vertical scroll (the hook starts only if `Math.abs(dx) > Math.abs(dy) * 1.5` after the first 8 px of movement to distinguish scroll from swipe).

**Why not always-visible remove button on mobile:** Always showing the remove button shrinks the card name to about 60% of the row width on narrow screens (the row also shows quantity, name, mana cost, and sometimes a "Set as Commander" button). The swipe pattern is standard mobile UX (iOS Mail, most list apps) and preserves full row width for content.

**Alternative: `sm:block` always-visible remove button:** Simpler to implement. However it creates layout pressure on narrow screens and the mana cost icons may be truncated. Retained as a fallback in the risk section.

### 4. Card row tap height

**Choice:** Change `py-1` to `py-2.5` on `<li>` rows in `DeckDetailModal`. This gives each row ~44 px height on a standard 16 px font size (2 × 10 px padding + ~24 px line height = 44 px). This is a global change (desktop and mobile) — it slightly increases list density on desktop but is not visually objectionable.

**Alternative: `max-sm:py-2.5 py-1`:** Would require touch-only overrides. Accepted as fallback; prefer the simpler always-44px approach since the extra 16 px on desktop rows is negligible.

### 5. DeckCardPickerModal card list rows

**Choice:** Change picker list button `py-2` to `py-3` (48 px). The "Add to Deck" footer button gets `w-full sm:w-auto` so it fills the footer on mobile.

### 6. DeckImportModal — full-screen on mobile

**Choice:** Use `fullScreenOnMobile` on the `AccessibleModal`. The textarea inside gets `flex-1` so it expands to fill available height (already in a `flex flex-col` container — just add `flex-1` to the body div).

### 7. Locale keys for bottom action bar

**Choice:** Add four new keys under `deckDetail.mobileActions` in both `en.json` and `es.json`. Use shorter labels than the header buttons to fit in a row of four: "Add", "Export", "Import", "Delete". The existing longer keys (`deckDetail.addCard`, `deckDetail.export`, etc.) remain untouched for the desktop header.

## Component Change Summary

| Component | Mobile change | Desktop change |
|---|---|---|
| `AccessibleModal` | New `fullScreenOnMobile` prop removes overlay padding and fills screen | None |
| `DeckBuilder.tsx` | `min-h-[100px]` on tiles for safe thumb tap | None |
| `DeckDetailModal.tsx` | Full-screen modal; hide left image panel; sticky bottom bar; swipe-to-remove on rows; always-visible remove on `< md`; increased row tap height | None (header buttons preserved) |
| `DeckCardPickerModal.tsx` | Full-screen modal; rows `py-3`; "Add" button full-width | None |
| `DeckImportModal.tsx` | Full-screen modal; textarea `flex-1` | None |
| `hooks/useSwipeToRemove.ts` | New hook (touch only) | No-op on mouse |
| `locales/en.json`, `es.json` | Four new `deckDetail.mobileActions.*` keys | Same (shared file) |

## Risks and Mitigations

**Swipe conflicts with scroll:** Mitigated by the axis-lock check in `useSwipeToRemove` — the hook only captures horizontal swipes where `|dx| > |dy| × 1.5`. Vertical scroll is never interrupted.

**Swipe fallback if hook is too complex:** If the swipe UX proves unreliable in QA, replace with always-visible remove button on `< sm` (add `sm:opacity-0 sm:group-hover:opacity-100` to the existing button and `opacity-100` unconditionally on very small screens). The task list calls this out explicitly.

**`safe-area-inset-bottom` for notched phones:** The bottom action bar uses `pb-[env(safe-area-inset-bottom,0px)]` via inline style or a Tailwind plugin to avoid being covered by the home indicator on iPhone. This requires no additional library (CSS env variable is standard).

**`AccessibleModal` panel centering on desktop after prop change:** The responsive class approach (`max-sm:w-full max-sm:h-full`) scopes the full-screen behavior below 640 px — it does not affect `md` (768 px) which is the breakpoint the detail modal uses for its own two-column layout. No overlap.

**Focus management in full-screen modal:** `AccessibleModal` already manages focus trap and Escape-to-close. Full-screen modals use the same mechanism — no change needed.
