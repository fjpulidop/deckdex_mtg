# Tasks: Accessibility Pass — Modals and Tables

All tasks are frontend-only. No migrations, no backend changes, no new npm packages.
Execute in order — each task is independently testable and deployable.

---

## Task 1: Wire aria-label to DeckCardPickerModal search input ✓

**File**: `frontend/src/components/DeckCardPickerModal.tsx`

**What**: Add `aria-label={t('deckCardPicker.searchLabel')}` to the `<input>` at line 113.

The i18n key already exists in both locale files:
- `en.json` line 305: `"searchLabel": "Search cards"`
- `es.json`: `"searchLabel": "Buscar cartas"`

No new i18n keys are needed.

**Change**:
```tsx
// Line 113-119 — add aria-label
<input
  type="text"
  aria-label={t('deckCardPicker.searchLabel')}
  placeholder={t('deckCardPicker.searchPlaceholder')}
  value={search}
  onChange={(e) => setSearch(e.target.value)}
  className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
/>
```

**Acceptance criteria**:
- The search input in `DeckCardPickerModal` has `aria-label` that resolves to "Search cards" in EN
  and "Buscar cartas" in ES.
- No visual change.
- Existing placeholder text ("Search cards...") is preserved.

---

## Task 2: Add i18n keys for new labels

**Files**: `frontend/src/locales/en.json`, `frontend/src/locales/es.json`

**What**: Add the new i18n keys needed by Tasks 3–6 to both locale files.

**Keys to add**:

`en.json`:
- Under `"cardDetail"`: add `"lightboxTitle": "Card image: {{name}}"`
- Under `"deckDetail"`: add `"lightboxTitle": "Card image: {{name}}"`
- Under `"deckImport"`: add `"textareaLabel": "Deck list"`
- Under `"settings"`: add `"importFileLabel": "Import collection file (CSV or JSON)"` and
  `"scryfallFileLabel": "Scryfall credentials JSON file"`

`es.json`:
- Under `"cardDetail"`: add `"lightboxTitle": "Imagen de la carta: {{name}}"`
- Under `"deckDetail"`: add `"lightboxTitle": "Imagen de la carta: {{name}}"`
- Under `"deckImport"`: add `"textareaLabel": "Lista del mazo"`
- Under `"settings"`: add `"importFileLabel": "Archivo de importación de colección (CSV o JSON)"`
  and `"scryfallFileLabel": "Archivo JSON de credenciales de Scryfall"`

**Acceptance criteria**:
- `t('cardDetail.lightboxTitle', { name: 'Lightning Bolt' })` returns `"Card image: Lightning Bolt"` in EN.
- `t('deckDetail.lightboxTitle', { name: 'Atraxa' })` returns `"Card image: Atraxa"` in EN.
- `t('deckImport.textareaLabel')` returns `"Deck list"` in EN.
- `t('settings.importFileLabel')` returns `"Import collection file (CSV or JSON)"` in EN.
- `t('settings.scryfallFileLabel')` returns `"Scryfall credentials JSON file"` in EN.
- All five keys have corresponding translations in `es.json`.

---

## Task 3: Replace CardDetailModal image lightbox with AccessibleModal ✓

**File**: `frontend/src/components/CardDetailModal.tsx`

**What**: Replace the raw `<div role="button">` lightbox (lines 442–461) with an `AccessibleModal`
that provides focus trap, ESC, body scroll-lock, and proper dialog semantics.
Also remove the manual `window.addEventListener('keydown', ...)` ESC handler (lines 76–85).

**Change summary**:

Remove the `useEffect` at lines 76–85:
```tsx
// DELETE this entire useEffect:
useEffect(() => {
  if (!imageLightboxOpen) return;
  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      setImageLightboxOpen(false);
    }
  };
  window.addEventListener('keydown', onKeyDown);
  return () => window.removeEventListener('keydown', onKeyDown);
}, [imageLightboxOpen]);
```

