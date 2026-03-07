### Requirement: All hardcoded UI strings replaced with t() calls
Every user-visible string in `frontend/src/` (labels, placeholders, titles, button text, error messages, aria-labels, empty-state messages, error fallback strings) SHALL be replaced with a `t('key')` call from `useTranslation()`. No UI string SHALL be hardcoded directly in JSX after this change. This includes:

- Empty-state messages in insight renderer components (`InsightListRenderer`, `InsightTimelineRenderer`, `InsightComparisonRenderer`)
- Aria-labels on non-interactive visual indicators (e.g., presence/absence markers in comparison renderers)
- Error boundary UI strings (the `ErrorBoundary` component error screen)
- Fallback error strings in `catch` blocks where `e` is not an `Error` instance

#### Scenario: Component renders in active locale
- **WHEN** a component using `useTranslation()` renders
- **THEN** all text nodes and aria-label values reflect the currently active language

#### Scenario: Insight renderer shows empty state in active locale
- **WHEN** an insight returns an empty items list
- **THEN** the empty-state message (e.g., "No items to display") is shown in the active locale language

#### Scenario: ErrorBoundary renders in active locale
- **WHEN** a JavaScript error is caught by `ErrorBoundary`
- **THEN** the error screen heading, description, and refresh button text appear in the active locale language

#### Scenario: Catch block fallback shows in active locale
- **WHEN** a network or API operation fails with a non-Error rejection
- **THEN** the fallback error message shown to the user is in the active locale language (not hardcoded English)

#### Scenario: Missing translation key falls back to English
- **WHEN** a translation key exists in `en.json` but is missing from `es.json`
- **THEN** the English string is displayed (i18next fallback language behavior)
