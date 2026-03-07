## 1. Add new translation keys to locale files

- [ ] 1.1 In `frontend/src/locales/en.json`, extend the `"insights"` object with a new `"list"` sub-object containing `"noItems": "No items to display"`, a new `"timeline"` sub-object containing `"noData": "No timeline data available"` and `"cardCount": "{{count}} cards"`, and a new `"comparison"` sub-object containing `"present": "Present"` and `"missing": "Missing"`
- [ ] 1.2 In `frontend/src/locales/en.json`, add a new top-level `"errorBoundary"` object with keys: `"title": "Something went wrong"`, `"description": "The application encountered an error. Please refresh the page or check the console."`, `"refresh": "Refresh Page"`
- [ ] 1.3 In `frontend/src/locales/en.json`, add `"syncEncounteredError": "Sync encountered an error"` and `"failedToStartSync": "Failed to start sync"` inside the existing `"admin"` object
- [ ] 1.4 In `frontend/src/locales/en.json`, add `"importFailed": "Import failed"` inside the existing `"deckImport"` object
- [ ] 1.5 In `frontend/src/locales/en.json`, add a new `"errors"` sub-object inside the existing `"settings"` object containing: `"failedToSave": "Failed to save Scryfall credentials"`, `"importFailed": "Import failed"`, `"failedToClear": "Failed to clear credentials"`, `"failedToUpdate": "Failed to update setting"`
- [ ] 1.6 In `frontend/src/locales/es.json`, mirror all the changes from tasks 1.1–1.5 with Spanish translations:
  - `insights.list.noItems`: `"No hay elementos para mostrar"`
  - `insights.timeline.noData`: `"No hay datos de cronología disponibles"`
  - `insights.timeline.cardCount`: `"{{count}} cartas"`
  - `insights.comparison.present`: `"Presente"`
  - `insights.comparison.missing`: `"Ausente"`
  - `errorBoundary.title`: `"Algo salió mal"`
  - `errorBoundary.description`: `"La aplicación encontró un error. Por favor, recarga la página o revisa la consola."`
  - `errorBoundary.refresh`: `"Recargar página"`
  - `admin.syncEncounteredError`: `"La sincronización encontró un error"`
  - `admin.failedToStartSync`: `"Error al iniciar la sincronización"`
  - `deckImport.importFailed`: `"Error al importar"`
  - `settings.errors.failedToSave`: `"Error al guardar las credenciales de Scryfall"`
  - `settings.errors.importFailed`: `"Error al importar"`
  - `settings.errors.failedToClear`: `"Error al eliminar las credenciales"`
  - `settings.errors.failedToUpdate`: `"Error al actualizar el ajuste"`

**Acceptance criteria**: Both locale files are valid JSON (no parse errors), all new keys are present in both files, and each en.json key has a corresponding es.json key with a non-empty Spanish string.

## 2. Wire insight renderer — InsightListRenderer

- [ ] 2.1 In `frontend/src/components/insights/InsightListRenderer.tsx`, add `import { useTranslation } from 'react-i18next'` at the top of the file alongside the existing imports
- [ ] 2.2 Add `const { t } = useTranslation()` as the first statement inside the `InsightListRenderer` function body
- [ ] 2.3 Replace the hardcoded string `'No items to display'` (line 29) with `{t('insights.list.noItems')}`

**Acceptance criteria**: The component no longer contains any hardcoded English string in JSX. Switching the app to Spanish shows `"No hay elementos para mostrar"` in the empty state.

## 3. Wire insight renderer — InsightTimelineRenderer

- [ ] 3.1 In `frontend/src/components/insights/InsightTimelineRenderer.tsx`, add `import { useTranslation } from 'react-i18next'` alongside the existing imports
- [ ] 3.2 Add `const { t } = useTranslation()` as the first statement inside the `InsightTimelineRenderer` function body
- [ ] 3.3 Replace `'No timeline data available'` (line 24) with `{t('insights.timeline.noData')}`
- [ ] 3.4 Replace the inline `{item.count} cards` text (line 53, inside the count/value div) with `{t('insights.timeline.cardCount', { count: item.count })}`

**Acceptance criteria**: No hardcoded English strings remain in this component's JSX. Both the empty-state message and the card count label render in the active locale.

## 4. Wire insight renderer — InsightComparisonRenderer

- [ ] 4.1 In `frontend/src/components/insights/InsightComparisonRenderer.tsx`, add `import { useTranslation } from 'react-i18next'` alongside the existing imports
- [ ] 4.2 Add `const { t } = useTranslation()` as the first statement inside the `InsightComparisonRenderer` function body
- [ ] 4.3 Replace `aria-label={item.present ? 'Present' : 'Missing'}` (line 52) with `aria-label={item.present ? t('insights.comparison.present') : t('insights.comparison.missing')}`

**Acceptance criteria**: The aria-label no longer contains hardcoded English. Screen reader users in Spanish see "Presente" / "Ausente" on the presence/absence indicators.

## 5. Refactor ErrorBoundary to support useTranslation

- [ ] 5.1 In `frontend/src/components/ErrorBoundary.tsx`, add `import { useTranslation } from 'react-i18next'` at the top of the file
- [ ] 5.2 Extract a new private functional component `ErrorFallback` that accepts props `{ error: Error | null; onReset: () => void }`, calls `const { t } = useTranslation()` inside, and renders the same error screen HTML that the class currently renders in its `render()` method — replacing:
  - `'Something went wrong'` → `{t('errorBoundary.title')}`
  - The description paragraph text → `{t('errorBoundary.description')}`
  - `'Refresh Page'` button text → `{t('errorBoundary.refresh')}`
