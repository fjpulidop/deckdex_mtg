# Design: Accessibility Pass — Modals and Tables

## Impact Analysis

| File | Change | Reason |
|---|---|---|
| `frontend/src/components/DeckCardPickerModal.tsx` | Small fix | Add `aria-label` to search input (line 113) |
| `frontend/src/components/ProfileModal.tsx` | Refactor | Replace raw crop sub-modal div with `AccessibleModal` |
| `frontend/src/components/CardDetailModal.tsx` | Refactor | Replace image lightbox `role="button"` div with `AccessibleModal` |
| `frontend/src/components/DeckDetailModal.tsx` | Refactor | Replace image lightbox `role="button"` div with `AccessibleModal` |
| `frontend/src/components/DeckImportModal.tsx` | Small fix | Add `<label>` + `id` to textarea |
| `frontend/src/components/SettingsModal.tsx` | Small fix | Add visible label to collection import file input |
| `frontend/src/locales/en.json` | Addition | New i18n keys for new labels |
| `frontend/src/locales/es.json` | Addition | New i18n keys for new labels |

No backend files, no migrations, no new npm packages.

---

## 1. DeckCardPickerModal — Add aria-label to search input

### Current state

`frontend/src/components/DeckCardPickerModal.tsx` lines 113–119:

```tsx
<input
  type="text"
  placeholder={t('deckCardPicker.searchPlaceholder')}
  value={search}
  onChange={(e) => setSearch(e.target.value)}
  className="w-full border ..."
/>
```

No `aria-label`, no `id`, no associated `<label>`. The i18n key
`deckCardPicker.searchLabel` already exists in both `en.json` (line 305 = `"Search cards"`) and
`es.json` from the previous change; it just was never wired to the element.

### Target state

Add `aria-label={t('deckCardPicker.searchLabel')}` to the input. No other changes.

No new i18n keys are needed — both locale files already have the key.

### Decision

A visible `<label>` element is not added because the modal header already contextualises the
UI ("Add cards from collection") and the filter bar is compact. `aria-label` is the correct
WCAG technique for toolbar inputs where a visible label would be redundant (WCAG technique
ARIA14).

---

## 2. ProfileModal — Replace crop sub-modal with AccessibleModal

### Current state

`frontend/src/components/ProfileModal.tsx` lines 217–281 render a crop dialog as:

```tsx
{cropOpen && rawImageSrc && (
  <div
    className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70"
    role="dialog"
    aria-modal="true"
    aria-labelledby="crop-modal-title"
  >
    ...
  </div>
)}
```

Problems:
- No focus trap — Tab moves freely to elements behind the overlay.
- No body scroll-lock — `AccessibleModal` for the outer profile modal still has the lock, but
  when `cropOpen` is true the focus trap of the outer modal remains active and will interfere,
  making Tab cycle within the profile modal (not the crop modal).
- ESC handling is a manual `document.addEventListener` (lines 64–74) that calls
  `e.stopPropagation()` to prevent the outer `AccessibleModal` from also closing.
- No auto-focus of first element on open.

### Target state

Replace the raw `<div>` overlay with `<AccessibleModal>`:

```tsx
{cropOpen && rawImageSrc && (
  <AccessibleModal
    isOpen={cropOpen}
    onClose={() => setCropOpen(false)}
    titleId="crop-modal-title"
    className="z-[60]"
  >
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 id="crop-modal-title" ...>{t('profile.adjustPhoto')}</h3>
        <button onClick={() => setCropOpen(false)} aria-label={t('common.close')}>
          <X className="w-5 h-5" />
        </button>
      </div>
      {/* crop area, zoom slider, action buttons — unchanged */}
    </div>
  </AccessibleModal>
)}
```

The manual ESC `useEffect` (lines 64–74 in `ProfileModal.tsx`) is removed — `AccessibleModal`
handles ESC natively.

### Decision: z-index layering

