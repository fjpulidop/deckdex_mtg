# Context Bundle: Mobile-Optimized Deck Management

This file collects the exact code segments and structural facts a developer needs to implement this change without reading the full file on every task.

---

## File inventory

| File | Role | Change type |
|---|---|---|
| `frontend/src/components/AccessibleModal.tsx` | Modal wrapper with focus trap | Minor: add `fullScreenOnMobile` prop |
| `frontend/src/pages/DeckBuilder.tsx` | Deck grid page | Minor: verify tile min-height |
| `frontend/src/components/DeckDetailModal.tsx` | Main deck modal | Significant: layout, action bar, row styles |
| `frontend/src/components/DeckCardPickerModal.tsx` | Card picker modal | Minor: full-screen, row height, button width |
| `frontend/src/components/DeckImportModal.tsx` | Text import modal | Minor: full-screen, textarea flex |
| `frontend/src/hooks/useSwipeToRemove.ts` | Swipe gesture hook | New file |
| `frontend/src/locales/en.json` | English strings | Add 4 keys |
| `frontend/src/locales/es.json` | Spanish strings | Add 4 keys |
| `frontend/src/hooks/__tests__/useSwipeToRemove.test.ts` | Hook unit tests | New file |
| `frontend/src/components/__tests__/DeckDetailModal.test.tsx` | Existing test | Add one assertion |

---

## Key existing code segments

### AccessibleModal — current overlay and panel structure

```tsx
// frontend/src/components/AccessibleModal.tsx  lines 138–164
return (
  <div
    className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 ${className ?? ''}`}
    role="dialog"
    aria-modal="true"
    aria-labelledby={titleId}
    onClick={onClose}
  >
    <div
      ref={panelRef}
      className="relative"
      onClick={e => e.stopPropagation()}
    >
      {showCloseButton && ( ... )}
      {children}
    </div>
  </div>
);
```

**What to change:** When `fullScreenOnMobile` is true, replace the overlay's static `flex items-center justify-center p-4` with responsive classes `sm:flex sm:items-center sm:justify-center sm:p-4`, and add `max-sm:w-full max-sm:h-[100dvh]` to the inner panel `div.relative`.

### AccessibleModal — props interface

```tsx
// lines 5–17
interface AccessibleModalProps {
  isOpen: boolean;
  onClose: () => void;
  titleId: string;
  children: ReactNode;
  className?: string;
  showCloseButton?: boolean;
}
```

**What to add:** `fullScreenOnMobile?: boolean` (default `false`).

---

### DeckDetailModal — panel div (root of modal content)

```tsx
// line 266
<div
  className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden"
>
```

**What to change:** Add `max-sm:rounded-none max-sm:max-w-none max-sm:max-h-none max-sm:h-full` so on mobile the panel fills the screen. Also pass `fullScreenOnMobile` to the outer `AccessibleModal`.

### DeckDetailModal — left image panel

```tsx
// line 383
<div className="w-64 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 flex flex-col items-center justify-start bg-gray-50 dark:bg-gray-900/50 p-4 overflow-visible">
```

**What to change:** Add `hidden md:flex` to hide on mobile.

### DeckDetailModal — header action buttons row

```tsx
// line 349
<div className="flex items-center gap-2 shrink-0 ml-auto">
  {/* Export, Import, Add card, Delete buttons */}
</div>
```

**What to change:** Add `hidden md:flex` so this block is hidden on mobile (replaced by the sticky bar).

### DeckDetailModal — card row `<li>` (current)

```tsx
// line 430–432
<li
  key={card.id}
  onMouseEnter={() => card.id != null && setHoverCardId(card.id)}
  onMouseLeave={() => setHoverCardId(null)}
  className="flex items-center gap-2 py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700/50 group"
>
```

**What to change:** `py-1` → `py-2.5`. Add `relative overflow-hidden` for swipe strip positioning. Wrap content in an inner `div` that receives the swipe `transform` style. Extract each `<li>` to a `DeckCardRow` local component to allow per-row hook invocation.

### DeckDetailModal — remove button (current)

```tsx
// line 459–471
<button
  type="button"
  onClick={(e) => {
    e.stopPropagation();
    if (card.id != null) handleRemoveCard(card.id);
  }}
  className="opacity-0 group-hover:opacity-100 text-red-600 hover:text-red-700 dark:text-red-400 p-1 rounded flex-shrink-0"
  aria-label={`Remove ${card.name}`}
>
```

**What to change:** Replace `opacity-0 group-hover:opacity-100 ... p-1` with `sm:opacity-0 sm:group-hover:opacity-100 ... p-3 sm:p-1`.

### DeckDetailModal — flex body (main content area below header)

```tsx
// line 382
<div className="flex flex-1 overflow-hidden min-h-0">
```

**What to add:** The mobile sticky action bar is inserted as a child of the outer `flex flex-col` panel, after (not inside) this div. Structure becomes:

```tsx
<div className="flex flex-col overflow-hidden h-full">
  {/* header */}
  <div className="flex flex-1 overflow-hidden min-h-0">
    {/* image panel - hidden md:flex */}
    {/* card list */}
  </div>
  {/* mobile action bar - md:hidden */}
  <div className="md:hidden sticky bottom-0 ...">
    {/* Add, Export, Import, Delete */}
  </div>
