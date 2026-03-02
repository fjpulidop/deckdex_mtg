## 1. Setup

- [x] 1.1 Install `i18next` and `react-i18next` via npm in `frontend/`
- [x] 1.2 Create `frontend/src/locales/` directory
- [x] 1.3 Create `frontend/src/i18n.ts` — init i18next with localStorage detection, browser fallback, and `'en'` as ultimate fallback
- [x] 1.4 Import `i18n.ts` as a side-effect in `frontend/src/main.tsx` (before React renders)

## 2. Locale files

- [x] 2.1 Create `frontend/src/locales/en.json` with all UI strings extracted from components and pages (dot-notation keys grouped by component/page, plus `common.*` for shared strings)
- [x] 2.2 Create `frontend/src/locales/es.json` with Spanish translations for all keys in `en.json`

## 3. Language switcher component

- [x] 3.1 Create `frontend/src/components/LanguageSwitcher.tsx` — compact `EN | ES` toggle using `i18next.changeLanguage()` and persisting to `localStorage`
- [x] 3.2 Add `LanguageSwitcher` to `Navbar.tsx` desktop bar (right side, near ThemeToggle)
- [x] 3.3 Add `LanguageSwitcher` to `Navbar.tsx` mobile menu

## 4. Migrate components

- [x] 4.1 Migrate `Filters.tsx` — search placeholder, rarity/type/set option labels, price placeholders, color filter titles
- [x] 4.2 Migrate `CardTable.tsx` — column headers, cell titles, sort tooltips
- [x] 4.3 Migrate `CardFormModal.tsx` — form labels, placeholders, button text
- [x] 4.4 Migrate `CardDetailModal.tsx` — field labels, section headers, button text
- [x] 4.5 Migrate `DeckDetailModal.tsx` — labels, headers, button text
- [x] 4.6 Migrate `ConfirmModal.tsx` — confirm/cancel button text, any static copy
- [x] 4.7 Migrate `JobLogModal.tsx` — "Progress" label, status text
- [x] 4.8 Migrate `JobsBottomBar.tsx` — "Stop" button, status labels
- [x] 4.9 Migrate `ActiveJobs.tsx` — job status strings, labels
- [x] 4.10 Migrate `ProfileModal.tsx` — field labels, placeholders (`"Your name"`), error message (`'Error al guardar el perfil'`)
- [x] 4.11 Migrate `SettingsModal.tsx` — Spanish import section text (`"Importar colección"`, descriptions), all other labels
- [x] 4.12 Migrate `CollectionInsights.tsx` — section labels, stat names
- [x] 4.13 Migrate `DeckCardPickerModal.tsx` — sort option labels, placeholders, button text

## 5. Migrate pages

- [x] 5.1 Migrate `Import.tsx` — all text (currently mostly Spanish): page title, tab labels, dropzone text, format hints, button text, result messages
- [x] 5.2 Migrate `Dashboard.tsx` — page title, button titles, empty-state text
- [x] 5.3 Migrate `Analytics.tsx` — chart titles, axis labels, filter/reset button titles, section headers
- [x] 5.4 Migrate `DeckBuilder.tsx` — page title, aria-labels, deck list labels
- [x] 5.5 Migrate `Login.tsx` — login prompt text, subtitle
- [x] 5.6 Migrate `Settings.tsx` — section labels, descriptions
- [x] 5.7 Migrate `Admin.tsx` — labels, status text, button text

## 6. Migrate landing pages

- [x] 6.1 Migrate `LandingNavbar.tsx` — nav link labels (`"Features"`, `"Source Code"`)
- [x] 6.2 Migrate `Hero.tsx` — headline, subtitle, CTA text
- [x] 6.3 Migrate `BentoGrid.tsx` and `BentoCard.tsx` — feature names and descriptions
- [x] 6.4 Migrate `FinalCTA.tsx` — CTA heading and button text
- [x] 6.5 Migrate `Footer.tsx` — footer links, copyright text
- [x] 6.6 Migrate `InteractiveDemo.tsx` — demo labels and descriptions

## 7. Audit and smoke test

- [x] 7.1 Grep audit: search for remaining string literals in JSX that are not inside `t()` — fix any missed strings and add missing keys to locale files
- [x] 7.2 Smoke-test English locale: verify all UI renders correctly in EN
- [x] 7.3 Smoke-test Spanish locale: switch to ES and verify all UI renders correctly with no key-fallthrough artifacts (raw key strings visible)
- [x] 7.4 Verify localStorage persistence: switch language, reload page, confirm language is restored
