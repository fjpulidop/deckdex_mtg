## Context

The first i18n coverage sweep (archived 2026-03-07) wired `ActionButtons`, `PriceChart`, `ThemeToggle`, `Demo` banner, `AuthCallback`, `Dashboard`, and `Navbar`, and fixed the `es-ES` locale bug in two insight renderers. A second audit of `frontend/src/` reveals 6 additional locations with hardcoded English strings, affecting 8 files total (including two that share the same Settings logic in modal vs. page form).

The remaining gaps fall into three categories:

1. **Insight sub-renderers**: `InsightListRenderer`, `InsightTimelineRenderer`, `InsightComparisonRenderer` — pure presentational components that render empty-state text and aria-labels in hardcoded English.
2. **ErrorBoundary**: A class component — the only one in the codebase — rendering 3 hardcoded strings. Class components cannot use hooks, requiring a functional rewrite.
3. **Catch-block fallback strings**: `Admin`, `DeckImportModal`, `Settings`, `SettingsModal` — all already use `useTranslation()` but their `catch` branches fall back to hardcoded English strings when the error object is not an `Error` instance.

## Goals / Non-Goals

**Goals:**
- Achieve 100% coverage of user-visible strings across all `.tsx` files in `frontend/src/`
- Add the minimum set of new translation keys (13 new en.json keys + matching es.json translations)
- Maintain structural parity between `en.json` and `es.json`

**Non-Goals:**
- Translating `console.error()` messages (developer-only, not user-visible)
- Translating backend API error strings (spec explicitly excludes these)
- Adding new languages
- Touching components already covered by the previous sweep

## Key Decisions

### Decision 1: ErrorBoundary — Convert to functional component

**Problem**: `ErrorBoundary.tsx` is a class component (`extends Component<Props, State>`). Class components cannot use hooks, so `useTranslation()` cannot be called directly inside the render method.

**Options considered**:
1. Keep class component, wrap in a functional HOC that passes translated strings as props.
2. Convert ErrorBoundary to a functional component using React's `useErrorBoundary` (if available) or a state-based approach.
3. Use a static `t` function imported directly from `i18next` (bypasses hook system).

**Decision**: Convert to a functional component using `useState` + an event listener pattern for error catching, or more precisely, use a pattern with a class-based error catcher delegating render to a functional child. The simplest correct approach is: keep the class for error catching but extract the error UI into a functional component.

**Concretely**: Refactor into two components:
- `ErrorBoundaryClass` (class, private) — only implements `getDerivedStateFromError` and `componentDidCatch`, delegates all rendering to `ErrorBoundaryUI`
- `ErrorBoundaryUI` (functional, private) — receives `hasError`, `error`, `onReset` props, calls `useTranslation()`, renders the error screen
- `ErrorBoundary` (public export) — is the class component wrapper, unchanged API

This preserves the required class component semantics for error catching while allowing hooks in the UI layer.

**Rationale**: The class component pattern for error boundaries is required by React (no functional equivalent for `componentDidCatch` yet in React 19 without experimental APIs). Delegating render to a functional child is the standard community pattern for this scenario.

### Decision 2: Insight renderer empty-state strings — new namespace segment `insights.*`

**Problem**: `InsightListRenderer`, `InsightTimelineRenderer`, and `InsightComparisonRenderer` each have 1-3 hardcoded strings. No insight sub-renderer keys exist yet.

**Decision**: Add keys under the existing `insights` namespace using sub-keys scoped to each renderer type:
- `insights.list.noItems` — "No items to display"
- `insights.timeline.noData` — "No timeline data available"
- `insights.timeline.cardCount` — "{{count}} cards" (interpolated)
- `insights.comparison.present` — "Present" (aria-label)
- `insights.comparison.missing` — "Missing" (aria-label)

**Rationale**: The existing `insights.*` namespace in `en.json` covers the `CollectionInsights` component UI. These sub-keys naturally extend the namespace without polluting `common.*`. The `{{count}}` interpolation for `cardCount` follows the existing pattern used in `gallery.quantityBadge`, `jobLog.progressCount`, etc.

### Decision 3: Catch-block fallback strings — new `settings.errors.*` sub-namespace

**Problem**: Both `Settings.tsx` and `SettingsModal.tsx` contain identical catch blocks with 4 hardcoded fallback strings. These are reached when `e` is not an `Error` instance (network errors sometimes arrive as plain objects).

**Decision**: Add `settings.errors.failedToSave`, `settings.errors.importFailed`, `settings.errors.failedToClear`, `settings.errors.failedToUpdate` keys under `settings`. Both `Settings.tsx` and `SettingsModal.tsx` use the same keys.

**Rationale**: The two files are parallel implementations (modal vs. page). Using the same keys avoids divergence. Grouping under `settings.errors.*` makes the error keys easy to find and maintains the component-scoped namespace convention.

### Decision 4: Admin and DeckImportModal catch strings — minimal additions

**Problem**: `Admin.tsx` line 76 has `'Sync encountered an error'` and line 109 has `'Failed to start sync'` as fallbacks. `DeckImportModal.tsx` line 63 has `'Import failed'`.

**Decision**:
- `Admin.tsx`: Add `admin.syncEncounteredError` ("Sync encountered an error") and `admin.failedToStartSync` ("Failed to start sync") to the existing `admin.*` namespace.
- `DeckImportModal.tsx`: Add `deckImport.importFailed` ("Import failed") to the existing `deckImport.*` namespace.

**Rationale**: Both files already have well-populated namespaces. Adding to the existing namespace is consistent and discoverable. Reusing `common.*` keys was considered but rejected — "Failed to start sync" is domain-specific enough to belong to `admin.*`.