Replace the lightbox JSX (lines 442–461):
```tsx
// REPLACE:
{imageLightboxOpen && imageUrl && (
  <div
    className="fixed inset-0 z-[60] ..."
    role="button"
    tabIndex={0}
    aria-label={t('cardDetail.close')}
    onClick={e => { e.stopPropagation(); setImageLightboxOpen(false); }}
    onKeyDown={e => e.key === 'Enter' && setImageLightboxOpen(false)}
  >
    <img src={imageUrl} alt={displayName} className="..." aria-hidden />
  </div>
)}

// WITH:
{imageLightboxOpen && imageUrl && (
  <AccessibleModal
    isOpen={true}
    onClose={() => setImageLightboxOpen(false)}
    titleId="card-detail-lightbox-title"
    className="z-[60] cursor-zoom-out"
  >
    <div
      tabIndex={0}
      role="button"
      aria-label={t('common.close')}
      onClick={() => setImageLightboxOpen(false)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setImageLightboxOpen(false); }}
      className="outline-none p-4"
    >
      <span id="card-detail-lightbox-title" className="sr-only">
        {t('cardDetail.lightboxTitle', { name: displayName })}
      </span>
      <img
        src={imageUrl}
        alt={displayName}
        className="max-w-[488px] max-h-[680px] w-auto h-auto object-contain rounded-lg shadow-2xl"
      />
    </div>
  </AccessibleModal>
)}
```

**Acceptance criteria**:
- Opening the lightbox (clicking the image in view mode) moves focus to the dismissal button
  inside the lightbox panel.
- Pressing Escape while the lightbox is open closes it without closing the parent
  `CardDetailModal`.
- Pressing Tab while the lightbox is open cycles focus within the lightbox (only the one
  focusable element — the button div).
- Clicking anywhere on the overlay or the inner div closes the lightbox.
- Screen reader announces the dialog with its title (e.g., "Card image: Lightning Bolt, dialog").
- The `window.addEventListener` ESC handler is gone — no duplicate ESC handling.
- Visual appearance is unchanged (image centered on dark overlay, same maximum dimensions).

---

## Task 4: Replace DeckDetailModal image lightbox with AccessibleModal ✓

**File**: `frontend/src/components/DeckDetailModal.tsx`

**What**: Same pattern as Task 3. Replace the raw `<div role="button">` lightbox (lines 495–511)
with `AccessibleModal`. Remove the manual `window.addEventListener('keydown', ...)` ESC handler
(lines 250–258).

**Change summary**:

Remove the `useEffect` at lines 250–258:
```tsx
// DELETE this entire useEffect:
useEffect(() => {
  if (!imageLightboxOpen) return;
  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      setImageLightboxOpen(false);
    }
  };
  window.addEventListener('keydown', onKeyDown);
  return () => window.removeEventListener('keydown', onKeyDown);
}, [imageLightboxOpen]);
```

Replace the lightbox JSX (lines 495–511):
```tsx
// REPLACE:
{imageLightboxOpen && bigImageUrl && (
  <div
    className="fixed inset-0 z-[60] ..."
    onClick={() => setImageLightboxOpen(false)}
    role="button"
    tabIndex={0}
    aria-label={t('deckDetail.close')}
    onKeyDown={(e) => e.key === 'Enter' && setImageLightboxOpen(false)}
  >
    <img src={bigImageUrl} alt="Card" className="..." aria-hidden />
  </div>
)}

// WITH:
{imageLightboxOpen && bigImageUrl && (
  <AccessibleModal
    isOpen={true}
    onClose={() => setImageLightboxOpen(false)}
    titleId="deck-detail-lightbox-title"
    className="z-[60] cursor-zoom-out"
  >
    <div
      tabIndex={0}
      role="button"
      aria-label={t('common.close')}
      onClick={() => setImageLightboxOpen(false)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setImageLightboxOpen(false); }}
      className="outline-none p-4"
    >
      <span id="deck-detail-lightbox-title" className="sr-only">
        {t('deckDetail.lightboxTitle', { name: previewCard?.name ?? '' })}
      </span>
      <img
        src={bigImageUrl}
        alt={previewCard?.name ?? t('deckDetail.hoverCard')}
        className="max-w-[90vw] max-h-[90vh] w-auto h-auto object-contain rounded-lg shadow-2xl pointer-events-none"
      />
    </div>
  </AccessibleModal>
)}
```

