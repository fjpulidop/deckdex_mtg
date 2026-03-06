## 1. i18n keys

- [x] 1.1 Add modal i18n keys to `en.json`: `importListModal.title` ("Import list"), `importListModal.fileTab` ("File"), `importListModal.textTab` ("Text"), `importListModal.dragDrop` ("Drag & drop a .csv or .txt file here"), `importListModal.selectFile` ("Select file"), `importListModal.textPlaceholder` ("Paste your card list here…\ne.g. 4 Lightning Bolt\n1 Counterspell"), `importListModal.continue` ("Continue"), `importListModal.resolving` ("Resolving cards…")
- [x] 1.2 Add same keys to `es.json` with Spanish translations

## 2. ImportListModal component

- [x] 2.1 Create `frontend/src/components/ImportListModal.tsx` with props `onClose: () => void`
- [x] 2.2 Implement fixed overlay with click-outside-to-close (CardFormModal pattern)
- [x] 2.3 Add file/text tab toggle (text selected by default)
- [x] 2.4 Implement text tab: textarea + "Continue" button (disabled when empty)
- [x] 2.5 Implement file tab: drag-and-drop zone + file picker for .csv/.txt
- [x] 2.6 On submit: call `api.importResolve()`, show loading state, handle errors inline
- [x] 2.7 On success: close modal and `navigate('/import', { state: { resolveData } })`

## 3. Dashboard wiring

- [x] 3.1 Change `cardModal` state type to `null | 'add' | 'import'` and update `handleImport` to set `'import'`
- [x] 3.2 Render `ImportListModal` when `cardModal === 'import'`

## 4. Import page route state

- [x] 4.1 In `Import.tsx`, check `location.state?.resolveData` on mount; if present, set `resolveData` and skip to review step
- [x] 4.2 Clear route state after consuming it (`window.history.replaceState`)
