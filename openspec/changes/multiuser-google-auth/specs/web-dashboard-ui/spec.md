## ADDED Requirements

### Requirement: Login page replaces anonymous access
The frontend SHALL display a login page for unauthenticated users instead of showing the dashboard directly.

#### Scenario: Unauthenticated user sees login page
- **WHEN** an unauthenticated user opens the application
- **THEN** the app SHALL redirect to `/login` and display a "Continue with Google" button

#### Scenario: Authenticated user sees dashboard
- **WHEN** an authenticated user opens the application at `/`
- **THEN** the app SHALL display the dashboard with that user's cards and stats

### Requirement: All pages wrapped in ProtectedRoute
Every page (Dashboard, Settings, Analytics, Decks) SHALL be wrapped in a `ProtectedRoute` component that redirects to `/login` when the user is not authenticated.

#### Scenario: ProtectedRoute redirects unauthenticated user
- **WHEN** an unauthenticated user navigates to `/settings`
- **THEN** the app SHALL redirect to `/login`

#### Scenario: ProtectedRoute allows authenticated user
- **WHEN** an authenticated user navigates to `/settings`
- **THEN** the app SHALL render the Settings page normally

### Requirement: Loading state during auth check
The app SHALL show a loading indicator while checking authentication status on mount (not the login page and not the dashboard).

#### Scenario: Loading spinner during auth check
- **WHEN** the app is checking the authentication status (`isLoading = true`)
- **THEN** the app SHALL display a centered loading spinner or skeleton
- **THEN** the app SHALL NOT flash the login page or the dashboard