</div>
```

---

### DeckCardPickerModal — panel div (current)

```tsx
// line 98–99
<div
  className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col overflow-hidden"
>
```

**What to change:** Add `max-sm:rounded-none max-sm:max-w-none max-sm:max-h-none max-sm:h-full max-sm:w-full`. Also pass `fullScreenOnMobile` to `AccessibleModal`.

### DeckCardPickerModal — card list button height (current)

```tsx
// line 198
className={`w-full flex items-center gap-2 py-2 px-3 rounded text-left ...`}
```

**What to change:** `py-2` → `py-3`.

### DeckCardPickerModal — "Add to Deck" footer button (current)

```tsx
// line 228–234
<button
  type="button"
  onClick={handleAdd}
  disabled={selected.size === 0 || addPending}
  className="px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-indigo-500 dark:hover:bg-indigo-600"
>
```

**What to change:** Add `w-full sm:w-auto` to the className.

---

### DeckImportModal — panel div (current)

```tsx
// line 38–39
<div
  className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg flex flex-col overflow-hidden"
>
```

**What to change:** Add `max-sm:rounded-none max-sm:max-w-none max-sm:h-full`. Pass `fullScreenOnMobile` to `AccessibleModal`.

### DeckImportModal — body div (current)

```tsx
// line 48
<div className="px-6 py-4 flex flex-col gap-4">
```

**What to change:** Add `flex-1` so the body grows to fill available height on full-screen modal.

### DeckImportModal — textarea height (current)

```tsx
// line 58
className="w-full h-48 rounded-lg ..."
```

**What to change:** `h-48` → `sm:h-48 flex-1 min-h-[12rem]` so the textarea fills remaining space on mobile but stays at its current size on desktop.

---

## New file: `useSwipeToRemove` hook

**Location:** `frontend/src/hooks/useSwipeToRemove.ts`

```typescript
import { useState, useRef, useCallback } from 'react';

const SWIPE_THRESHOLD = 72;
const AXIS_LOCK_RATIO = 1.5;
const CAPTURE_START_PX = 8;

export function useSwipeToRemove(onRemove: () => void) {
  const [translateX, setTranslateX] = useState(0);
  const [animatingBack, setAnimatingBack] = useState(false);
  const startX = useRef(0);
  const startY = useRef(0);
  const tracking = useRef(false);
  const axisLocked = useRef<'horizontal' | 'vertical' | null>(null);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    if (e.pointerType === 'mouse') return;
    startX.current = e.clientX;
    startY.current = e.clientY;
    tracking.current = true;
    axisLocked.current = null;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!tracking.current) return;
    const dx = e.clientX - startX.current;
    const dy = e.clientY - startY.current;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (axisLocked.current === null && dist > CAPTURE_START_PX) {
      axisLocked.current =
        Math.abs(dx) > Math.abs(dy) * AXIS_LOCK_RATIO ? 'horizontal' : 'vertical';
    }

    if (axisLocked.current !== 'horizontal') return;

    if (dx < 0) {
      setAnimatingBack(false);
      setTranslateX(Math.max(dx, -SWIPE_THRESHOLD));
    }
  }, []);

  const onPointerUp = useCallback(() => {
    if (!tracking.current) return;
    tracking.current = false;

    setTranslateX((prev) => {
      if (prev <= -SWIPE_THRESHOLD) {
        onRemove();
        return 0;
      }
      setAnimatingBack(true);
      setTimeout(() => setAnimatingBack(false), 200);
      return 0;
    });
  }, [onRemove]);

  const onPointerCancel = useCallback(() => {
    tracking.current = false;
    setAnimatingBack(true);
    setTranslateX(0);
    setTimeout(() => setAnimatingBack(false), 200);
  }, []);

  return {
    containerProps: { onPointerDown, onPointerMove, onPointerUp, onPointerCancel },
    translateX,
    animatingBack,
    isRevealed: translateX <= -36,
  };
}
```

---

## Locale keys to add

### `en.json` — under `"deckDetail"` object

```json
"mobileActions": {
  "addCard": "Add",
  "export": "Export",
  "import": "Import",
  "deleteDeck": "Delete"
}
```

### `es.json` — under `"deckDetail"` object

```json
"mobileActions": {
  "addCard": "Añadir",
  "export": "Exportar",
  "import": "Importar",
  "deleteDeck": "Eliminar"
}
```

---

## Breakpoints reference (Tailwind defaults)

| Prefix | Min width |
|---|---|
| `sm:` | 640 px |
| `md:` | 768 px |

The image panel and desktop header buttons hide at `< md` (768 px). The remove button always-visible behaviour activates at `< sm` (640 px). Full-screen modals via `max-sm:` activate at `< sm` (640 px). These two thresholds are intentionally different: the sticky bar is a layout concern (md), while the remove button visibility is a touch-device concern (sm).

---

## Existing test file to extend

`frontend/src/components/__tests__/DeckDetailModal.test.tsx` — this file already exists. The task requires adding one test; do not modify or remove existing tests.
