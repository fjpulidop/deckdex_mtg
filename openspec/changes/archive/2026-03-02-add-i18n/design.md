## Context

The frontend currently has ~60 hardcoded UI strings spread across ~15 files. The majority are in English, but `Import.tsx` is largely in Spanish and `SettingsModal.tsx` has mixed strings. There is no i18n infrastructure at all. The backend is out of scope — error messages stay in English.

React ecosystem has a clear standard: **i18next + react-i18next** is the most widely adopted solution, well-maintained, and handles everything from simple string lookup to pluralization and interpolation.

## Goals / Non-Goals

**Goals:**
- Single `t('key')` call pattern everywhere in JSX
- EN as source of truth; ES as first translation
- Architecture that allows adding a third language by dropping in a new JSON file
- Language persisted via `localStorage`, with browser-default fallback
- Language switcher accessible from the main Navbar

**Non-Goals:**
- Backend i18n
- ICU message format (overkill for this scale)
- Lazy-loaded namespaces (single flat JSON is enough for ~60 strings)
- RTL support
- Automated CI translation validation

## Decisions

### 1. Library: i18next + react-i18next

**Chosen over**:
- `react-intl` (FormatJS) — heavier, ICU format is overkill for ~60 strings
- Custom context + JSON — would need to reimplement pluralization, interpolation, and tooling
- Paraglide JS — newer, less ecosystem, TypeScript integration still maturing

**Rationale**: i18next is the de-facto standard, well supported with React 19, and the flat JSON format is readable and easy for AI-assisted translation. The `useTranslation()` hook pattern is clean and familiar.

### 2. Single flat JSON per locale (no namespaces)

**Structure**:
```
frontend/src/locales/
  en.json   ← source of truth
  es.json
```

**Chosen over**: namespace-split files (e.g. `en/common.json`, `en/import.json`)

**Rationale**: ~60 strings across ~15 files doesn't justify the overhead of namespace configuration and lazy loading. A single flat file per locale is readable, easy to diff, and trivial to extend. If the app grows to 500+ strings, namespace splitting can be added without changing call-sites (just change the `ns` config).

### 3. Key naming: dot-notation by component/page

```json
{
  "nav.collection": "Collection",
  "nav.analytics": "Analytics",
  "import.title": "Import collection",
  "import.dropzone.hint": "Drag your file here or",
  "filters.searchPlaceholder": "Search cards by name...",
  "common.cancel": "Cancel",
  "common.save": "Save"
}
```

**Rationale**: Flat dot-notation gives context without requiring namespace configuration. `common.*` handles shared strings across components.

### 4. Language switcher: Navbar, flag/abbreviation button

Place a `EN | ES` toggle in the Navbar (desktop) and the mobile menu. No full settings page needed for 2 languages.

**Persistence**: `localStorage.getItem('lang')` → init i18next → `i18next.changeLanguage()` on toggle → `localStorage.setItem('lang', lang)`.

**Fallback chain**: `localStorage` → browser `navigator.language` → `'en'`

### 5. Migration approach: file-by-file, EN strings extracted first

1. Install library + create `i18n.ts` bootstrap
2. Build `en.json` by extracting all current hardcoded strings (English and Spanish unified under EN keys)
3. Generate `es.json` translation (AI-assisted)
4. Migrate components/pages one at a time, starting with `Import.tsx` (most Spanish-heavy)

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Missing a hardcoded string during migration | Grep-based audit after migration; any untranslated string stays as-is (no crash) |
| Key typo causes `t('key')` to return the key itself | TypeScript-typed keys via `i18next-resources-to-typescript` (optional, add later if needed) |
| `es.json` translation quality | AI translation is reviewed against the source; MTG-specific terms (card names, set names) are left in original |
| i18next adds render overhead | Negligible for this scale; i18next is optimized for React via `react-i18next` hooks |

## Migration Plan

1. `npm install i18next react-i18next` in `frontend/`
2. Create `frontend/src/i18n.ts` — init i18next with resources, localStorage detection, fallback to `'en'`
3. Import `i18n.ts` in `main.tsx` (side-effect import)
4. Create `en.json` with all UI strings
5. Create `es.json` with Spanish translations
6. Migrate each file: add `const { t } = useTranslation()` and replace hardcoded strings
7. Add `LanguageSwitcher` component to `Navbar.tsx`
8. Smoke-test both locales

**Rollback**: Revert is safe — if i18n is removed, strings would just go back to hardcoded. No DB or API changes.

## Open Questions

- None. Decisions are well-defined given the scope constraints provided.