**Acceptance criteria**:
- Opening the lightbox (clicking the card image in the left panel) moves focus to the dismissal
  button inside the lightbox.
- Pressing Escape closes only the lightbox, not the parent `DeckDetailModal`.
- Tab cycles within the lightbox.
- Clicking the overlay or inner div closes the lightbox.
- Screen reader announces the dialog with its title (e.g., "Card image: Atraxa, dialog").
- Visual appearance is unchanged.

---

## Task 5: Replace ProfileModal crop sub-modal with AccessibleModal ✓

**File**: `frontend/src/components/ProfileModal.tsx`

**What**: Replace the raw `<div role="dialog">` crop sub-modal (lines 217–281) with
`AccessibleModal`. Modify the existing manual ESC `useEffect` (lines 64–74) to use capture phase
so it stops propagation before the outer `AccessibleModal`'s handler fires.

**Change summary**:

Modify the ESC `useEffect` (lines 64–74). Change the event listener to use capture phase (`true`)
so it intercepts ESC before the outer `AccessibleModal`'s bubble-phase handler:
```tsx
// MODIFY lines 64-74:
useEffect(() => {
  if (!cropOpen) return;
  const handler = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      setCropOpen(false);
    }
  };
  // Use capture phase (true) to intercept before AccessibleModal's bubble handler
  document.addEventListener('keydown', handler, true);
  return () => document.removeEventListener('keydown', handler, true);
}, [cropOpen]);
```

Replace the crop sub-modal JSX (lines 217–281):
```tsx
// REPLACE:
{cropOpen && rawImageSrc && (
  <div
    className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70"
    role="dialog"
    aria-modal="true"
    aria-labelledby="crop-modal-title"
  >
    <div className="bg-white dark:bg-gray-800 rounded-xl ...">
      ...
    </div>
  </div>
)}

// WITH:
{cropOpen && rawImageSrc && (
  <AccessibleModal
    isOpen={true}
    onClose={() => setCropOpen(false)}
    titleId="crop-modal-title"
    className="z-[60]"
  >
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 id="crop-modal-title" className="text-base font-semibold text-gray-900 dark:text-white">
          {t('profile.adjustPhoto')}
        </h3>
        <button
          onClick={() => setCropOpen(false)}
          aria-label={t('common.close')}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
      {/* Crop area — unchanged */}
      <div className="relative w-full h-64 rounded-lg overflow-hidden bg-gray-900">
        <Cropper ... />
      </div>
      {/* Zoom slider — unchanged */}
      <div className="flex items-center gap-3 mt-4">
        <span className="text-sm text-gray-500 dark:text-gray-400">🔍</span>
        <input type="range" ... />
      </div>
      {/* Action buttons — unchanged */}
      <div className="flex gap-3 justify-end mt-4">
        <button onClick={() => setCropOpen(false)} ...>{t('profile.cancel')}</button>
        <button onClick={handleApplyCrop} ...>{t('profile.apply')}</button>
      </div>
    </div>
  </AccessibleModal>
)}
```

**Acceptance criteria**:
- Opening the crop modal (clicking the avatar) moves focus to the first focusable element inside
  the crop panel (the close button).
- Pressing Escape while the crop modal is open closes only the crop modal; the parent
  `ProfileModal` remains open.
- Tab cycles within the crop modal (close button, range slider, Cancel button, Apply button).
- Clicking the overlay background closes the crop modal.
- The outer `ProfileModal`'s scroll-lock, focus trap, and ESC handling are unaffected while the
  crop modal is not open.
- Visual appearance of the crop dialog is unchanged.

---

## Task 6: Add label to DeckImportModal textarea ✓

**File**: `frontend/src/components/DeckImportModal.tsx`

