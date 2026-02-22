## ADDED Requirements

### Requirement: Navigation component displays all routes
The navigation component SHALL display links to all primary application routes: Dashboard, Decks, Analytics, and Settings.

#### Scenario: All navigation links are visible on desktop
- **WHEN** the application loads on a desktop viewport (>=768px)
- **THEN** all four navigation links (Dashboard, Decks, Analytics, Settings) are visible in the navbar

#### Scenario: Navigation links are accessible via hamburger menu on mobile
- **WHEN** the application loads on a mobile viewport (<768px)
- **THEN** navigation links are hidden behind a hamburger menu icon
- **THEN** clicking the hamburger icon reveals all navigation links in an overlay

### Requirement: Active route is visually indicated
The navigation component SHALL provide clear visual feedback showing which route is currently active.

#### Scenario: Active link has distinctive styling
- **WHEN** user is on the Dashboard page (path: `/`)
- **THEN** the Dashboard link displays with primary color (indigo-600), semibold font weight, and a 2px bottom border
- **THEN** all other navigation links display in neutral gray color

#### Scenario: Active state updates on navigation
- **WHEN** user clicks the Analytics link from the Dashboard page
- **THEN** the Analytics link becomes the active link with distinctive styling
- **THEN** the Dashboard link returns to neutral inactive styling

### Requirement: Logo navigates to home
The navbar logo/title SHALL be clickable and navigate to the Dashboard (home page).

#### Scenario: Logo click returns user to Dashboard
- **WHEN** user is on the Settings page
- **THEN** user clicks the "DeckDex MTG" logo/title
- **THEN** the application navigates to the Dashboard page (path: `/`)

### Requirement: Navigation is sticky during scroll
The navigation component SHALL remain visible at the top of the viewport when the user scrolls down the page.

#### Scenario: Navbar stays visible while scrolling
- **WHEN** user scrolls down on a page with scrollable content (e.g., Dashboard with many cards)
- **THEN** the navbar remains fixed at the top of the viewport
- **THEN** page content scrolls behind the navbar

### Requirement: Theme toggle is accessible in navbar
The navigation component SHALL integrate the existing ThemeToggle component for theme switching.

#### Scenario: Theme toggle is visible on desktop
- **WHEN** viewing the navbar on desktop (>=768px)
- **THEN** the theme toggle button is visible in the top-right area of the navbar

#### Scenario: Theme toggle is accessible on mobile
- **WHEN** viewing the navbar on mobile (<768px)
- **THEN** the theme toggle is accessible within the hamburger menu overlay

### Requirement: Navigation links show status badges
Navigation links SHALL display status badges (alpha, beta) where applicable to indicate feature maturity.

#### Scenario: Beta badge is shown on Analytics link
- **WHEN** viewing the navigation
- **THEN** the Analytics link displays a "beta" badge next to the link text
- **THEN** the badge uses appropriate styling (small text, rounded pill, indigo colors)

#### Scenario: Alpha badge is shown on Decks link
- **WHEN** viewing the navigation
- **THEN** the Decks link displays an "alpha" badge next to the link text
- **THEN** the badge uses appropriate styling (small text, rounded pill, amber colors)

### Requirement: Mobile menu closes on navigation
The mobile hamburger menu SHALL automatically close when a navigation link is clicked.

#### Scenario: Menu closes after link selection
- **WHEN** mobile menu is open
- **THEN** user clicks the Analytics link
- **THEN** the menu overlay closes
- **THEN** the application navigates to the Analytics page

### Requirement: Mobile menu closes on outside click
The mobile hamburger menu SHALL close when the user clicks outside the menu area or presses the ESC key.

#### Scenario: Menu closes on background click
- **WHEN** mobile menu is open
- **THEN** user clicks on the dimmed background overlay
- **THEN** the menu closes without navigating

#### Scenario: Menu closes on ESC key
- **WHEN** mobile menu is open
- **THEN** user presses the ESC key
- **THEN** the menu closes without navigating

### Requirement: Navigation supports dark mode
The navigation component SHALL adapt its appearance based on the active theme (light or dark mode).

#### Scenario: Navbar styles update for dark mode
- **WHEN** user enables dark mode via the theme toggle
- **THEN** the navbar background changes to dark gray (gray-800)
- **THEN** text colors invert appropriately (light text on dark background)
- **THEN** borders and hover states use dark mode color variants

### Requirement: Hover states provide visual feedback
Navigation links SHALL display hover effects to indicate interactivity (excluding the active link).

#### Scenario: Inactive link shows hover effect
- **WHEN** user hovers over an inactive navigation link
- **THEN** the link text color darkens/brightens (depending on theme)
- **THEN** a smooth transition animation plays (200ms duration)

#### Scenario: Active link has no hover effect
- **WHEN** user hovers over the currently active navigation link
- **THEN** no hover effect is applied (link maintains active styling)
## Requirements
### Requirement: User info displayed in navbar
The navbar SHALL display the authenticated user's avatar and display name in the right section.

#### Scenario: User avatar and name on desktop
- **WHEN** an authenticated user views the navbar on desktop (>=768px)
- **THEN** the navbar right section SHALL display the user's avatar image (circular, small) and display name next to the theme toggle

#### Scenario: User avatar and name on mobile
- **WHEN** an authenticated user views the navbar on mobile (<768px)
- **THEN** the hamburger menu SHALL include the user's avatar, display name, and logout option

#### Scenario: Avatar fallback
- **WHEN** the user has no avatar URL
- **THEN** the navbar SHALL display a fallback icon (e.g., a generic user icon or the first letter of their name)

### Requirement: Logout button in navbar
The navbar SHALL include a logout action for authenticated users.

#### Scenario: Logout button on desktop
- **WHEN** an authenticated user views the navbar on desktop
- **THEN** a logout button (icon or text) SHALL be visible in the navbar right section

#### Scenario: Logout action
- **WHEN** the user clicks the logout button
- **THEN** the app SHALL call `POST /api/auth/logout`, clear auth state, and redirect to `/login`

### Requirement: Navbar hidden on login page
The navbar SHALL NOT be displayed on the `/login` route.

#### Scenario: No navbar on login page
- **WHEN** the current route is `/login`
- **THEN** the navbar component SHALL not render

