## Context

The i18n capability was delivered with a solid foundation: i18next + react-i18next, `LanguageSwitcher`, localStorage persistence, and comprehensive locale files (`en.json` / `es.json`). However, a post-delivery audit identified 8 components that were never wired to `useTranslation()` — they continue to render hardcoded English strings — and 2 insight renderers that hardcode the locale identifier `'es-ES'` in `toLocaleString()` calls, producing Spanish number formatting regardless of the active language.

This design describes the corrective implementation to achieve full coverage as required by the `i18n` spec.

## Goals / Non-Goals

**Goals:**
- Wire `useTranslation()` in all 8 components that currently bypass i18n
- Fix the `es-ES` locale bug in both insight renderers
- Add the minimum set of new translation keys required by the un-wired components
- Maintain structural parity between `en.json` and `es.json`

**Non-Goals:**
- Translating backend API error strings (spec explicitly excludes these)
- Adding new languages (fr, de, etc.)
- Refactoring the i18n infrastructure itself
- Auditing or modifying landing-page-only components not listed in the proposal

## Decisions

### Decision 1: Use `i18n.language` for `toLocaleString()` locale

**Problem**: `InsightValueRenderer` and `InsightDistributionRenderer` call `toLocaleString('es-ES', ...)` which forces Spanish number formatting globally.

**Decision**: Replace the hardcoded `'es-ES'` string with `i18n.language` from the `useTranslation()` hook. Both components will call `const { i18n } = useTranslation()` and pass `i18n.language` as the locale argument.

**Rationale**: `i18n.language` is the canonical source of truth for the currently active locale in the react-i18next system. It matches the value persisted to localStorage and matches what all other components observe. This is a one-line fix per file with no structural changes.

**Alternative considered**: Using `navigator.language` directly. Rejected because it doesn't reflect the user's in-app language selection — the user could switch the app to English while the browser language is Spanish, and the number format would still show Spanish.

### Decision 2: Minimal new key additions to locale files

**Problem**: Some components have hardcoded strings with no corresponding translation key yet (`PriceChart`, `Demo`, `ThemeToggle`, `Navbar`).

**Decision**: Add the minimum keys needed to represent these strings. New keys follow the existing namespace pattern: `priceChart.*`, `demo.banner*`, `themeToggle.*`, `navbar.userMenu`, `navbar.toggleMobileMenu`. All keys are added to both `en.json` and `es.json` simultaneously to maintain parity.

**Rationale**: The existing locale structure uses component-scoped namespaces consistently. Deviating from this pattern would introduce inconsistency. Spanish translations for the new keys must be provided immediately to avoid relying on i18next fallback behavior in production.

**Alternative considered**: Reusing keys from `common.*`. Some strings (e.g., `'Signing in…'`) could map to `login.loading` which already exists. This approach is used where a match exists (AuthCallback uses `login.loading`, Dashboard uses `dashboard.addCard`) to avoid key duplication.

### Decision 3: ActionButtons — wire existing keys, change no structure

**Problem**: `ActionButtons.tsx` has complete key coverage in both locale files (`actionButtons.*`) but never calls `useTranslation()`.

**Decision**: Add `const { t } = useTranslation();` and replace each hardcoded string with its corresponding `t('actionButtons.*')` call. No new keys needed.

**Rationale**: The keys were defined in anticipation of this wiring. This is purely mechanical — zero risk of key mismatch or missing translation.

### Decision 4: AuthCallback uses `login.loading` — no new key

**Problem**: `AuthCallback` renders `'Signing in…'` hardcoded.

**Decision**: Use the existing `login.loading` key (`"Loading..."` in en, `"Cargando..."` in es) rather than introducing a new `login.signingIn` key.

**Rationale**: The two strings are semantically equivalent in context (a spinner screen during auth flow). Creating a second key for marginally different wording adds key proliferation with no user-facing benefit. If a distinct string is ever needed, the key can be added then.

### Decision 5: Navbar aria-labels — add 2 new keys

**Problem**: `Navbar.tsx` has `aria-label="User menu"` and `aria-label="Toggle mobile menu"` hardcoded.

**Decision**: Add `navbar.userMenu` and `navbar.toggleMobileMenu` keys to both locale files. The rest of `Navbar.tsx` already uses `t()` extensively — this brings the two remaining aria-labels in line.

**Rationale**: Aria-labels are user-visible in the accessibility tree and must be translated for screen reader users in Spanish. They cannot be skipped.

## Risks / Trade-offs

**[Risk] Locale identifier format mismatch**: `i18n.language` may return `'en'` or `'en-US'` depending on browser/i18next configuration. `toLocaleString()` accepts both formats natively, so this is not a functional risk. However, if i18next ever normalizes to a format like `'en_US'` (underscore), `toLocaleString` would silently fall back to the default locale. Mitigation: the i18next setup in this project uses standard BCP 47 codes (`'en'`, `'es'`) as language keys, which are fully compatible with `Intl` APIs.

**[Risk] Missing Spanish translations for new keys**: If `es.json` is submitted without the new keys, i18next silently falls back to English. This is acceptable behavior but should be avoided. Mitigation: tasks require both locale files to be updated in the same task.

**[Risk] `AuthCallback` uses `login.loading` which reads `"Loading..."` in English**: The original string was `"Signing in…"` which is slightly more specific. This is a minor UX regression. Mitigation: acceptable trade-off to avoid key proliferation; the spinner is visible for < 2 seconds.

## Migration Plan

No migration required. All changes are purely additive (new keys) or in-place replacements (hardcoded string → `t()` call). No API changes, no data migrations, no breaking changes. The change can be deployed as a standard frontend build with no coordination needed.

## Open Questions

None. All decisions above are unambiguous given the current codebase state.
