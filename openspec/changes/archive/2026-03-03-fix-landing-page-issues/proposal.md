## Why

The landing page (pre-login) has two UX issues: the Jobs bottom bar pill is visible to unauthenticated users where it serves no purpose, and the language switcher added in the multi-language feature was only integrated into the authenticated Navbar — not the LandingNavbar.

## What Changes

- **Hide JobsBottomBar on public pages**: Conditionally render `<JobsBottomBar />` only on authenticated routes (exclude `/` landing and `/login`). This aligns with the global-jobs-ui spec which states the bar should appear "when jobs exist" on "main views (Dashboard, Settings)".
- **Add LanguageSwitcher to LandingNavbar**: Include the existing `<LanguageSwitcher />` component in the landing page navbar (both desktop and mobile views), so visitors can switch language before logging in.

## Non-goals

- No changes to the LanguageSwitcher component itself.
- No changes to JobsBottomBar internals — only its render condition in App.tsx.
- No new translations or locale keys needed.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `i18n`: Language switcher must also be visible on the LandingNavbar, not only the authenticated Navbar.
- `global-jobs-ui`: Bar must not render on public pages (landing, login).

## Impact

- `frontend/src/App.tsx` — conditional rendering of `<JobsBottomBar />`
- `frontend/src/components/landing/LandingNavbar.tsx` — add `<LanguageSwitcher />`
- `openspec/specs/i18n/spec.md` — delta spec for landing navbar requirement
- `openspec/specs/global-jobs-ui/spec.md` — delta spec for public page exclusion
