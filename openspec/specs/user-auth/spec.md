# user-auth Specification

## Purpose
TBD - created by archiving change multiuser-google-auth. Update Purpose after archive.
## Requirements
### Requirement: Google OAuth 2.0 login flow
The system SHALL authenticate users via Google OAuth 2.0. The backend SHALL handle the full authorization code exchange — the frontend SHALL NOT receive or handle authorization codes or tokens.

#### Scenario: User initiates login
- **WHEN** the frontend navigates the browser to `GET /api/auth/google`
- **THEN** the backend SHALL redirect to Google's OAuth 2.0 consent screen with scopes `openid email profile` and the configured `redirect_uri`

#### Scenario: Google callback creates new user
- **WHEN** Google redirects to `GET /api/auth/callback` with a valid authorization code and no user with that Google ID exists
- **THEN** the backend SHALL exchange the code for an ID token, extract user info (sub, email, name, picture), create a new row in the `users` table, sign a JWT, set it as an HTTP-only cookie, and redirect the browser to the frontend root (`/`)

#### Scenario: Google callback for existing user
- **WHEN** Google redirects to `GET /api/auth/callback` with a valid authorization code and a user with that Google ID already exists
- **THEN** the backend SHALL update `last_login` (and `display_name`/`avatar_url` if changed), sign a JWT, set it as an HTTP-only cookie, and redirect the browser to the frontend root (`/`)

#### Scenario: Seed user first login
- **WHEN** Google redirects with a valid code for email `admin@deckdex.local` and a seed user with `google_id = '__seed_pending__'` exists for that email
- **THEN** the backend SHALL update the seed user's `google_id` to the real Google `sub` value, update `last_login`, sign a JWT, and redirect as normal

#### Scenario: OAuth error
- **WHEN** Google redirects to the callback with an error parameter or the code exchange fails
- **THEN** the backend SHALL redirect the browser to `/login?error=auth_failed`

### Requirement: JWT cookie authentication
The backend SHALL issue and validate JWTs stored in HTTP-only cookies for stateless authentication.

#### Scenario: JWT cookie properties
- **WHEN** the backend sets the JWT cookie after successful OAuth
- **THEN** the cookie SHALL have `httpOnly=True`, `samesite='lax'`, `path='/'`, `max_age=3600` (1 hour), and `secure=True` when not in development mode

#### Scenario: JWT payload
- **WHEN** the backend signs a JWT
- **THEN** the payload SHALL contain `sub` (user database ID as string), `email`, `display_name`, `picture`, `jti` (UUID for token revocation), and `exp` (expiration timestamp)

#### Scenario: Valid JWT on request
- **WHEN** an API request includes a valid, non-expired JWT in the cookie
- **THEN** the backend SHALL extract the user payload and make it available to the route handler

#### Scenario: Missing or expired JWT
- **WHEN** an API request to a protected endpoint has no JWT cookie or the JWT is expired/invalid
- **THEN** the backend SHALL return HTTP 401 Unauthorized

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

#### Scenario: POST /api/auth/refresh — silent token refresh
- **WHEN** an authenticated client calls `POST /api/auth/refresh`
- **THEN** the backend SHALL validate the current JWT, blacklist the old token's JTI, issue a new JWT with a fresh JTI and expiration, set it as an HTTP-only cookie, and return `{"ok": true}`

#### Scenario: POST /api/auth/refresh — expired token
- **WHEN** a client calls `POST /api/auth/refresh` with an expired or invalid JWT
- **THEN** the backend SHALL return HTTP 401

#### Scenario: POST /api/auth/logout
- **WHEN** a client calls `POST /api/auth/logout`
- **THEN** the backend SHALL blacklist the current token's JTI, clear the JWT cookie, and return HTTP 200

### Requirement: Public endpoints do not require authentication
The endpoints `/api/health` and all `/api/auth/*` routes SHALL be accessible without authentication.

#### Scenario: Health check without auth
- **WHEN** an unauthenticated client calls `GET /api/health`
- **THEN** the backend SHALL return 200 with the health response

#### Scenario: Auth routes without auth
- **WHEN** an unauthenticated client calls any `/api/auth/*` endpoint
- **THEN** the backend SHALL process the request normally (no 401)

### Requirement: Login page
The frontend SHALL display a login page at route `/login` for unauthenticated users.

#### Scenario: Login page content
- **WHEN** an unauthenticated user navigates to `/login`
- **THEN** the page SHALL display the DeckDex MTG logo/title and a "Continue with Google" button

#### Scenario: Login button action
- **WHEN** the user clicks "Continue with Google"
- **THEN** the browser SHALL navigate to `/api/auth/google` (full page redirect)

#### Scenario: Login page with error
- **WHEN** the user arrives at `/login?error=auth_failed`
- **THEN** the page SHALL display an error message (e.g., "Authentication failed. Please try again.")

#### Scenario: Login page when already authenticated
- **WHEN** an authenticated user navigates to `/login`
- **THEN** the page SHALL redirect to `/` (dashboard)

