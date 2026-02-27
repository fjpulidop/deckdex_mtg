## 1. ConfirmModal component (new file)

- [ ] 1.1 Create `frontend/src/components/ConfirmModal.tsx` with the props interface defined in design.md: `isOpen`, `title`, `message`, `confirmLabel`, `cancelLabel`, `destructive`, `promptLabel`, `promptDefault`, `onConfirm`, `onCancel`
- [ ] 1.2 Implement overlay (`fixed inset-0 bg-black/50 z-50`) + centered card (white/dark, rounded, shadow); focus confirm button or text input on open via `useEffect + ref`
- [ ] 1.3 Wire `Escape` key to `onCancel` and `Enter` key (outside text input) to `onConfirm`; in prompt mode pressing Enter in the text input also calls `onConfirm(value)`
- [ ] 1.4 Apply `bg-red-600 hover:bg-red-700` to confirm button when `destructive={true}`, otherwise `bg-blue-600 hover:bg-blue-700`; cancel button always neutral

## 2. Replace window.confirm in CardDetailModal

- [ ] 2.1 In `CardDetailModal.tsx`, add `deleteConfirmOpen` boolean state; replace the `window.confirm(...)` call with setting `deleteConfirmOpen = true`
- [ ] 2.2 Add `<ConfirmModal isOpen={deleteConfirmOpen} title="Delete card" message="Are you sure you want to delete this card? This cannot be undone." destructive confirmLabel="Delete" onConfirm={handleDeleteConfirmed} onCancel={() => setDeleteConfirmOpen(false)} />` to the JSX; move actual delete API call into `handleDeleteConfirmed`

## 3. Replace confirm in DeckDetailModal

- [ ] 3.1 In `DeckDetailModal.tsx`, add `deleteDeckConfirmOpen` boolean state; replace the `confirm(...)` call with setting that state to true
- [ ] 3.2 Add `<ConfirmModal isOpen={deleteDeckConfirmOpen} title="Delete deck" message="Delete this deck? This cannot be undone." destructive confirmLabel="Delete" onConfirm={handleDeleteDeckConfirmed} onCancel={() => setDeleteDeckConfirmOpen(false)} />` and move the delete API call into `handleDeleteDeckConfirmed`

## 4. Replace window.prompt in DeckBuilder

- [ ] 4.1 In `DeckBuilder.tsx`, add `newDeckModalOpen` boolean state; replace the `window.prompt(...)` + immediate `createDeck` call with setting `newDeckModalOpen = true`
- [ ] 4.2 Add `<ConfirmModal isOpen={newDeckModalOpen} title="New Deck" message="Enter a name for your new deck." promptLabel="Deck name" promptDefault="Unnamed Deck" confirmLabel="Create" onConfirm={name => { setNewDeckModalOpen(false); createDeck(name ?? 'Unnamed Deck'); }} onCancel={() => setNewDeckModalOpen(false)} />`

## 5. Scroll-to-top on page change in CardTable

- [ ] 5.1 In `CardTable.tsx`, add `containerRef = useRef<HTMLDivElement>(null)` and attach it to the outermost `<div>`
- [ ] 5.2 Add `useEffect(() => { containerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, [currentPage])` — effect runs after every page change

## 6. Keyboard navigation in CardTable

- [ ] 6.1 Add `focusedIndex` state (`useState(-1)`) and `rowRefs = useRef<(HTMLTableRowElement | null)[]>([])` in `CardTable`
- [ ] 6.2 On each `<tr>`, add `tabIndex={0}`, `ref={el => (rowRefs.current[index] = el)}`, `onFocus={() => setFocusedIndex(index)}`, and focus ring classes `focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-400`
- [ ] 6.3 Add `onKeyDown` handler on `<tbody>`: `ArrowDown` → focus `rowRefs.current[focusedIndex + 1]` (or advance page if on last row and next page exists); `ArrowUp` → focus `rowRefs.current[focusedIndex - 1]` (or go to previous page if on first row); `Enter` → call `onRowClick?.(paginatedCards[focusedIndex])`
- [ ] 6.4 When page changes due to keyboard navigation (ArrowDown on last row / ArrowUp on first row), use a `pendingFocus` ref to record whether to focus first or last row after re-render; resolve it in a `useEffect` that runs when `paginatedCards` changes

## 7. Color filter toggle bar in Filters

- [ ] 7.1 Add `colors: string[]` and `onColorsChange: (colors: string[]) => void` props to `FiltersProps` in `Filters.tsx`
- [ ] 7.2 Add a new row of five toggle buttons (W, U, B, R, G) between the existing dropdowns row and the chips row; each button toggles its letter in/out of the `colors` array; apply color-appropriate active/inactive Tailwind classes per the design palette
- [ ] 7.3 Emit active color chip(s) via the existing `activeChips` prop mechanism: caller should include a chip for each selected color with an `onRemove` that deselects that color; update Dashboard page to pass these chips

## 8. Wire color filter in Dashboard page

- [ ] 8.1 In the Dashboard page (App.tsx or the relevant page file), add `const [colors, setColors] = useState<string[]>([])` and pass `colors` / `onColorsChange={setColors}` to `<Filters>`
- [ ] 8.2 Pass `color_identity: colors.length ? colors.join(',') : undefined` to `api.getCards(...)` (via `useCards` hook or equivalent) and to `useStats(...)` so list and stats stay in sync
- [ ] 8.3 Add one active chip per selected color to the `activeChips` array passed to `<Filters>`: `{ id: 'color-W', label: 'Color: W', onRemove: () => setColors(c => c.filter(x => x !== 'W')) }` (one per color); include these in the existing chip-building logic
- [ ] 8.4 Include `colors` in the `onClearFilters` handler so clearing all filters also resets color selection to `[]`