The outer `ProfileModal` uses `AccessibleModal` with `className="z-50"`. The crop sub-modal
must render above it, so `className="z-[60]"` is used — matching the existing value already set
on the raw div (`z-[60]`). No change to layering.

### Decision: nested AccessibleModal focus trap interaction

When `cropOpen` is true, two `AccessibleModal` instances are simultaneously mounted:
- The outer profile modal at `z-50`
- The crop modal at `z-[60]`

Both register `document` keydown listeners for Tab and ESC. The crop modal renders above the
profile modal in the DOM (it is rendered after, because it is conditionally rendered inside the
fragment returned by `ProfileModal`). Both focus traps run, but since the crop modal auto-focuses
its first element, `document.activeElement` is inside the crop modal. The profile modal's Tab
trap only wraps focus when the user is on the last element *of the profile modal's panel*, but
since focus is inside the crop modal's panel, the profile modal's Tab handler is effectively
inert (it calls `panel.querySelectorAll(...)` on the profile modal panel and checks
`document.activeElement === last` — which is false because focus is in the crop panel).

This is the same pattern already used in `DeckDetailModal` (which renders `ConfirmModal`,
`DeckCardPickerModal`, `DeckImportModal`, and `CardDetailModal` as siblings — each is an
`AccessibleModal` above the outer `z-50`). The pattern is proven to work correctly.

### Decision: `AccessibleModal` `isOpen` prop

`AccessibleModal` renders nothing when `isOpen` is false and mounts the DOM when `isOpen` is
true. The crop modal already uses conditional rendering (`cropOpen && rawImageSrc`). Pass
`isOpen={true}` (since the render is gated by the conditional), matching the pattern used in
`CardFormModal`, `CardDetailModal`, `ProfileModal` outer, etc.

Alternatively, pass `isOpen={cropOpen}` and remove the outer conditional. Either approach is
correct. Keep the outer conditional for clarity — `isOpen={true}` inside it.

---

## 3. CardDetailModal — Replace image lightbox with AccessibleModal

### Current state

`frontend/src/components/CardDetailModal.tsx` lines 442–461:

```tsx
{imageLightboxOpen && imageUrl && (
  <div
    className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 cursor-zoom-out p-4"
    onClick={e => { e.stopPropagation(); setImageLightboxOpen(false); }}
    role="button"
    tabIndex={0}
    aria-label={t('cardDetail.close')}
    onKeyDown={e => e.key === 'Enter' && setImageLightboxOpen(false)}
  >
    <img src={imageUrl} alt={displayName} className="..." aria-hidden />
  </div>
)}
```

Problems:
- `role="button"` on a full-screen fixed overlay is semantically wrong. A lightbox *is* a dialog.
- No focus trap — Tab moves freely to elements behind the overlay.
- Screen reader cannot identify it as a dialog.
- The image has `aria-hidden` which is correct for a decorative enlargement, but the containing
  element has `aria-label={t('cardDetail.close')}` — this mis-identifies the entire structure as
  a "Close" button.
- There is a manual `window.addEventListener('keydown', ...)` for ESC (lines 76–85) that uses
  `e.stopPropagation()`.

### Target state

Replace the `<div role="button">` with `<AccessibleModal>`:

```tsx
{imageLightboxOpen && imageUrl && (
  <AccessibleModal
    isOpen={true}
    onClose={() => setImageLightboxOpen(false)}
    titleId="card-detail-lightbox-title"
    className="z-[60] cursor-zoom-out"
  >
    <div onClick={() => setImageLightboxOpen(false)}>
      <span id="card-detail-lightbox-title" className="sr-only">
        {t('cardDetail.lightboxTitle', { name: displayName })}
      </span>
      <img
        src={imageUrl}
        alt={displayName}
        className="max-w-[488px] max-h-[680px] w-auto h-auto object-contain rounded-lg shadow-2xl pointer-events-none"
      />
    </div>
  </AccessibleModal>
)}
```

The manual ESC `window.addEventListener` (lines 76–85 in `CardDetailModal.tsx`) is removed.

