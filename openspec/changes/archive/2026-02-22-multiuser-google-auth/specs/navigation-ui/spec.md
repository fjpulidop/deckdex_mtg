## ADDED Requirements

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
