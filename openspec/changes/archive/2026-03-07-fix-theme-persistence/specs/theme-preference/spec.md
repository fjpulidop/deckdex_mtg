# Delta spec for: theme-preference
# Base spec: openspec/specs/theme-preference/spec.md

## MODIFIED Requirements

### Requirement: Persist (cross-tab sync)
The theme preference SHALL be synchronized across browser tabs in real time. When the user changes the theme in one tab, all other open tabs SHALL update their applied theme within one render cycle — without requiring a page reload.

**Implementation mechanism:** `ThemeProvider` SHALL listen to the `storage` event on `window`. When the event fires with `key === 'deckdex-theme'` and a valid value (`'dark'` or `'light'`), the provider SHALL update its React state and re-apply the theme class to `document.documentElement`.

#### Scenario: Theme change propagates to a second tab
- **WHEN** the user switches from dark to light in Tab A
- **THEN** Tab A SHALL immediately show light mode
- **AND** Tab B (same origin, same app) SHALL update to light mode within one render cycle without a page reload

#### Scenario: Invalid or unrelated storage event is ignored
- **WHEN** a `storage` event fires with `key !== 'deckdex-theme'` or an unrecognized value
- **THEN** the theme provider SHALL ignore the event and make no changes

## ADDED Requirements

### Requirement: Login page respects active theme
Every page in the web dashboard — including the Login/unauthenticated page — SHALL apply the active theme. No page SHALL contain hardcoded light-only or dark-only Tailwind classes without the corresponding `dark:` variant.

#### Scenario: Login page in dark mode
- **WHEN** the user's stored theme is `dark` (or no preference — default is dark)
- **AND** the user visits the `/login` route
- **THEN** the login page SHALL display a dark-themed card container, dark text, and a dark-styled button with no bright-white elements

#### Scenario: Login page in light mode
- **WHEN** the user switches to light mode and then navigates to or views `/login`
- **THEN** the login page SHALL display a light-themed card container, dark text on white background, and appropriate light-mode button styling

#### Scenario: Login loading state in dark mode
- **WHEN** the auth state is loading and the user's theme is dark
- **THEN** the full-screen loading spinner container SHALL have a dark background, not the default light gray

### Requirement: No class-based dark mode via OS media query
Components that need dark-mode overrides SHALL use **Tailwind `dark:` utility variants** or theme-context-conditioned inline styles. Components SHALL NOT use `@media (prefers-color-scheme: dark)` CSS for in-app dark mode detection, because DeckDex uses class-based dark mode (`dark` class on `<html>`), not OS-preference-based detection.

#### Scenario: Insight comparison cards in dark mode (app toggle)
- **WHEN** the user has toggled the app to dark mode (OS may be light)
- **THEN** the `InsightComparisonRenderer` comparison cards SHALL show dark-tinted backgrounds (green-tinted for present, red-tinted for absent)

#### Scenario: Insight comparison cards in light mode (app toggle)
- **WHEN** the user has toggled the app to light mode (OS may be dark)
- **THEN** the `InsightComparisonRenderer` comparison cards SHALL show light-tinted backgrounds appropriate for light mode