The visually hidden `<span>` provides a title for `aria-labelledby` while not cluttering the
visual display. The entire panel `<div>` has an `onClick` to close (click-anywhere-to-close is
a standard lightbox pattern). `AccessibleModal`'s overlay `onClick={onClose}` also fires, so
clicking the background closes the lightbox without needing the panel click handler — but the
inner click handler is kept for clarity.

New i18n key needed:
- `en.json`: `"cardDetail": { ..., "lightboxTitle": "Card image: {{name}}" }`
- `es.json`: `"cardDetail": { ..., "lightboxTitle": "Imagen de la carta: {{name}}" }`

### Decision: pointer-events and cursor

The existing `cursor-zoom-out` class is moved to the `AccessibleModal` overlay via `className`.
`AccessibleModal` forwards `className` to the fixed overlay div, so this works correctly. The
image retains `pointer-events-none`.

### Decision: `aria-hidden` on image

The image `aria-hidden` is removed. The image is the primary content of the dialog and should be
described by its `alt` text. The `sr-only` title span gives the dialog its accessible name;
the image `alt` provides its description. This is correct ARIA practice.

---

## 4. DeckDetailModal — Replace image lightbox with AccessibleModal

### Current state

`frontend/src/components/DeckDetailModal.tsx` lines 495–511:

```tsx
{imageLightboxOpen && bigImageUrl && (
  <div
    className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 cursor-zoom-out p-4"
    onClick={() => setImageLightboxOpen(false)}
    role="button"
    tabIndex={0}
    aria-label={t('deckDetail.close')}
    onKeyDown={(e) => e.key === 'Enter' && setImageLightboxOpen(false)}
  >
    <img
      src={bigImageUrl}
      alt="Card"
      className="max-w-[90vw] max-h-[90vh] ..."
      aria-hidden
    />
  </div>
)}
```

Same issues as `CardDetailModal` lightbox. Manual `window.addEventListener` ESC handler at lines
250–258.

### Target state

Same pattern as `CardDetailModal` lightbox refactor:

```tsx
{imageLightboxOpen && bigImageUrl && (
  <AccessibleModal
    isOpen={true}
    onClose={() => setImageLightboxOpen(false)}
    titleId="deck-detail-lightbox-title"
    className="z-[60] cursor-zoom-out"
  >
    <div onClick={() => setImageLightboxOpen(false)}>
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

The manual ESC `window.addEventListener` (lines 250–258 in `DeckDetailModal.tsx`) is removed.

New i18n key needed:
- `en.json`: `"deckDetail": { ..., "lightboxTitle": "Card image: {{name}}" }`
- `es.json`: `"deckDetail": { ..., "lightboxTitle": "Imagen de la carta: {{name}}" }`

---

## 5. DeckImportModal — Add label to textarea

### Current state

`frontend/src/components/DeckImportModal.tsx` lines 52–58:

```tsx
<textarea
  className="w-full h-48 ..."
  placeholder={t('deckImport.placeholder')}
  value={text}
  onChange={(e) => setText(e.target.value)}
  disabled={mutation.isPending}
  autoFocus
/>
```

No `id`, no `aria-label`, no associated `<label>`. The placeholder is a multi-line example text
(see `en.json` line 157).

### Target state

Add an `id` to the textarea and a `<label>` element above it. The label can be visually hidden
(`sr-only`) since the modal header `h2` already contextualises the purpose. Using a visible label
is also acceptable — in this case, it can serve as a brief instruction ("Paste your deck list:")
which aids all users, not only screen reader users. Using a visible label is preferred.

```tsx
<label
  htmlFor="deck-import-textarea"
  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
>
  {t('deckImport.textareaLabel')}
</label>
<textarea
  id="deck-import-textarea"
  className="w-full h-48 ..."
  ...
