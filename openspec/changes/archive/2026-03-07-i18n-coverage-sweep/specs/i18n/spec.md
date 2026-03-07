## ADDED Requirements

### Requirement: PriceChart strings are translatable
The `PriceChart` component SHALL use `useTranslation()` for all user-visible strings. The locale files SHALL contain keys `priceChart.title` (section heading), `priceChart.noHistory` (empty-state message), and `priceChart.tooltipLabel` (tooltip series label).

#### Scenario: PriceChart renders in Spanish
- **WHEN** the active language is Spanish and `PriceChart` renders with no data points
- **THEN** the heading reads the Spanish translation of "Price History" and the empty-state reads the Spanish translation of "No price history yet — run a price update to start tracking."

#### Scenario: PriceChart tooltip label is translated
- **WHEN** the active language is Spanish and a user hovers over a data point in the chart
- **THEN** the tooltip series label reads the Spanish translation of "Price"

### Requirement: Demo banner strings are translatable
The `Demo` page banner SHALL use `useTranslation()` for all user-visible strings. The locale files SHALL contain keys `demo.bannerText` (main message), `demo.bannerSignIn` (inline CTA link text), and `demo.bannerDismiss` (aria-label for the dismiss button).

#### Scenario: Demo banner renders in Spanish
- **WHEN** the active language is Spanish and a user visits the demo page
- **THEN** the banner message, sign-in link text, and dismiss button aria-label all display Spanish text

### Requirement: ThemeToggle labels are translatable
The `ThemeToggle` component SHALL use `useTranslation()` for its `title` and `aria-label` attributes. The locale files SHALL contain keys `themeToggle.switchToDark` and `themeToggle.switchToLight`.

#### Scenario: ThemeToggle tooltip in Spanish
- **WHEN** the active language is Spanish and the current theme is light
- **THEN** the button's title and aria-label reflect the Spanish translation of "Switch to dark mode"

### Requirement: Navbar aria-labels are translatable
The Navbar SHALL use `useTranslation()` for the user menu button aria-label and the mobile menu toggle button aria-label. The locale files SHALL contain keys `navbar.userMenu` and `navbar.toggleMobileMenu`.

#### Scenario: Screen reader announces Navbar buttons in Spanish
- **WHEN** the active language is Spanish
- **THEN** assistive technology announces the user menu button and mobile menu toggle button using their Spanish aria-label translations

## MODIFIED Requirements

### Requirement: All hardcoded UI strings replaced with t() calls
Every user-visible string in `frontend/src/` (labels, placeholders, titles, button text, error messages, aria-labels) SHALL be replaced with a `t('key')` call from `useTranslation()`. No UI string SHALL be hardcoded directly in JSX after this change.

This requirement now explicitly covers the following previously non-compliant components:
- `ActionButtons.tsx` — process/price-update button labels and dropdown items
- `PriceChart.tsx` — section title, empty-state message, tooltip label
- `InsightValueRenderer.tsx` — uses `i18n.language` (not `'es-ES'`) for `toLocaleString()`
- `InsightDistributionRenderer.tsx` — uses `i18n.language` (not `'es-ES'`) for `toLocaleString()`
- `Demo.tsx` — demo mode banner strings
- `ThemeToggle.tsx` — title and aria-label attributes
- `AuthCallback.tsx` — loading/signing-in spinner text
- `Dashboard.tsx` — "Add card" modal title prop
- `Navbar.tsx` — user menu and mobile menu toggle aria-labels

#### Scenario: Component renders in active locale
- **WHEN** a component using `useTranslation()` renders
- **THEN** all text nodes reflect the currently active language

#### Scenario: Missing translation key falls back to English
- **WHEN** a translation key exists in `en.json` but is missing from `es.json`
- **THEN** the English string is displayed (i18next fallback language behavior)

#### Scenario: Insight number formatting respects active locale
- **WHEN** the active language is English
- **THEN** `InsightValueRenderer` and `InsightDistributionRenderer` format numbers using English locale conventions (e.g., `1,234` not `1.234`)

#### Scenario: Insight number formatting in Spanish
- **WHEN** the active language is Spanish
- **THEN** `InsightValueRenderer` and `InsightDistributionRenderer` format numbers using Spanish locale conventions (e.g., `1.234`)
