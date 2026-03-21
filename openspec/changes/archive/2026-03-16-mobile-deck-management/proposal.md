# Proposal: Mobile-Optimized Deck Management

## Why

MTG players use DeckDex at the LGS (local game store) — away from a laptop, one hand holding cards and one holding a phone. The existing deck builder was designed for desktop: hover-to-preview requires a mouse, the remove button is hidden behind `opacity-0 group-hover:opacity-100`, action buttons are small (`px-3 py-1.5`), and the DeckDetailModal caps at `max-w-4xl` with a rigid two-column layout that collapses poorly below 640 px. The DeckCardPickerModal is fixed at `max-w-2xl max-h-[80vh]` — tolerable on a tablet, cramped on a 390 px phone screen.

This change makes deck editing fully usable on a mobile device without a backend API change, without introducing new dependencies, and without breaking the existing desktop experience.

## What Changes

### DeckBuilder page (deck grid)

- Deck grid switches from `grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5` to `grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5` with `min-h-[100px]` on mobile so tiles remain reachable with a thumb. No structural change to `DeckCardButton`; existing commander-image background logic is preserved.

### DeckDetailModal — responsive two-phase layout

- On mobile (`< md`): modal becomes full-screen (`w-full h-full rounded-none`). The left image panel is hidden; the mana curve and image preview are instead surfaced in a compact top-strip. Action buttons (Export, Import, Add card, Delete) move to a sticky bottom action bar with large tap targets (min 44 px height).
- On desktop (`>= md`): current layout preserved exactly.
- The per-row remove button changes from `opacity-0 group-hover:opacity-100` to always visible on mobile (`sm:opacity-0 sm:group-hover:opacity-100`), sized 44 × 44 px minimum via `p-3`.
- Card rows grow in tap target height on mobile: `py-2.5` instead of `py-1`, giving each row at least 44 px touch area.

### DeckCardPickerModal — full-screen on mobile

- On mobile: modal fills the viewport (`w-full h-full inset-0 rounded-none`); filters collapse into a scrollable row.
- On desktop: current `max-w-2xl max-h-[80vh]` preserved.
- Card list rows grow to minimum 44 px tap height (`py-3`).
- The "Add to Deck" confirm button in the footer grows to full-width on mobile.

### DeckImportModal — full-screen on mobile

- On mobile: modal fills the viewport; textarea grows to fill available space.
- On desktop: current `max-w-lg` preserved.

### Swipe-to-remove on card rows

- A new hook `useSwipeToRemove` implements horizontal pointer/touch tracking on a card row: swipe left ≥ 72 px reveals a red "Remove" strip behind the row; releasing at that threshold triggers the remove action. On desktop (pointer: fine), the hook is a no-op — the existing hover remove button is used instead.
- The hook is attached only in `DeckDetailModal` card rows. It does not affect `DeckCardPickerModal`.

### i18n

- Add keys for the mobile action bar labels: `deckDetail.mobileActions.addCard`, `deckDetail.mobileActions.export`, `deckDetail.mobileActions.import`, `deckDetail.mobileActions.deleteDeck`. These are separate from existing header keys so the mobile bar can use shorter text if needed (e.g. "Add", "Export").

## Capabilities Touched

- **deck-builder-ui** (modified): responsive layout requirements for DeckDetailModal, DeckCardPickerModal, DeckImportModal, card row tap targets, swipe-to-remove.
- **web-dashboard-ui** (advisory): no structural change; Tailwind breakpoint additions are additive.
- No backend capabilities affected.

## Impact

- **Frontend only**: changes are confined to `DeckBuilder.tsx`, `DeckDetailModal.tsx`, `DeckCardPickerModal.tsx`, `DeckImportModal.tsx`, and `AccessibleModal.tsx` (minor tweak to allow full-screen panel variant). A new hook file `hooks/useSwipeToRemove.ts` is added. Locale files `en.json` and `es.json` receive new keys.
- **No API changes**: all mutations already go through `api/client.ts`; no new endpoints needed.
- **No new dependencies**: swipe detection uses the Pointer Events API (already supported in all target browsers).