/>
```

New i18n keys:
- `en.json`: `"deckImport": { ..., "textareaLabel": "Deck list" }`
- `es.json`: `"deckImport": { ..., "textareaLabel": "Lista del mazo" }`

### Decision: visible vs sr-only label

A visible label is chosen over `sr-only`. The modal panel has vertical space above the textarea.
"Deck list" as a label serves as a heading for the field — it helps sighted users scanning the
modal too. The placeholder still provides format hints.

---

## 6. SettingsModal — Add label to collection import file input

### Current state

`frontend/src/components/SettingsModal.tsx` lines 208–222: a `<section>` with heading
`settings.importCollection`. The `<input type="file">` at line 216 has no `aria-label` and no
associated `<label>`.

The Scryfall file input (line 128) shares the same problem but is inside a group with a visible
`<h3>` heading and a descriptive paragraph — its context is clear, though a label is still
preferred. The collection import file input at line 216 is more isolated.

### Target state

Add a `<label>` element wrapping or associated with the file input:

```tsx
<label
  htmlFor="settings-import-file"
  className="sr-only"
>
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

Also add a `<label>` to the Scryfall file input (`<input type="file" accept=".json">` at line
128) for completeness:

```tsx
<label htmlFor="settings-scryfall-file" className="sr-only">
  {t('settings.scryfallFileLabel')}
</label>
<input
  id="settings-scryfall-file"
  type="file"
  accept=".json"
  onChange={handleScryfallFileChange}
  className="..."
/>
```

New i18n keys:
- `en.json`: `"settings": { ..., "importFileLabel": "Import collection file (CSV or JSON)", "scryfallFileLabel": "Scryfall credentials JSON file" }`
- `es.json`: corresponding translations

### Decision: sr-only vs visible label

`sr-only` is used here because the section already has an `<h3>` heading and a descriptive
`<p>` that provide visual context. A visible label would be redundant. `sr-only` keeps the visual
design unchanged while satisfying WCAG 1.3.1.

---

## Data Flow: No changes

All six fixes are pure UI / ARIA attribute additions and structural refactors within existing
components. No API calls, no state shape changes, no new hooks, no context changes, no backend
changes.

---

## i18n Summary

New keys needed (both locales):

| Key path | EN value | ES value |
|---|---|---|
| `cardDetail.lightboxTitle` | `"Card image: {{name}}"` | `"Imagen de la carta: {{name}}"` |
| `deckDetail.lightboxTitle` | `"Card image: {{name}}"` | `"Imagen de la carta: {{name}}"` |
| `deckImport.textareaLabel` | `"Deck list"` | `"Lista del mazo"` |
| `settings.importFileLabel` | `"Import collection file (CSV or JSON)"` | `"Archivo de importación de colección (CSV o JSON)"` |
| `settings.scryfallFileLabel` | `"Scryfall credentials JSON file"` | `"Archivo JSON de credenciales de Scryfall"` |

Existing keys that are already present and require no changes:
- `deckCardPicker.searchLabel` — already in both locales; fix is just wiring it to the input.

---

## Edge Cases and Risks

### ProfileModal crop modal: nested focus trap ordering

As described in section 2, two `AccessibleModal` instances run simultaneously when `cropOpen` is
true. Both register `document` keydown Tab handlers. The outer profile modal's handler checks
`document.activeElement === first/last` where first/last are elements within the profile panel.
Since focus is in the crop panel after auto-focus, these conditions are false and the outer
handler is inert. ESC on the inner modal calls `onClose` of the inner (`setCropOpen(false)`);
since `AccessibleModal` calls `e.key === 'Escape'` and returns early without
`e.stopPropagation()`, the document event will bubble and the outer modal's handler also runs.
The outer modal will call its `onClose` as well, which is `onClose` of `ProfileModal` — closing
the entire profile modal.

**Resolution**: ESC on the crop sub-modal should close only the crop modal, not the outer profile
modal. To preserve this behaviour, keep a manual `document.addEventListener` for ESC with
`e.stopPropagation()` **and also** use `AccessibleModal` for focus trap and focus management —
but disable `AccessibleModal`'s own ESC by patching its `onClose` to be a no-op and handling ESC
ourselves, OR use `AccessibleModal`'s `onClose` as `() => setCropOpen(false)` and rely on event
propagation being blocked at the inner handler.

