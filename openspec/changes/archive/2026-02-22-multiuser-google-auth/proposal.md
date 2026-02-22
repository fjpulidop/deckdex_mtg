# Proposal: Multiuser Google Auth

## Why

DeckDex is currently single-user by default — there is no concept of user accounts, authentication, or data ownership. All cards, decks, and images belong to a single implicit user. Adding multi-user support with Google OAuth lets multiple people use the same DeckDex instance with isolated collections and decks, following industry-standard security practices (no password management, no email verification, token-free frontend).

## What Changes

- **New `users` table** in PostgreSQL to store user identity (Google ID, email, display name, avatar).
- **Google OAuth 2.0 login flow**: backend redirects to Google consent, exchanges authorization code for identity, issues a JWT in an HTTP-only cookie. Frontend never sees tokens.
- **JWT-based authentication middleware** on all API routes (except health and auth endpoints). Every request is authenticated; the current user is injected as a FastAPI dependency.
- **User-scoped data**: `cards` and `decks` tables gain a `user_id` foreign key. All queries filter by the authenticated user. Each user sees only their own collection and decks.
- **Login page** in the frontend with a "Continue with Google" button. Protected routes redirect unauthenticated users to login.
- **User info in navbar**: avatar, display name, and logout button replace the current anonymous layout.
- **Data migration**: existing cards and decks are assigned to the seed user (`admin@deckdex.local`) so no data is lost. The seed user's `google_id` is updated on first real Google login.
- **New users start with an empty collection** — no automatic import or onboarding flow.

## Capabilities

### New Capabilities

- `user-auth`: Google OAuth 2.0 login/logout, JWT cookie issuance and validation, user creation on first login, `/api/auth/*` endpoints, `AuthContext` and `ProtectedRoute` in the frontend, login page UI.

### Modified Capabilities

- `architecture`: New `users` table and auth layer; data flow adds authentication middleware between frontend requests and route handlers; `user_id` scoping on `cards` and `decks`.
- `web-api-backend`: All data endpoints require authentication (JWT cookie); responses scoped to `user_id`; new `/api/auth/google`, `/api/auth/callback`, `/api/auth/me`, `/api/auth/logout` endpoints; `get_current_user` dependency injected into every route.
- `web-dashboard-ui`: Login page added; all pages wrapped in `ProtectedRoute`; navbar shows user avatar, name, and logout button.
- `navigation-ui`: Navbar right section gains user avatar, display name, and logout button (replacing or augmenting the current theme toggle area).
- `decks`: Decks scoped by `user_id`; all deck queries and mutations filter by authenticated user.
- `data-model`: New `users` entity; `cards` and `decks` gain `user_id` foreign key.

## Impact

- **Database**: New migration files — `users` table, `ALTER` on `cards` and `decks` to add `user_id` (nullable first, then backfill and set NOT NULL), indexes.
- **Backend (`backend/api/`)**: New `routes/auth.py`; modified `dependencies.py` with `get_current_user`; every existing route handler gains a `user_id` parameter from the auth dependency; `CollectionRepository` and `DeckRepository` queries add `WHERE user_id = :user_id`.
- **Frontend (`frontend/src/`)**: New `contexts/AuthContext.tsx`, `pages/Login.tsx`, `components/ProtectedRoute.tsx`; modified `App.tsx` (auth wrapping), `Navbar.tsx` (user info + logout).
- **Core (`deckdex/`)**: `CollectionRepository` interface gains optional `user_id` parameter on read/write methods; `PostgresCollectionRepository` and `DeckRepository` implementations filter by `user_id`.
- **Configuration**: Three new environment variables — `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `JWT_SECRET_KEY`. Docker compose updated to pass them through.
- **Dependencies**: `python-jose[cryptography]` added to backend requirements for JWT handling. No new frontend dependencies.
- **External setup**: Google Cloud Console OAuth 2.0 credentials (Web application type) with redirect URI pointing to `/api/auth/callback`.
