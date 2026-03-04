## ADDED Requirements

### Requirement: Language switcher in LandingNavbar
The system SHALL provide a language switcher control visible in the LandingNavbar (both desktop and mobile views), so that unauthenticated users can switch language before logging in. The switcher SHALL use the same `LanguageSwitcher` component used in the authenticated Navbar.

#### Scenario: Switch language from landing page desktop
- **WHEN** a visitor on the landing page clicks the language switcher in the desktop navbar
- **THEN** all UI text on the landing page updates immediately to the selected language without a page reload

#### Scenario: Language switcher visible in landing mobile menu
- **WHEN** a visitor opens the mobile menu on the landing page
- **THEN** the language switcher is present and functional
