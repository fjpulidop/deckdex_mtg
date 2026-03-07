## Why

The i18n infrastructure (i18next, LanguageSwitcher, locale files) is fully operational, but several components were shipped without being wired to it — they render hardcoded English strings regardless of the user's selected language. Additionally, two insight renderers hardcode `toLocaleString('es-ES')`, which forces Spanish number formatting even when the app is set to English.

## What Changes

- **ActionButtons.tsx**: Add `useTranslation()` and replace 4 hardcoded strings (`'Starting...'`, `'Process Cards'`, `'New added cards (with only the name)'`, `'All cards'`, `'Update Prices'`, `'Actions'`) with `t()` calls — keys already exist in `actionButtons.*`.
- **PriceChart.tsx**: Add `useTranslation()` and introduce 3 new translation keys (`priceChart.title`, `priceChart.noHistory`, `priceChart.tooltipLabel`) to replace hardcoded strings. Add keys to both locale files.
- **InsightValueRenderer.tsx**: Replace `toLocaleString('es-ES', ...)` with `toLocaleString(i18n.language, ...)` so number formatting respects the active locale.
- **InsightDistributionRenderer.tsx**: Replace `toLocaleString('es-ES')` with `toLocaleString(i18n.language)` for the same reason.
- **Demo.tsx**: Add `useTranslation()` and introduce 3 new keys (`demo.bannerText`, `demo.bannerSignIn`, `demo.bannerDismiss`) to replace hardcoded banner strings. Add keys to both locale files.
- **ThemeToggle.tsx**: Add `useTranslation()` and introduce 2 new keys (`themeToggle.switchToDark`, `themeToggle.switchToLight`) to replace hardcoded `title` and `aria-label`. Add keys to both locale files.
- **AuthCallback.tsx**: Add `useTranslation()` and use the existing `login.loading` key to replace `'Signing in…'`.
- **Dashboard.tsx**: Replace `title="Add card"` with `title={t('dashboard.addCard')}` — the key already exists.
- **Navbar.tsx**: Replace hardcoded `aria-label="User menu"` and `aria-label="Toggle mobile menu"` with `t()` calls using 2 new keys (`navbar.userMenu`, `navbar.toggleMobileMenu`). Add keys to both locale files.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `i18n`: The requirement "All hardcoded UI strings replaced with t() calls" was not fully implemented. This change closes the gaps identified by audit: 8 components still contain hardcoded strings and 2 renderers use a hardcoded locale identifier. The spec requirement already covers this — this change is the implementation catch-up.

## Impact

- `frontend/src/components/ActionButtons.tsx` — wire existing keys
- `frontend/src/components/PriceChart.tsx` — add new keys + wire
- `frontend/src/components/insights/InsightValueRenderer.tsx` — fix locale bug
- `frontend/src/components/insights/InsightDistributionRenderer.tsx` — fix locale bug
- `frontend/src/pages/Demo.tsx` — add new keys + wire
- `frontend/src/components/ThemeToggle.tsx` — add new keys + wire
- `frontend/src/pages/AuthCallback.tsx` — wire existing key
- `frontend/src/pages/Dashboard.tsx` — wire existing key
- `frontend/src/components/Navbar.tsx` — add new keys + wire
- `frontend/src/locales/en.json` — add ~7 new translation keys
- `frontend/src/locales/es.json` — add matching Spanish translations for the same keys

No API changes. No backend changes. No new dependencies.

## Non-goals

- Translating backend API error strings (explicitly out of scope per the i18n spec).
- Adding new languages beyond en/es.
- Auditing components outside of `frontend/src/` (e.g., landing-only pages not listed above).
- Translating dynamic card data (card names, set names, etc.) from Scryfall.
