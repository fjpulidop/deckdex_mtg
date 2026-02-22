# Design: Multiuser Google Auth

## Context

DeckDex is a single-user MTG card collection manager backed by PostgreSQL. The backend is FastAPI (port 8000) with REST + WebSocket; the frontend is React/Vite (port 5173) with TanStack Query. There is no authentication — every request hits the API anonymously and all data is shared. Tables `cards`, `decks`, `deck_cards`, and `card_images` exist with no ownership column. A `sessions` table was created during an earlier OAuth-for-Sheets-import change but is unused for user auth. The frontend uses `credentials: 'include'` on all fetch calls already, which means cookies will be sent automatically once set.

Existing data (cards, decks) belongs to the project owner (`fj.pulidop@gmail.com`) and must be preserved during migration.

## Goals / Non-Goals

**Goals:**

- Google OAuth 2.0 as the sole login method; backend handles the full OAuth code exchange — frontend never touches tokens.
- JWT stored in an HTTP-only, secure, SameSite cookie — stateless auth with no server-side session lookup per request.
- User-scoped data isolation: each user sees only their own cards, decks, and images.
- Seed migration: assign all existing cards and decks to `fj.pulidop@gmail.com`.
- Clean login page with "Continue with Google" button; protected routes redirect to `/login`.
- User info (avatar, name) and logout in the navbar.

**Non-Goals:**

- Other OAuth providers (GitHub, Discord) — Google only for now.
- Role-based access control or admin features.
- Refresh token rotation or token blacklisting — JWT expiry is sufficient for the current scale.
- Onboarding flow or automatic import for new users — empty collection on signup.
- Migrating the existing `sessions` table — it will be left as-is (unused).

## Decisions

### 1. OAuth flow: backend-only code exchange

**Decision:** The frontend links to `GET /api/auth/google` which redirects to Google's consent screen. Google redirects back to `GET /api/auth/callback` on the backend. The backend exchanges the authorization code for an ID token, extracts user info (sub, email, name, picture), upserts the user in the `users` table, signs a JWT, sets it as an HTTP-only cookie, and redirects the browser to the frontend root (`/`).

**Rationale:** The authorization code and tokens never reach the browser. One redirect URI to configure in Google Cloud. The frontend already sends cookies via `credentials: 'include'`.

**Alternatives considered:** PKCE flow with frontend handling the redirect — adds complexity, exposes the code to JS briefly, requires an extra POST from frontend to backend.

### 2. JWT in HTTP-only cookie (not localStorage)

**Decision:** The JWT is stored in a cookie with `httpOnly=True`, `secure=True` (production), `samesite='lax'`, `path='/'`, `max_age=3600` (1 hour). The JWT payload contains `sub` (user ID), `email`, `name`, `picture`, `exp`. The secret key is `JWT_SECRET_KEY` from environment.

**Rationale:** HTTP-only cookies are immune to XSS token theft. `SameSite=lax` provides baseline CSRF protection (cookie sent on top-level navigations but not on cross-origin POST). The frontend already uses `credentials: 'include'` so no code changes needed for cookie transmission.

**Alternatives considered:** JWT in localStorage + Authorization header — vulnerable to XSS; would require modifying every `apiFetch` call to attach the header. Session ID in cookie + server-side lookup — adds DB hit per request.

### 3. User table schema

