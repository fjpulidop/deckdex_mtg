# Proposal: Security Hardening Layer 1

## Why

DeckDex is transitioning from a localhost-only app to an internet-exposed service supporting thousands of concurrent users. The current codebase has critical security gaps: CORS is hardcoded to localhost, error responses leak internal details, WebSocket endpoints have no authentication, there is zero rate limiting, JWT tokens are stored in XSS-vulnerable sessionStorage, and the database creates a new connection pool per repository type per request. These gaps must be closed before any public exposure.

## What Changes

- **CORS**: Make allowed origins configurable via `DECKDEX_CORS_ORIGINS` env var (comma-separated), defaulting to `http://localhost:5173` for dev.
- **Error sanitization**: Remove `str(exc)` from all client-facing error responses. Log full errors server-side only.
- **WebSocket auth**: Validate JWT on WebSocket connect (via query param `token`). Verify the connecting user owns the job.
- **Rate limiting**: Add `slowapi` middleware with per-endpoint limits (auth: 10/min/IP, reads: 60/min/user, writes: 30/min/user, triggers: 5/min/user).
- **JWT in HTTP-only cookie**: Align implementation with existing spec — backend sets HTTP-only cookie, frontend stops using sessionStorage/Bearer header.
- **Token revocation**: In-memory JTI blacklist checked on every request; populated on logout. TTL-based cleanup.
- **Auth code cleanup**: Purge expired one-time auth codes on each new code generation.
- **File upload limits**: Enforce 10MB max on import endpoints. Return 413 if exceeded.
- **Shared DB pool**: Single SQLAlchemy engine with `pool_size=20, max_overflow=40, pool_recycle=3600`. All repositories share it.

## Capabilities

### Modified Capabilities

- **user-auth**: JWT delivery moves from response body → HTTP-only cookie. Token revocation on logout. Auth code memory leak fixed.
- **web-api-backend**: CORS configurable, error sanitization, rate limiting middleware, file upload limits, shared DB connection pool.
- **web-dashboard-ui**: Frontend removes sessionStorage token handling and Bearer header injection; relies on cookie-based auth.

## Non-goals

- Adding refresh tokens (Layer 2)
- Changing the user model or adding roles to DB
- HTTPS/TLS configuration (deployment concern, not application)
- Changing frontend routing or page structure
- Structured JSON logging (Layer 3)

## Impact

- **Backend**: `main.py`, `dependencies.py`, `auth.py`, `progress.py`, all route files (error sanitization), all repository classes (shared engine), `requirements-api.txt`.
- **Frontend**: `client.ts`, `AuthContext.tsx` — remove sessionStorage/Bearer, rely on cookies.
- **Core**: Repository classes gain optional `engine` parameter; no logic changes.
- **Dependencies**: Add `slowapi` to backend requirements.