**What**: Add a visible `<label>` element associated with the textarea via `htmlFor` / `id`.

**Change**: In the `result === null` branch (approximately line 50–65), add:
```tsx
// BEFORE the textarea, add a label:
<label
  htmlFor="deck-import-textarea"
  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
>
  {t('deckImport.textareaLabel')}
</label>
<textarea
  id="deck-import-textarea"
  className="w-full h-48 rounded-lg border ..."
  placeholder={t('deckImport.placeholder')}
  value={text}
  onChange={(e) => setText(e.target.value)}
  disabled={mutation.isPending}
  autoFocus
/>
```

**Acceptance criteria**:
- The textarea is announced by screen readers with the label "Deck list" (EN) / "Lista del mazo"
  (ES) when focused.
- The label is visible above the textarea.
- The `autoFocus` and placeholder behaviour are unchanged.
- No visual regression to the modal layout.
- Requires Task 2 to be complete first (for the i18n key).

---

## Task 7: Add labels to SettingsModal file inputs ✓

**File**: `frontend/src/components/SettingsModal.tsx`

**What**: Add visually-hidden `<label>` elements for both `<input type="file">` elements:
1. The Scryfall credentials file input (line ~128, inside `<div className="flex flex-wrap ...">`)
2. The collection import file input (line ~216, inside the `importCollection` section)

**Change for Scryfall file input** (line ~128):
```tsx
// Add before the file input:
<label htmlFor="settings-scryfall-file" className="sr-only">
  {t('settings.scryfallFileLabel')}
</label>
<input
  id="settings-scryfall-file"
  type="file"
  accept=".json"
  onChange={handleScryfallFileChange}
  className="text-sm text-gray-500 ..."
/>
```

**Change for import file input** (line ~216):
```tsx
// Add before the file input:
<label htmlFor="settings-import-file" className="sr-only">
  {t('settings.importFileLabel')}
</label>
<input
  id="settings-import-file"
  type="file"
  accept=".csv,.json"
  onChange={handleFileChange}
  disabled={importFileLoading}
  className="block w-full ..."
/>
```

**Acceptance criteria**:
- The Scryfall file input is announced as "Scryfall credentials JSON file" (EN) when focused.
- The collection import file input is announced as "Import collection file (CSV or JSON)" (EN)
  when focused.
- Labels are visually hidden (`sr-only`) — no layout change.
- File inputs retain all existing functionality (change handlers, disabled state, etc.).
- Requires Task 2 to be complete first (for the i18n keys).

---

## Task 8: Write tests for the refactored lightboxes and crop modal ✓

**File**: Create or extend `frontend/src/components/__tests__/` — specifically tests for
`CardDetailModal`, `DeckDetailModal`, and `ProfileModal`.

**What**: Verify the accessibility of the three refactored components.

**Test cases to add**:

For `CardDetailModal` lightbox:
- Renders `role="dialog"` on the lightbox overlay when open.
- Renders `aria-labelledby` pointing to the visually hidden title span.
- Renders the title span with card name interpolated.
- The inner div has `role="button"` and `aria-label={t('common.close')}`.
- Closes when `onClose` prop is called (simulate Escape via `AccessibleModal` — or just check the
  `onClose` prop is passed correctly to `AccessibleModal`).

For `DeckDetailModal` lightbox:
- Same set of assertions as `CardDetailModal` lightbox.

For `ProfileModal` crop sub-modal:
- When `cropOpen` is true, renders `role="dialog"`.
- The crop dialog has `aria-labelledby="crop-modal-title"`.

Note: Do NOT use `scope="module"` for any test fixtures that involve mocked dependencies —
use `scope="function"` per project convention. All tests expect HTTP 400 for validation errors
(not 422). Use `vi.mock` / `vitest` mocking patterns consistent with the existing
`frontend/src/components/__tests__/CardTable.test.tsx`.

**Acceptance criteria**:
- All new tests pass with `npm run test` (or equivalent vitest invocation).
- No existing tests are broken.
- Test fixtures use `scope="function"` (not `scope="module"`).