- [ ] 5.3 Update the `ErrorBoundary` class component's `render()` method: when `this.state.hasError` is true, return `<ErrorFallback error={this.state.error} onReset={() => this.setState({ hasError: false, error: null })} />` instead of the inline JSX
- [ ] 5.4 Keep the public export `ErrorBoundary` and its Props/State interfaces unchanged — callers must require no modification

**Acceptance criteria**: When a runtime error is caught, the error screen renders the heading, description, and button in the active locale. TypeScript compiles without errors. The `ErrorBoundary` component API (wraps children, `Props` interface) is unchanged.

## 6. Fix catch-block fallback strings — Admin.tsx

- [ ] 6.1 In `frontend/src/pages/Admin.tsx`, locate the WebSocket `onmessage` handler (inside the second `useEffect`). On line 76, replace `data.message || 'Sync encountered an error'` with `data.message || t('admin.syncEncounteredError')`. Note: `t` is already in scope from the outer component function.
- [ ] 6.2 In `handleStartSync`, locate the `catch` block (around line 109). Replace `e instanceof Error ? e.message : 'Failed to start sync'` with `e instanceof Error ? e.message : t('admin.failedToStartSync')`

**Acceptance criteria**: Both fallback strings are gone. When the WebSocket receives an error message without a `message` field, or when `handleStartSync` catches a non-Error rejection, the displayed error text comes from the locale file.

## 7. Fix catch-block fallback string — DeckImportModal.tsx

- [ ] 7.1 In `frontend/src/components/DeckImportModal.tsx`, the mutation error is displayed at line 61-64. Replace `mutation.error instanceof Error ? mutation.error.message : 'Import failed'` with `mutation.error instanceof Error ? mutation.error.message : t('deckImport.importFailed')`. Note: `t` is already in scope.

**Acceptance criteria**: The hardcoded `'Import failed'` fallback is removed. When the mutation rejects with a non-Error value, the user sees the translated string.

## 8. Fix catch-block fallback strings — Settings.tsx

- [ ] 8.1 In `frontend/src/pages/Settings.tsx`, in `handleSaveScryfallCredentials` catch block (line ~46), replace `'Failed to save Scryfall credentials'` with `t('settings.errors.failedToSave')`
- [ ] 8.2 In `handleFileChange` catch block (line ~76), replace `'Import failed'` with `t('settings.errors.importFailed')`
- [ ] 8.3 In the inline clear credentials button click handler catch block (line ~139), replace `'Failed to clear credentials'` with `t('settings.errors.failedToClear')`
- [ ] 8.4 In the Scryfall toggle button click handler catch block (line ~180), replace `'Failed to update setting'` with `t('settings.errors.failedToUpdate')`

**Acceptance criteria**: All 4 fallback strings in `Settings.tsx` use `t()` calls. The component still compiles, and `t` is already in scope.

## 9. Fix catch-block fallback strings — SettingsModal.tsx

- [ ] 9.1 In `frontend/src/components/SettingsModal.tsx`, apply the same 4 replacements as in tasks 8.1–8.4:
  - `handleSaveScryfallCredentials` catch: `'Failed to save Scryfall credentials'` → `t('settings.errors.failedToSave')`
  - `handleFileChange` catch: `'Import failed'` → `t('settings.errors.importFailed')`
  - Clear button handler catch: `'Failed to clear credentials'` → `t('settings.errors.failedToClear')`
  - Toggle button handler catch: `'Failed to update setting'` → `t('settings.errors.failedToUpdate')`

**Acceptance criteria**: All 4 fallback strings in `SettingsModal.tsx` use `t()` calls. The component compiles with no TypeScript errors.

## 10. Verification

- [ ] 10.1 Run `npm run build` in `frontend/` — zero TypeScript errors and zero build errors
- [ ] 10.2 Run `npm run lint` in `frontend/` — zero ESLint errors
- [ ] 10.3 Switch the app language to Spanish and spot-check the 8 modified locations:
  - Navigate to the Collection Insights panel, run an insight that returns an empty list → verify "No hay elementos para mostrar" appears
  - Run a timeline insight with data → verify "{{count}} cartas" appears (e.g., "5 cartas")
  - Inspect the comparison renderer aria-labels via browser DevTools accessibility inspector → verify "Presente" / "Ausente"
  - Trigger the ErrorBoundary by temporarily throwing in a child component → verify Spanish error screen
  - In Admin page, observe that the sync error fallback and start sync fallback would display Spanish (test with mock or manual check of key presence in es.json)
  - In DeckImportModal, verify the import error key exists in es.json
  - In Settings page (both standalone and modal), verify catch fallback keys exist in es.json
- [ ] 10.4 Verify that `frontend/src/locales/en.json` and `frontend/src/locales/es.json` are valid JSON by running `node -e "require('./frontend/src/locales/en.json'); require('./frontend/src/locales/es.json'); console.log('OK')"` from the repo root
- [ ] 10.5 Confirm that no `.tsx` file in `frontend/src/` (excluding test files and pure chart primitives that receive all text as props) contains a user-visible string not routed through `t()`