Actually, the simplest resolution: `AccessibleModal`'s ESC handler calls `onClose()` after
checking `e.key === 'Escape'` — it does NOT call `e.stopPropagation()` or `e.preventDefault()`.
This means the event propagates to the outer modal's handler, which also fires.

To prevent the outer modal from closing when the inner modal's ESC fires, we have two options:

**Option A**: Keep the manual `stopPropagation` ESC handler from the original code (lines 64–74)
alongside `AccessibleModal`. Remove only the manual ESC handler and let `AccessibleModal` handle
ESC — but this means both modals close on ESC. This is arguably acceptable UX: pressing ESC
dismisses the crop sub-dialog and returns to the profile modal, then another ESC closes the
profile modal. But the original code explicitly stopped propagation to prevent this.

**Option B**: Modify `AccessibleModal` to accept a prop `stopPropagationOnEsc?: boolean` and use
it in the crop modal. This adds complexity to `AccessibleModal`.

**Option C**: Keep the manual `stopPropagation` `useEffect` for ESC (lines 64–74) alongside
`AccessibleModal`. This makes ESC propagation stop before the outer modal sees it. The manual ESC
handler fires first (because it was registered first on `document`), calls `e.stopPropagation()`,
and `setCropOpen(false)`. The outer modal's `AccessibleModal` handler never fires. This is exactly
what the current code does — we just add `AccessibleModal` for focus trap/focus restoration on
top, keeping the manual ESC handler.

**Chosen approach: Option C**. Keep the existing manual `useEffect` for ESC with
`stopPropagation`, and also add `AccessibleModal` wrapper — but pass `onClose` as a no-op
`() => {}` so that `AccessibleModal`'s internal ESC call does nothing (the manual handler does the
actual close). Then the focus trap and auto-focus are provided by `AccessibleModal` while ESC is
controlled manually.

Wait — this is overly complex. Let's reconsider. The standard WCAG pattern for nested dialogs
is that ESC closes the innermost dialog only. Users expect to press ESC once for the crop modal
and once more for the profile modal. Option A (let both close on one ESC) is therefore the
worse UX. Option C is the correct approach and matches standard AT behaviour.

