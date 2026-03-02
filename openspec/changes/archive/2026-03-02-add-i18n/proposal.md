## Why

The frontend UI has hardcoded text strings scattered across components, with an inconsistent mix of English and Spanish — most of the app is in English but `Import.tsx` and parts of `SettingsModal.tsx` are in Spanish. This makes the UX incoherent and the codebase hard to maintain. Adding proper i18n now establishes a clean foundation and enables the app to serve users in their preferred language.

## What Changes

- Install `i18next` and `react-i18next` in the frontend
- Create locale files `en.json` (source of truth) and `es.json`
- Replace all hardcoded UI strings in components and pages with `t('key')` calls
- Add a language selector UI control (e.g. in the Navbar or Settings)
- Persist the chosen language to `localStorage`
- Backend strings (API error messages) remain in English — not in scope

## Capabilities

### New Capabilities
- `i18n`: Internationalization support for the React frontend — locale files, language detection, language switcher, and `useTranslation` hooks across all components.

### Modified Capabilities
<!-- No existing spec-level requirements change; this is purely additive infrastructure -->

## Non-goals

- Backend i18n (API errors stay in English)
- More than 2 initial languages (EN + ES); architecture must support adding more easily
- Automatic language detection beyond `localStorage` preference + browser default fallback
- Translation of card names, set names, or Scryfall-sourced content

## Impact

- **Frontend only**: all changes in `frontend/src/`
- New dependency: `i18next`, `react-i18next`
- New files: `frontend/src/i18n.ts`, `frontend/src/locales/en.json`, `frontend/src/locales/es.json`
- All `.tsx` components and pages that contain hardcoded UI strings
- `Navbar.tsx` or `Settings` area gains a language switcher control
