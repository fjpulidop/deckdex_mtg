## MODIFIED Requirements

### Requirement: Auth API endpoints
The backend SHALL expose authentication endpoints under `/api/auth/`.

#### Scenario: GET /api/auth/google
- **WHEN** a client calls `GET /api/auth/google`
- **THEN** the backend SHALL return HTTP 302 redirect to Google's OAuth consent URL

#### Scenario: GET /api/auth/callback
- **WHEN** Google redirects to `GET /api/auth/callback` with a valid code
- **THEN** the backend SHALL process the OAuth flow and redirect to the frontend with a JWT cookie set

#### Scenario: GET /api/auth/me — reads from database
- **WHEN** an authenticated client calls `GET /api/auth/me`
- **THEN** the backend SHALL extract the user ID from the JWT cookie (`sub` claim)
- **THEN** the backend SHALL query the `users` table by that ID
- **THEN** the backend SHALL return `{ id, email, display_name, avatar_url }` from the database row (NOT from the JWT payload)

#### Scenario: GET /api/auth/me unauthenticated
- **WHEN** an unauthenticated client calls `GET /api/auth/me`
- **THEN** the backend SHALL return HTTP 401

#### Scenario: PATCH /api/auth/profile — update display name
- **WHEN** an authenticated client calls `PATCH /api/auth/profile` with `{ "display_name": "New Name" }`
- **THEN** the backend SHALL update `display_name` in the `users` table for the current user
- **THEN** the backend SHALL return the updated `{ id, email, display_name, avatar_url }`

#### Scenario: PATCH /api/auth/profile — update avatar
- **WHEN** an authenticated client calls `PATCH /api/auth/profile` with `{ "avatar_url": "data:image/jpeg;base64,..." }`
- **THEN** the backend SHALL update `avatar_url` in the `users` table for the current user
- **THEN** the backend SHALL return the updated `{ id, email, display_name, avatar_url }`

#### Scenario: PATCH /api/auth/profile — request too large
- **WHEN** an authenticated client calls `PATCH /api/auth/profile` with a body exceeding 500KB
- **THEN** the backend SHALL return HTTP 413 Payload Too Large

#### Scenario: PATCH /api/auth/profile unauthenticated
- **WHEN** an unauthenticated client calls `PATCH /api/auth/profile`
- **THEN** the backend SHALL return HTTP 401

#### Scenario: POST /api/auth/logout
- **WHEN** a client calls `POST /api/auth/logout`
- **THEN** the backend SHALL clear the JWT cookie (set `max_age=0`) and return HTTP 200

### Requirement: Auth state management
The frontend SHALL manage authentication state via a React context (`AuthContext`).

#### Scenario: Auth check on app mount
- **WHEN** the app mounts
- **THEN** `AuthContext` SHALL call `GET /api/auth/me` to check if the user is authenticated

#### Scenario: Auth context provides user data
- **WHEN** the auth check succeeds
- **THEN** `AuthContext` SHALL provide `{ user: { id, email, display_name, avatar_url }, isAuthenticated: true, isLoading: false, refreshUser }` to child components

#### Scenario: Auth context refreshUser updates state
- **WHEN** a component calls `refreshUser()`
- **THEN** `AuthContext` SHALL re-call `GET /api/auth/me` and update the `user` state with the fresh database values

#### Scenario: Auth context provides unauthenticated state
- **WHEN** the auth check returns 401
- **THEN** `AuthContext` SHALL provide `{ user: null, isAuthenticated: false, isLoading: false }` to child components

#### Scenario: Loading state during auth check
- **WHEN** the auth check is in progress
- **THEN** `AuthContext` SHALL provide `{ user: null, isAuthenticated: false, isLoading: true }` and the app SHALL display a loading indicator (not the login page)

## ADDED Requirements

### Requirement: User profile is updatable via API
The backend SHALL expose an endpoint for authenticated users to update their own profile.

#### Scenario: Repository updates user profile fields
- **WHEN** `update_user_profile(user_id, display_name, avatar_url)` is called on the repository
- **THEN** the method SHALL update only the provided non-None fields in the `users` table
- **THEN** the method SHALL return the full updated user row as a dict