**Decision:**

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    google_id TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ DEFAULT NOW()
);
```

No password column. `google_id` is the stable identifier from Google (`sub` claim). `email` is unique but can theoretically change on Google's side — `google_id` is the primary lookup key.

**Rationale:** Minimal table; only stores what we get from Google's ID token. No sensitive data beyond what Google already exposes. `last_login` is useful for analytics later.

**Alternatives considered:** Reuse the existing `sessions` table — wrong shape (session-oriented, not user-oriented); cleaner to add a proper `users` table.

### 4. User-scoping: `user_id` column on `cards` and `decks`

**Decision:** Add `user_id BIGINT REFERENCES users(id)` to `cards` and `decks`. Migration is three-phase: (1) add column as nullable, (2) backfill existing rows with the seed user's ID, (3) set NOT NULL. All repository methods (`get_all_cards`, `create`, `update`, `delete`, etc.) accept `user_id` and include it in queries. `card_images` and `deck_cards` are scoped transitively through their parent card/deck.

**Rationale:** Simplest isolation model — no row-level security, no tenant schemas. A WHERE clause on every query is explicit and easy to audit. The FK + index ensures referential integrity and query performance.

**Alternatives considered:** Postgres Row-Level Security — powerful but adds operational complexity (policies, roles); overkill for this scale. Separate schemas per user — high overhead, complicates migrations.

### 5. Auth middleware and dependency injection

**Decision:** A FastAPI dependency `get_current_user(request: Request) -> dict` reads the JWT from the cookie, validates signature and expiry, and returns the user payload (`{"id": ..., "email": ..., "name": ..., "picture": ...}`). Routes that need auth declare this dependency. A convenience `get_current_user_id` dependency extracts just the `id`. Public routes (`/api/health`, `/api/auth/*`) do not use the dependency.

**Rationale:** FastAPI's `Depends()` is the idiomatic pattern — no global middleware needed; each route explicitly opts in. This avoids accidentally breaking health checks or the auth callback itself.

**Alternatives considered:** Global middleware that rejects unauthenticated requests with a whitelist — works but less explicit; harder to reason about which routes are public.

### 6. Frontend auth: AuthContext + ProtectedRoute

**Decision:** `AuthContext` provides `{ user, isLoading, isAuthenticated, logout }`. On mount it calls `GET /api/auth/me` — if 200, user is set; if 401, user is null. `ProtectedRoute` wraps all app routes (except `/login`); if `!isAuthenticated && !isLoading`, it redirects to `/login`. The login page has a single button that navigates to `/api/auth/google` (full-page redirect, not AJAX). Logout calls `POST /api/auth/logout` (clears cookie) then sets user to null and redirects to `/login`.

**Rationale:** Minimal state management; no auth library needed. The "check session on mount" pattern works because the cookie is already being sent. No token handling in JS.

**Alternatives considered:** React Query for auth state — possible but auth is app-level state, not server-state; a context is simpler and avoids cache invalidation questions.

### 7. Seed user migration strategy

**Decision:** Migration `005_users_table.sql` creates the `users` table. Migration `006_add_user_id.sql` adds `user_id` (nullable) to `cards` and `decks`, inserts a seed user for `fj.pulidop@gmail.com` with `google_id = '__seed_pending__'`, backfills all existing rows, then sets the column to NOT NULL. On first real Google login with that email, the backend updates `google_id` from `'__seed_pending__'` to the real Google sub.

**Rationale:** Two-phase migration (nullable → backfill → NOT NULL) avoids downtime. The seed approach preserves existing data without requiring the owner to log in first. The `__seed_pending__` sentinel is replaced transparently on first login.

**Alternatives considered:** Require the owner to log in first, then run a manual SQL update — fragile and manual. Leave `user_id` nullable forever — loses the NOT NULL guarantee.

### 8. Environment variables

**Decision:** Three new variables:
- `GOOGLE_OAUTH_CLIENT_ID` — from Google Cloud Console
- `GOOGLE_OAUTH_CLIENT_SECRET` — from Google Cloud Console  
- `JWT_SECRET_KEY` — random string (≥32 chars); used to sign/verify JWTs

All required for the backend to start with auth enabled. Added to `.env.example` and `docker-compose.yml`.

**Rationale:** Standard OAuth + JWT configuration. Kept separate (not bundled into config.yaml) because they are secrets.

## Risks / Trade-offs

- **[Risk] JWT not revocable:** If a JWT is stolen (e.g., cookie exfiltrated via network attack), it remains valid until expiry (1h). **Mitigation:** Short TTL (1h); `secure` flag ensures HTTPS-only in production; `httpOnly` prevents JS access.
- **[Risk] Google OAuth consent screen:** For external users, Google may require app verification. **Mitigation:** Use minimal scopes (`openid`, `email`, `profile` — no sensitive scopes); for personal/small use, "Testing" mode allows up to 100 users without verification.
- **[Risk] Migration breaks existing workflows:** Adding NOT NULL `user_id` means all insert paths must provide a user. **Mitigation:** The migration is three-phase; backend code is updated before the NOT NULL constraint is applied.
- **[Trade-off] No refresh tokens:** Users must re-login after 1h of inactivity. **Mitigation:** Acceptable for a personal tool; can add refresh tokens later if needed.
- **[Trade-off] Single provider:** Users without a Google account cannot use the app. **Mitigation:** Google is near-universal for the target audience (MTG players using DeckDex); other providers can be added later following the same pattern.

## Migration Plan

1. **Add `users` table** — migration `005_users_table.sql`; no impact on existing code.
2. **Add `user_id` to `cards` and `decks`** — migration `006_add_user_id.sql`; nullable first, seed user created, backfill, then NOT NULL.
3. **Deploy backend auth** — new `routes/auth.py`, updated `dependencies.py`; existing routes gain `user_id` filtering. Requires `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `JWT_SECRET_KEY` in environment.
4. **Deploy frontend auth** — `AuthContext`, `Login` page, `ProtectedRoute`, navbar updates. Must deploy after backend auth is live.
5. **Rollback:** Drop `user_id` columns (revert migration 006), remove auth routes and middleware, remove frontend auth components. Data remains intact (cards/decks lose the `user_id` column but rows are preserved).

## Open Questions

- **Card images scoping:** `card_images` is keyed by `card_id` (FK to `cards`). Since cards are now user-scoped, images are transitively scoped. Should we add `user_id` to `card_images` too, or is the FK cascade sufficient? (Recommendation: FK cascade is sufficient — no change needed.)
- **WebSocket auth:** The progress WebSocket (`/ws/progress`) currently has no auth. Should it require the JWT cookie? (Recommendation: defer — WebSocket is used for job progress which is not user-scoped yet; can be addressed in a follow-up.)
