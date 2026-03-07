# i18n Coverage Audit Exploration (2026-03-07)

## Summary
- i18n spec exists at `openspec/specs/i18n/spec.md` -- clear requirements
- Infrastructure is solid: i18next + react-i18next, `i18n.ts` config, localStorage persistence, browser lang detection
- `en.json` and `es.json` both exist with ~565 lines, 30+ top-level sections
- 35 of ~45 non-test TSX files use `useTranslation()`
- Key structure between en.json and es.json is 1:1 (no missing keys between them)

## Files WITHOUT useTranslation (10 with user-visible hardcoded strings)

### HIGH PRIORITY (user-facing text visible in normal usage)
1. **ActionButtons.tsx** -- 6 hardcoded strings: "Starting...", "Process Cards", "New added cards (with only the name)", "All cards", "Update Prices", "Actions" heading. Translation keys EXIST in `actionButtons.*` section of en.json but component never imports useTranslation!
2. **PriceChart.tsx** -- 3 hardcoded strings: "Price History" (x3 occurrences), "No price history yet -- run a price update to start tracking.", tooltip label "Price"
3. **ErrorBoundary.tsx** -- 3 hardcoded strings: "Something went wrong", "The application encountered an error...", "Refresh Page". Note: class component, cannot use hooks directly (needs wrapper or i18next.t import)
4. **Demo.tsx** -- 3 hardcoded strings: "You're viewing a demo with sample data.", "Sign in with Google", aria-label "Dismiss banner"
5. **AuthCallback.tsx** -- 1 hardcoded string: "Signing in..."
6. **ThemeToggle.tsx** -- 2 hardcoded strings in title/aria-label: "Switch to light mode" / "Switch to dark mode"

### MEDIUM PRIORITY (insight renderers -- display backend data but have some static UI strings)
7. **InsightListRenderer.tsx** -- 1 hardcoded: "No items to display"
8. **InsightTimelineRenderer.tsx** -- 2 hardcoded: "No timeline data available", "{count} cards" (template string)
9. **InsightComparisonRenderer.tsx** -- 2 hardcoded aria-labels: "Present", "Missing"

### LOW PRIORITY (no user-visible strings or brand names only)
10. **InsightValueRenderer.tsx** -- no hardcoded UI strings, BUT has `toLocaleString('es-ES')` hardcoded
11. **InsightDistributionRenderer.tsx** -- no hardcoded strings, BUT has `toLocaleString('es-ES')` hardcoded
12. Analytics chart components (RarityChart, TopSetsChart, TypeDistributionChart) -- no user-visible strings (data-driven labels)
13. Landing.tsx, AdminRoute.tsx, ProtectedRoute.tsx, backgrounds/* -- no user-visible strings
14. InsightResponse.tsx -- no hardcoded strings (uses `response.question` from backend)
15. BentoCard.tsx -- no hardcoded strings (receives props)
16. ManaText.tsx -- no user-visible strings

## Hardcoded Strings in Components THAT DO Use useTranslation

### In Navbar.tsx
- `aria-label="User menu"` -- hardcoded
- `aria-label="Toggle mobile menu"` -- hardcoded

### In Footer.tsx (landing)
- `aria-label="Twitter"`, `aria-label="GitHub"`, `aria-label="Discord"` -- brand names, arguably OK

### In Dashboard.tsx
- `title="Add card"` -- hardcoded (should use t('dashboard.addCard'))

### In CardDetailModal.tsx
- `alert(... 'Delete failed')` -- hardcoded error in alert()

## Locale-Specific Bugs

### Hardcoded 'es-ES' locale in number formatting
- `InsightValueRenderer.tsx:37-38` -- `toLocaleString('es-ES', ...)` hardcoded regardless of active language
- `InsightDistributionRenderer.tsx:69` -- `toLocaleString('es-ES')` hardcoded regardless of active language
- Should use `i18n.language` to derive locale (en -> 'en-US', es -> 'es-ES')

## Missing Translation Keys (needed for new strings)
Keys that need to be ADDED to en.json and es.json:
- `priceChart.title` / `priceChart.noData` / `priceChart.tooltipLabel`
- `errorBoundary.title` / `errorBoundary.message` / `errorBoundary.refresh`
- `demo.banner` / `demo.signInGoogle` / `demo.dismissBanner`
- `authCallback.signingIn`
- `themeToggle.lightMode` / `themeToggle.darkMode`
- `insights.noItems` / `insights.noTimeline` / `insights.cards` (pluralized)
- `insights.present` / `insights.missing`
- `navbar.userMenu` / `navbar.toggleMobile`

## Key Finding: ActionButtons Has Keys But Doesn't Use Them
The `actionButtons.*` section exists in BOTH en.json and es.json with all 6 keys properly translated. But ActionButtons.tsx never imports or calls `useTranslation()`. This is a trivial fix -- just add the import and replace the 6 hardcoded strings with `t()` calls. This was previously noted in the accessibility exploration.

## Quantitative Summary
- Total non-test TSX files: ~45
- Files using useTranslation: 35 (78%)
- Files with hardcoded user-visible strings: 10 (22%)
- Total hardcoded strings found: ~25
- Strings with existing translation keys (just need t() call): ~8 (ActionButtons + Dashboard)
- Strings needing NEW keys in en.json + es.json: ~17
- Hardcoded locale bugs: 2 files (InsightValueRenderer, InsightDistributionRenderer)
