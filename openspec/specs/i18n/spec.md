### Requirement: Locale files as source of truth
The system SHALL maintain locale files at `frontend/src/locales/en.json` (English, source of truth) and `frontend/src/locales/es.json` (Spanish). All user-visible UI strings MUST be defined in these files. Adding a new language SHALL only require adding a new `<lang>.json` file and registering it in `i18n.ts`.

#### Scenario: English locale covers all strings
- **WHEN** a developer audits all `.tsx` files in `frontend/src/`
- **THEN** every user-visible string has a corresponding key in `en.json` with no hardcoded fallback in JSX

#### Scenario: Adding a third language
- **WHEN** a `fr.json` file is created with the same key structure as `en.json` and registered in `i18n.ts`
- **THEN** French becomes available as a selectable language without any other code changes

### Requirement: Language switcher in Navbar
The system SHALL provide a language switcher control visible in the main application Navbar (both desktop and mobile views). The switcher SHALL display the currently active language and allow switching between all registered locales.

#### Scenario: Switch language from Navbar
- **WHEN** the user clicks the language switcher and selects a different locale
- **THEN** all UI text updates immediately to the selected language without a page reload

#### Scenario: Language switcher visible on mobile
- **WHEN** the user opens the mobile menu
- **THEN** the language switcher is present and functional

### Requirement: Language preference persisted to localStorage
The system SHALL persist the user's language selection to `localStorage` under the key `'lang'`. On app load, the system SHALL restore the persisted language. If no preference is stored, the system SHALL fall back to the browser's `navigator.language` setting, then to English.

#### Scenario: Preference survives page reload
- **WHEN** the user selects Spanish and then reloads the page
- **THEN** the app loads in Spanish

#### Scenario: Fresh user defaults to browser language
- **WHEN** no language preference is stored in localStorage and the browser language is `es` or `es-*`
- **THEN** the app loads in Spanish

#### Scenario: Unknown browser language falls back to English
- **WHEN** no language preference is stored and the browser language is not supported (e.g. `fr`)
- **THEN** the app loads in English

### Requirement: All hardcoded UI strings replaced with t() calls
Every user-visible string in `frontend/src/` (labels, placeholders, titles, button text, error messages, aria-labels) SHALL be replaced with a `t('key')` call from `useTranslation()`. No UI string SHALL be hardcoded directly in JSX after this change.

#### Scenario: Component renders in active locale
- **WHEN** a component using `useTranslation()` renders
- **THEN** all text nodes reflect the currently active language

#### Scenario: Missing translation key falls back to English
- **WHEN** a translation key exists in `en.json` but is missing from `es.json`
- **THEN** the English string is displayed (i18next fallback language behavior)

### Requirement: Language switcher in LandingNavbar
The system SHALL provide a language switcher control visible in the LandingNavbar (both desktop and mobile views), so that unauthenticated users can switch language before logging in. The switcher SHALL use the same `LanguageSwitcher` component used in the authenticated Navbar.

#### Scenario: Switch language from landing page desktop
- **WHEN** a visitor on the landing page clicks the language switcher in the desktop navbar
- **THEN** all UI text on the landing page updates immediately to the selected language without a page reload

#### Scenario: Language switcher visible in landing mobile menu
- **WHEN** a visitor opens the mobile menu on the landing page
- **THEN** the language switcher is present and functional

### Requirement: Backend strings are not translated
API error messages and backend-originated strings SHALL remain in English. The frontend SHALL NOT attempt to translate raw API error strings. This is intentional and documented.

#### Scenario: API error shown as-is
- **WHEN** the backend returns an error detail string (e.g. `"Not authenticated"`)
- **THEN** the UI displays it in English regardless of the active locale