### Requirement: Protected routes
All frontend routes except `/login` SHALL require authentication.

#### Scenario: Unauthenticated access to protected route
- **WHEN** an unauthenticated user navigates to any route other than `/login` (e.g., `/`, `/decks`, `/analytics`, `/settings`)
- **THEN** the app SHALL redirect to `/login`

#### Scenario: Authenticated access to protected route
- **WHEN** an authenticated user navigates to any protected route
- **THEN** the app SHALL render the route normally

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

### Requirement: User profile is updatable via API
The backend SHALL expose an endpoint for authenticated users to update their own profile.

#### Scenario: Repository updates user profile fields
- **WHEN** `update_user_profile(user_id, display_name, avatar_url)` is called on the repository
- **THEN** the method SHALL update only the provided non-None fields in the `users` table
- **THEN** the method SHALL return the full updated user row as a dict

### Requirement: Logout
The frontend SHALL allow authenticated users to log out.

#### Scenario: User logs out
- **WHEN** the user triggers logout (e.g., clicking logout button in navbar)
- **THEN** the frontend SHALL call `POST /api/auth/logout`, clear the auth context, and redirect to `/login`

### Requirement: Environment configuration
The backend SHALL require three environment variables for auth functionality.

#### Scenario: Required environment variables
- **WHEN** the backend starts with auth enabled
- **THEN** the environment SHALL provide `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and `JWT_SECRET_KEY`

#### Scenario: Missing auth environment variables
- **WHEN** any of the three auth environment variables is missing and a user hits an auth endpoint
- **THEN** the backend SHALL return HTTP 500 with a clear error message indicating which variable is missing

### Requirement: Token revocation via JTI blacklist
The backend SHALL maintain an in-memory blacklist of revoked token JTIs to prevent reuse of old tokens after refresh or logout.

#### Scenario: Blacklisted token rejected
- **WHEN** a request includes a JWT whose `jti` has been blacklisted
- **THEN** the backend SHALL return HTTP 401 Unauthorized

#### Scenario: Blacklist cleanup
- **WHEN** a blacklisted JTI's token has expired (based on the stored `exp` timestamp)
- **THEN** the system SHALL remove the entry from the blacklist during periodic cleanup (every 10 minutes)

### Requirement: Avatar proxy endpoint
The backend SHALL provide `GET /api/auth/avatar/{user_id}` to serve user avatars from a local cache, avoiding external URL leakage to the browser.

#### Scenario: Avatar served from cache
- **WHEN** an authenticated client requests `GET /api/auth/avatar/{user_id}` and the avatar is cached locally
- **THEN** the backend SHALL return the cached image file with the correct content-type (stored in a `.ct` sidecar file)

#### Scenario: Avatar cache miss
- **WHEN** the avatar is not cached locally
- **THEN** the backend SHALL validate the stored `avatar_url` against the domain allowlist, download the image (max 2MB), write it atomically to disk with a `.ct` sidecar, and serve it

#### Scenario: Avatar URL domain validation
- **WHEN** the stored `avatar_url` is not HTTPS or its domain is not in the allowlist (`googleusercontent.com`, `gravatar.com`, `avatars.githubusercontent.com`)
- **THEN** the backend SHALL return HTTP 400

#### Scenario: No avatar
- **WHEN** the user has no `avatar_url` in the database
- **THEN** the backend SHALL return HTTP 404

### Requirement: Profile update avatar URL validation
The `PATCH /api/auth/profile` endpoint SHALL validate `avatar_url` against a domain allowlist to prevent SSRF.

#### Scenario: Valid avatar URL accepted
- **WHEN** `avatar_url` is an HTTPS URL from an allowed domain
- **THEN** the backend SHALL accept the update

#### Scenario: Invalid avatar URL rejected
- **WHEN** `avatar_url` is not HTTPS or its domain is not in the allowlist
- **THEN** the backend SHALL return HTTP 400

### Requirement: Frontend 401 interceptor with silent refresh
The frontend API client SHALL automatically handle 401 responses by attempting a silent token refresh before redirecting to login.

#### Scenario: 401 triggers refresh then retry
- **WHEN** an API call returns 401 (except `/auth/refresh` and `/auth/me`)
- **THEN** the client SHALL call `POST /api/auth/refresh`, and if successful, retry the original request

#### Scenario: Concurrent 401s deduplicated
- **WHEN** multiple API calls receive 401 simultaneously
- **THEN** only one refresh request SHALL be in-flight; all waiting calls SHALL share the same refresh promise

#### Scenario: Refresh failure redirects to login
- **WHEN** the refresh attempt fails (e.g., token fully expired)
- **THEN** the client SHALL redirect to `/login`

### Requirement: Frontend avatar via proxy
The frontend SHALL display user avatars via the backend proxy endpoint instead of external URLs.

#### Scenario: AuthContext uses proxy URL
- **WHEN** `/api/auth/me` indicates the user has an avatar
- **THEN** `AuthContext` SHALL set `avatar_url` to `/api/auth/avatar/{user_id}` (the proxy endpoint)

