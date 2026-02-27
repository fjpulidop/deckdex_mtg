# Design: UX Improvements Dashboard

## 1. Color filter toggle bar

### Location
Inside `Filters.tsx`, added as a new row below the existing search + dropdowns row, above the active-chips row.

### Behavior
- Five toggle buttons, one per MTG color: **W** (White), **U** (Blue), **B** (Black), **R** (Red), **G** (Green).
- Each button is independently toggleable (multi-select). Selecting multiple colors narrows to cards that contain **all** selected colors (AND semantics — matches existing backend `color_identity` param behavior).
- Active state: button gets a color-appropriate highlight (see palette below).
- Clearing all toggles removes the `color_identity` param entirely (shows all colors).
- The selected colors appear as removable chips in the active-chips row (same pattern as rarity/type chips).

### Color palette (Tailwind classes)
| Symbol | Label   | Active bg / text                        | Inactive                              |
|--------|---------|-----------------------------------------|---------------------------------------|
| W      | White   | `bg-yellow-100 text-yellow-800 border-yellow-400` | `bg-gray-100 dark:bg-gray-700`   |
| U      | Blue    | `bg-blue-100 text-blue-800 border-blue-400`       | same                              |
| B      | Black   | `bg-gray-800 text-gray-100 border-gray-500`       | same                              |
| R      | Red     | `bg-red-100 text-red-800 border-red-400`          | same                              |
| G      | Green   | `bg-green-100 text-green-800 border-green-400`    | same                              |

### Props changes to `Filters`
```ts
// New props added to FiltersProps
colors: string[];                            // e.g. ['W','U']
onColorsChange: (colors: string[]) => void;
```

### Hook / page wiring
In the Dashboard page (`App.tsx` or wherever filters are managed):
- `colors` state: `useState<string[]>([])`
- Passed as `color_identity: colors.join(',')` to `api.getCards(...)` and `useStats(...)`.
- Added as active chip: label `Color: W, U`, removed by clearing `colors`.

---

## 2. ConfirmModal component

### Location
New file: `frontend/src/components/ConfirmModal.tsx`

### API
```tsx
interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;   // default "Confirm"
  cancelLabel?: string;    // default "Cancel"
  destructive?: boolean;   // confirm button is red when true
  // Prompt mode (optional)
  promptLabel?: string;    // if set, renders a text input below message
  promptDefault?: string;
  // Callbacks
  onConfirm: (value?: string) => void;  // value = prompt input when in prompt mode
  onCancel: () => void;
}
```

### Behavior
- Renders a centered overlay (`fixed inset-0 bg-black/50 z-50`) with a white/dark card.
- Focuses the confirm button (or text input in prompt mode) on open.
- `Escape` key calls `onCancel`.
- `Enter` key (when not in prompt input) calls `onConfirm`.
- Confirm button uses `bg-red-600` when `destructive={true}`, otherwise `bg-blue-600`.

### Call-sites replaced

| File | Current | Replacement |
|------|---------|-------------|
| `CardDetailModal.tsx:123` | `window.confirm('Are you sure you want to delete this card?')` | `<ConfirmModal destructive title="Delete card" message="This cannot be undone." onConfirm={handleDeleteConfirmed} onCancel={...} />` |
| `DeckDetailModal.tsx:134` | `confirm('Delete this deck? This cannot be undone.')` | same pattern |
| `DeckBuilder.tsx:28` | `window.prompt('Deck name', 'Unnamed Deck')` | `<ConfirmModal title="New Deck" promptLabel="Deck name" promptDefault="Unnamed Deck" onConfirm={name => createDeck(name)} onCancel={...} />` |

---

## 3. Scroll-to-top on page change

### Location
`CardTable.tsx`

### Implementation
Add a `ref` to the outermost wrapper `<div>` of `CardTable`. In a `useEffect` that depends on `currentPage`, call `ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })`.

```tsx
const containerRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  containerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}, [currentPage]);

return <div ref={containerRef} className="bg-white dark:bg-gray-800 ...">
```

This scrolls the table top into view whenever the page changes. `behavior: 'smooth'` keeps it non-jarring.

---

## 4. Keyboard navigation in CardTable

### Target element
The `<tbody>` rows of the card table.

### Implementation
- Each `<tr>` receives `tabIndex={0}` and `role="row"` (already semantically correct inside `<table>`).
- A `ref` array (`rowRefs`) tracks each row DOM node.
- `onKeyDown` on the `<tbody>`:
  - `ArrowDown`: move focus to next row (if exists).
  - `ArrowUp`: move focus to previous row (if exists).
  - `Enter`: call `onRowClick?.(card)` for the currently focused row.
- Focus ring: `focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-inset` on each `<tr>`.
- Clicking a row still works as before.

### Focused-row tracking
```tsx
const [focusedIndex, setFocusedIndex] = useState<number>(-1);
const rowRefs = useRef<(HTMLTableRowElement | null)[]>([]);
```

`onFocus` on each `<tr>` updates `focusedIndex`. `onKeyDown` on `<tbody>` moves focus imperatively via `rowRefs.current[newIndex]?.focus()`.

### Page boundary
When `ArrowDown` is pressed on the last row of the page AND there is a next page, advance to the next page and focus the first row (after re-render via `useEffect`).
When `ArrowUp` is pressed on the first row AND there is a previous page, go to previous page and focus the last row.

### a11y notes
- `<table>` already has implicit `role="grid"` semantics when rows are focusable; no extra ARIA needed.
- Screen readers will announce cell content as the user arrows through rows.