## New Translation Keys

All 13 new keys must be added to both `en.json` and `es.json`.

### en.json additions

```json
// Under "insights":
"list": {
  "noItems": "No items to display"
},
"timeline": {
  "noData": "No timeline data available",
  "cardCount": "{{count}} cards"
},
"comparison": {
  "present": "Present",
  "missing": "Missing"
}

// Under "errorBoundary" (new top-level namespace):
"errorBoundary": {
  "title": "Something went wrong",
  "description": "The application encountered an error. Please refresh the page or check the console.",
  "refresh": "Refresh Page"
}

// Under "admin":
"syncEncounteredError": "Sync encountered an error",
"failedToStartSync": "Failed to start sync"

// Under "deckImport":
"importFailed": "Import failed"

// Under "settings":
"errors": {
  "failedToSave": "Failed to save Scryfall credentials",
  "importFailed": "Import failed",
  "failedToClear": "Failed to clear credentials",
  "failedToUpdate": "Failed to update setting"
}
```

### es.json additions (Spanish translations)

```json
// Under "insights":
"list": {
  "noItems": "No hay elementos para mostrar"
},
"timeline": {
  "noData": "No hay datos de cronología disponibles",
  "cardCount": "{{count}} cartas"
},
"comparison": {
  "present": "Presente",
  "missing": "Ausente"
}

// Under "errorBoundary":
"errorBoundary": {
  "title": "Algo salió mal",
  "description": "La aplicación encontró un error. Por favor, recarga la página o revisa la consola.",
  "refresh": "Recargar página"
}

// Under "admin":
"syncEncounteredError": "La sincronización encontró un error",
"failedToStartSync": "Error al iniciar la sincronización"

// Under "deckImport":
"importFailed": "Error al importar"

// Under "settings":
"errors": {
  "failedToSave": "Error al guardar las credenciales de Scryfall",
  "importFailed": "Error al importar",
  "failedToClear": "Error al eliminar las credenciales",
  "failedToUpdate": "Error al actualizar el ajuste"
}
```

## Component-Level Implementation Notes

### InsightListRenderer.tsx
- Add `import { useTranslation } from 'react-i18next'`
- Add `const { t } = useTranslation()` inside `InsightListRenderer` function
- Replace `'No items to display'` → `{t('insights.list.noItems')}`

### InsightTimelineRenderer.tsx
- Add `import { useTranslation } from 'react-i18next'`
- Add `const { t } = useTranslation()` inside `InsightTimelineRenderer` function
- Replace `'No timeline data available'` → `{t('insights.timeline.noData')}`
- Replace `{item.count} cards` → `{t('insights.timeline.cardCount', { count: item.count })}`

### InsightComparisonRenderer.tsx
- Add `import { useTranslation } from 'react-i18next'`
- Add `const { t } = useTranslation()` inside `InsightComparisonRenderer` function
- Replace `aria-label={item.present ? 'Present' : 'Missing'}` → `aria-label={item.present ? t('insights.comparison.present') : t('insights.comparison.missing')}`

### ErrorBoundary.tsx
- Extract the error UI into a new private functional component `ErrorFallback` that accepts `error: Error | null` and `onReset: () => void` props
- `ErrorFallback` calls `useTranslation()` and replaces the 3 hardcoded strings
- The existing `ErrorBoundary` class component calls `<ErrorFallback error={this.state.error} onReset={() => this.setState({ hasError: false, error: null })} />`
- Public export `ErrorBoundary` and its Props/State interfaces remain unchanged

### Admin.tsx
- Both strings are in catch/fallback positions in methods that already have `t` in scope (via the outer component scope)
- Line 76: `data.message || 'Sync encountered an error'` → `data.message || t('admin.syncEncounteredError')`
- Line 109: `e instanceof Error ? e.message : 'Failed to start sync'` → `e instanceof Error ? e.message : t('admin.failedToStartSync')`

### DeckImportModal.tsx
- Line 63: `mutation.error instanceof Error ? mutation.error.message : 'Import failed'` → `mutation.error instanceof Error ? mutation.error.message : t('deckImport.importFailed')`

### Settings.tsx and SettingsModal.tsx
- Both files are near-identical — apply the same 4 replacements in each:
  - `'Failed to save Scryfall credentials'` → `t('settings.errors.failedToSave')`
  - `'Import failed'` → `t('settings.errors.importFailed')`
  - `'Failed to clear credentials'` → `t('settings.errors.failedToClear')`
  - `'Failed to update setting'` → `t('settings.errors.failedToUpdate')`

## Risks / Trade-offs

**[Low risk] ErrorBoundary functional rewrite**: Converting from a pure class to a class+functional hybrid is the correct React pattern for this scenario. The public API of `ErrorBoundary` (wraps children, catches errors) is unchanged. The only behavioral change is that the error UI now renders translated strings.

**[Low risk] Catch block strings reach users rarely**: These strings are only shown when an error object is not a proper `Error` instance (e.g., a plain object thrown from a promise rejection). In practice this is rare, but the strings are still user-visible when it happens.

**[Low risk] insights.timeline.cardCount with {{count}} interpolation**: The value `item.count` is always a positive integer. No plural form is needed for this renderer (it shows the raw count without grammatical pluralization in context). However, if needed in the future, the key can be extended with `_one`/`_other` suffixes following the i18next pattern.

## Migration Plan

No migration required. All changes are purely additive (new keys) or in-place replacements. No API changes, no data migrations, no breaking changes.