**Final decision: Option C** — keep the `useEffect` ESC handler with `stopPropagation`, remove
its `setCropOpen(false)` call from inside it (since `AccessibleModal`'s `onClose` handles that),
and keep `e.stopPropagation()` only to prevent the outer modal from seeing the event. The
`AccessibleModal` `onClose` is `() => setCropOpen(false)`.

Revised `useEffect` (lines 64–74 become):
```tsx
useEffect(() => {
  if (!cropOpen) return;
  const handler = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.stopPropagation(); // Prevent outer AccessibleModal from also closing
    }
  };
  document.addEventListener('keydown', handler, true); // Use capture to run before AccessibleModal
  return () => document.removeEventListener('keydown', handler, true);
}, [cropOpen]);
```

Using capture phase (`true`) ensures this handler fires before `AccessibleModal`'s bubble-phase
handler. It stops propagation, so `AccessibleModal`'s handler never fires for ESC — but we need
`AccessibleModal`'s `onClose` to actually run. With propagation stopped, `AccessibleModal`'s
`document.addEventListener('keydown', ...)` never executes.

This means `setCropOpen(false)` must still be called by our capture-phase handler:
```tsx
const handler = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    e.stopPropagation();
    setCropOpen(false);
  }
};
document.addEventListener('keydown', handler, true);
```

With `AccessibleModal`'s `onClose={() => setCropOpen(false)}`, the `AccessibleModal` ESC path is
also `setCropOpen(false)` — but since we stopped propagation in capture, `AccessibleModal`'s
handler never fires. Our capture handler calls `setCropOpen(false)` directly. This is equivalent
to the original code and is correct.

Summary: in `ProfileModal`, keep the `useEffect` ESC capture handler unchanged from the original
(lines 64–74, using `true` as the third argument), and wrap the crop DOM in `AccessibleModal`.

### Lightbox: click-to-close interaction

`AccessibleModal` calls `onClose` when the overlay background is clicked (`onClick={onClose}` on
the outer fixed div). The lightbox inner `<div>` (containing the image) also has
`onClick={() => setImageLightboxOpen(false)}`. Clicking the image itself triggers the inner
`onClick`, and because `stopPropagation` is not called, the overlay `onClick` also fires — both
call `setImageLightboxOpen(false)`, which is idempotent. This is correct.

Clicking outside the image (on the black overlay) fires the overlay `onClick` directly.

### Lightbox: image is now inside a dialog — impact on focus

`AccessibleModal` auto-focuses the first focusable element inside the panel. The lightbox panel
contains a `<div>` and an `<img>` — neither is focusable by default. `AccessibleModal` uses
`FOCUSABLE_SELECTORS` which does not include `img` or `div`. The timer runs, finds no focusable
element, and does nothing. The `sr-only` `<span>` is not focusable.

This means the lightbox opens with no focused element inside the dialog. WCAG 2.4.3 requires
focus to move into the dialog. To satisfy this, make the inner `<div>` focusable:

```tsx
<div
  tabIndex={-1}  // focusable but not in Tab order
  onClick={() => setImageLightboxOpen(false)}
  className="outline-none"
>
```

Wait — `tabIndex={-1}` is not included in `FOCUSABLE_SELECTORS`. The selector includes
`[tabindex]:not([tabindex="-1"])`. So `tabIndex={-1}` still won't be auto-focused.

Better approach: use `tabIndex={0}` on the containing `<div>`, which makes it focusable and
included in the Tab order. When the lightbox opens, `AccessibleModal` auto-focuses this div.
The div represents the "close lightbox" action (clicking it closes the lightbox), so it is
semantically appropriate to be focusable. Add `aria-label={t('cardDetail.closeLightbox')}`.

```tsx
<div
  tabIndex={0}
  role="button"
  aria-label={t('cardDetail.closeLightbox')}
  onClick={() => setImageLightboxOpen(false)}
  onKeyDown={(e) => e.key === 'Enter' && setImageLightboxOpen(false)}
  className="outline-none cursor-zoom-out"
>
  <span id="card-detail-lightbox-title" className="sr-only">...</span>
  <img ... />
</div>
```

This is the same pattern already used in `CardDetailModal` and `DeckDetailModal` for the
image-click-to-lightbox button: `role="button"`, `tabIndex={0}`, `aria-label`. The lightbox
dismissal button is itself the entire image container.

New i18n keys for lightbox close label:
- `en.json`: `"cardDetail": { ..., "closeLightbox": "Close image, press Escape or click to close" }`
- `es.json`: `"cardDetail": { ..., "closeLightbox": "Cerrar imagen, pulsa Escape o haz clic para cerrar" }`
- Same for `deckDetail`.

Actually, keeping it simpler is better. The lightbox accessible name comes from
`aria-labelledby="card-detail-lightbox-title"` on the dialog, and the inner button's `aria-label`
can simply be `t('common.close')`. The tab-focused element inside is what matters for focus, and
clicking anywhere closes the lightbox.

**Final lightbox structure**:
```tsx
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
    onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setImageLightboxOpen(false)}
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
```

### DeckImportModal: `autoFocus` and `AccessibleModal` auto-focus interaction

`DeckImportModal`'s textarea has `autoFocus`. `AccessibleModal` also auto-focuses the first
focusable element. The textarea is the first (and only) focusable element. Both mechanisms target
the same element — no conflict.

After adding a `<label>` element, the textarea remains the first *focusable* element (labels are
not focusable). Auto-focus still goes to the textarea. Correct.

### Static IDs for lightboxes

`card-detail-lightbox-title` and `deck-detail-lightbox-title` are used as static IDs. Since only
one instance of each can be open at a time (they are conditionally rendered based on boolean
state), these IDs are safe from collision.
