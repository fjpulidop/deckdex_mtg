## 1. Add new translation keys to locale files

- [x] 1.1 Add `priceChart.title`, `priceChart.noHistory`, and `priceChart.tooltipLabel` keys to `frontend/src/locales/en.json` under a new `"priceChart"` namespace
- [x] 1.2 Add matching Spanish translations for the three `priceChart.*` keys to `frontend/src/locales/es.json`
- [x] 1.3 Add `demo.bannerText`, `demo.bannerSignIn`, and `demo.bannerDismiss` keys to `en.json` under the existing `"demo"` namespace
- [x] 1.4 Add matching Spanish translations for the three `demo.banner*` keys to `es.json`
- [x] 1.5 Add `themeToggle.switchToDark` and `themeToggle.switchToLight` keys to `en.json` under a new `"themeToggle"` namespace
- [x] 1.6 Add matching Spanish translations for the two `themeToggle.*` keys to `es.json`
- [x] 1.7 Add `navbar.userMenu` and `navbar.toggleMobileMenu` keys to `en.json` under the existing `"navbar"` namespace
- [x] 1.8 Add matching Spanish translations for `navbar.userMenu` and `navbar.toggleMobileMenu` to `es.json`

## 2. Fix locale bug in insight renderers

- [x] 2.1 In `frontend/src/components/insights/InsightValueRenderer.tsx`, add `const { i18n } = useTranslation()` and replace both `toLocaleString('es-ES', ...)` calls with `toLocaleString(i18n.language, ...)`
- [x] 2.2 In `frontend/src/components/insights/InsightDistributionRenderer.tsx`, add `const { i18n } = useTranslation()` and replace `toLocaleString('es-ES')` with `toLocaleString(i18n.language)`

## 3. Wire existing keys in ActionButtons

- [x] 3.1 In `frontend/src/components/ActionButtons.tsx`, add `import { useTranslation } from 'react-i18next'` and `const { t } = useTranslation()` inside the component
- [x] 3.2 Replace `'Starting...'` (process button pending state) with `t('actionButtons.starting')`
- [x] 3.3 Replace `'Process Cards'` with `t('actionButtons.processCards')`
- [x] 3.4 Replace `'New added cards (with only the name)'` dropdown item with `t('actionButtons.newCards')`
- [x] 3.5 Replace `'All cards'` dropdown item with `t('actionButtons.allCards')`
- [x] 3.6 Replace `'Starting...'` (price update pending state) with `t('actionButtons.starting')`
- [x] 3.7 Replace `'Update Prices'` with `t('actionButtons.updatePrices')`
- [x] 3.8 Replace `'Actions'` heading with `t('actionButtons.actions')`

## 4. Wire new keys in PriceChart

- [x] 4.1 In `frontend/src/components/PriceChart.tsx`, add `import { useTranslation } from 'react-i18next'` and `const { t } = useTranslation()` inside the component
- [x] 4.2 Replace all three hardcoded `'Price History'` section headings with `t('priceChart.title')`
- [x] 4.3 Replace `'No price history yet — run a price update to start tracking.'` with `t('priceChart.noHistory')`
- [x] 4.4 Replace `'Price'` in the Recharts Tooltip `formatter` callback with `t('priceChart.tooltipLabel')`

## 5. Wire new keys in Demo banner

- [x] 5.1 In `frontend/src/pages/Demo.tsx`, add `import { useTranslation } from 'react-i18next'` and `const { t } = useTranslation()` inside the component
- [x] 5.2 Replace `"You're viewing a demo with sample data."` with `t('demo.bannerText')`
- [x] 5.3 Replace `'Sign in with Google'` inline CTA with `t('demo.bannerSignIn')`
- [x] 5.4 Replace `aria-label="Dismiss banner"` with `aria-label={t('demo.bannerDismiss')}`

## 6. Wire new keys in ThemeToggle

- [x] 6.1 In `frontend/src/components/ThemeToggle.tsx`, add `import { useTranslation } from 'react-i18next'` and `const { t } = useTranslation()` inside the component
- [x] 6.2 Replace `title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}` with dynamic `t()` calls using `themeToggle.switchToLight` and `themeToggle.switchToDark`
- [x] 6.3 Apply the same translation to the matching `aria-label` attribute

## 7. Wire existing key in AuthCallback

- [x] 7.1 In `frontend/src/pages/AuthCallback.tsx`, add `import { useTranslation } from 'react-i18next'` and `const { t } = useTranslation()` inside the component
- [x] 7.2 Replace `'Signing in…'` with `t('login.loading')`

## 8. Wire existing key in Dashboard

- [x] 8.1 In `frontend/src/pages/Dashboard.tsx`, confirm that `useTranslation` is already imported and `t` is available (it likely is — check the file header)
- [x] 8.2 Replace `title="Add card"` on the `CardFormModal` call with `title={t('dashboard.addCard')}`

## 9. Wire new keys in Navbar

- [x] 9.1 In `frontend/src/components/Navbar.tsx`, confirm `useTranslation` is already imported and `t` is in scope (it is — file already uses `t()` extensively)
- [x] 9.2 Replace `aria-label="User menu"` with `aria-label={t('navbar.userMenu')}`
- [x] 9.3 Replace `aria-label="Toggle mobile menu"` with `aria-label={t('navbar.toggleMobileMenu')}`

## 10. Verification

- [x] 10.1 Run `npm run build` in `frontend/` and confirm zero TypeScript errors
- [x] 10.2 Run `npm run lint` in `frontend/` and confirm zero ESLint errors
- [x] 10.3 Manually switch the app to Spanish and verify all 8 modified components display Spanish text (spot-check: ActionButtons dropdown, PriceChart heading, demo banner, ThemeToggle tooltip, AuthCallback spinner, Navbar aria-labels via browser DevTools accessibility inspector)
- [x] 10.4 Verify that insight values and distribution counts display English number format (e.g., `1,234`) when the app is set to English, and Spanish format (`1.234`) when set to Spanish
