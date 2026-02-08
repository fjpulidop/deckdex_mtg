# Theme preference

User-selectable UI theme (dark / light) for the web dashboard, with dark as the default and the choice persisted in the browser.

## ADDED Requirements

### Requirement: Default theme is dark

When the user has not previously chosen a theme (or the stored value is missing or invalid), the system SHALL display the dashboard in dark theme.

#### Scenario: First visit or no stored preference
- **WHEN** the user opens the dashboard and no valid theme is stored (e.g. first visit or cleared storage)
- **THEN** the UI is rendered in dark theme (dark backgrounds and light text where applicable)

#### Scenario: Invalid stored value
- **WHEN** the stored theme value is not "dark" or "light" (e.g. corrupted or from an older format)
- **THEN** the system SHALL treat it as no preference and SHALL display dark theme

### Requirement: User can switch between dark and light theme

The system SHALL provide a control (e.g. in the main navigation) that allows the user to select dark or light theme. The control SHALL be available on Dashboard and Settings so the user can change theme from any main page.

#### Scenario: Switch to light theme
- **WHEN** the user selects light theme via the theme control
- **THEN** the UI switches immediately to light theme (light backgrounds and dark text)

#### Scenario: Switch to dark theme
- **WHEN** the user selects dark theme via the theme control
- **THEN** the UI switches immediately to dark theme

#### Scenario: Theme control visible in navigation
- **WHEN** the user is on the Dashboard or Settings page
- **THEN** the theme control (e.g. toggle or icon) is visible in the shared navigation area

### Requirement: Theme choice is persisted

The system SHALL persist the user's theme choice in the browser (e.g. localStorage) so that the same theme is used on subsequent visits and across tabs of the same origin.

#### Scenario: Persisted theme restored on reload
- **WHEN** the user has previously selected light theme and then reloads the page or opens the app in a new tab
- **THEN** the UI is shown in light theme without the user having to select it again

#### Scenario: Persisted theme restored after selecting dark
- **WHEN** the user has previously selected dark theme and then returns to the app
- **THEN** the UI is shown in dark theme

#### Scenario: Change persists immediately
- **WHEN** the user changes the theme via the control
- **THEN** the new choice is stored immediately so that the next load uses it

### Requirement: Theme applies consistently across the app

When a theme (dark or light) is active, the system SHALL apply it consistently to the main layout, navigation, tables, filters, modals, buttons, and error/feedback UI so that no area remains in a fixed light-only or dark-only appearance that contradicts the selected theme.

#### Scenario: Dashboard and Settings share the same theme
- **WHEN** the user has selected a theme and navigates between Dashboard and Settings
- **THEN** both pages use the same theme (dark or light)

#### Scenario: Modals and overlays respect theme
- **WHEN** a modal or overlay is open (e.g. card form, progress, error)
- **THEN** its background and text follow the currently selected theme
