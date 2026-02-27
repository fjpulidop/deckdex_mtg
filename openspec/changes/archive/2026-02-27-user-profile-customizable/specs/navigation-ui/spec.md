## MODIFIED Requirements

### Requirement: Navigation component displays all routes
The navigation component SHALL display links to the primary application routes: Dashboard, Decks, and Analytics. Settings SHALL NOT appear as a primary nav link — it is accessed via the user dropdown.

#### Scenario: Primary navigation links are visible on desktop
- **WHEN** the application loads on a desktop viewport (>=768px)
- **THEN** exactly three navigation links are visible in the navbar: Dashboard, Decks, Analytics
- **THEN** Settings SHALL NOT appear as a navbar link

#### Scenario: Navigation links are accessible via hamburger menu on mobile
- **WHEN** the application loads on a mobile viewport (<768px)
- **THEN** navigation links are hidden behind a hamburger menu icon
- **THEN** clicking the hamburger icon reveals Dashboard, Decks, and Analytics links in an overlay

### Requirement: User dropdown contains Profile, Settings, and Logout
Clicking the user avatar SHALL open a dropdown with three entries: Profile, Settings, and Logout.

#### Scenario: Dropdown items on desktop
- **WHEN** an authenticated user clicks their avatar on desktop (>=768px)
- **THEN** a dropdown SHALL appear with three items in order: "Profile", "Settings", "Logout"
- **THEN** Profile and Settings SHALL be separated from Logout by a visual divider

#### Scenario: Profile entry opens ProfileModal
- **WHEN** the user clicks "Profile" in the dropdown
- **THEN** the dropdown SHALL close
- **THEN** the `ProfileModal` SHALL open

#### Scenario: Settings entry opens SettingsModal
- **WHEN** the user clicks "Settings" in the dropdown
- **THEN** the dropdown SHALL close
- **THEN** the `SettingsModal` SHALL open

#### Scenario: Logout entry triggers logout
- **WHEN** the user clicks "Logout" in the dropdown
- **THEN** the frontend SHALL call `POST /api/auth/logout`, clear auth state, and redirect to `/login`

### Requirement: User info displayed in navbar
The navbar SHALL display the authenticated user's avatar and display name in the right section.

#### Scenario: User avatar on desktop
- **WHEN** an authenticated user views the navbar on desktop (>=768px)
- **THEN** the navbar right section SHALL display the user's avatar as a circular image filling the avatar button
- **THEN** clicking the avatar SHALL open the user dropdown

#### Scenario: User name on desktop
- **WHEN** an authenticated user views the navbar on desktop (>=768px)
- **THEN** the navbar SHALL display the user's `display_name` (or `email` as fallback) next to the avatar button

#### Scenario: Avatar fallback icon
- **WHEN** the user has no `avatar_url`
- **THEN** the navbar SHALL display a generic user icon in the circular avatar area

#### Scenario: Avatar displays uploaded photo
- **WHEN** the user has an `avatar_url` (base64 data URI or URL)
- **THEN** the circular avatar SHALL render the image filling the circle via `object-cover`

## REMOVED Requirements

### Requirement: Settings is a top-level navigation link
**Reason**: Settings moved to user dropdown as a modal to improve UX — settings are contextual to the user session, not a primary destination.
**Migration**: Access Settings from the user avatar dropdown in the navbar.
