## Context

DeckDex currently runs as a localhost-only app. The auth system uses Google OAuth → JWT, but tokens are returned in the response body and stored in sessionStorage (XSS-vulnerable). CORS is hardcoded to localhost:5173. Error handlers leak `str(exc)`. WebSocket connections have no auth. No rate limiting exists. Each repository creates its own SQLAlchemy engine. These gaps block internet exposure.

## Goals / Non-Goals

**Goals:**
- Close all critical security gaps for internet exposure
- Make the app handle thousands of concurrent users (DB pooling)
- Align JWT implementation with the existing user-auth spec (HTTP-only cookies)
- Add defense-in-depth: rate limiting, token revocation, file size limits

**Non-Goals:**
- Refresh tokens (Layer 2)
- Database-stored roles (keeping admin via env var)
- HTTPS/TLS (deployment-level)
- Frontend routing changes

## Decisions

### 1. CORS via environment variable

- **Choice:** Read `DECKDEX_CORS_ORIGINS` env var (comma-separated list). Default to `http://localhost:5173`. Pass parsed list to `CORSMiddleware.allow_origins`.
- **Rationale:** Simple, standard pattern. No config.yaml change needed — CORS is deployment-specific.
- **Alternative:** Add to config.yaml profiles — unnecessary complexity for a deployment concern.

### 2. Error sanitization strategy

- **Choice:** Remove `"error": str(exc)` from global exception handler. Return only `{"detail": "Internal server error"}` for 500s. Audit all route handlers: replace `f"Failed to X: {str(e)}"` with generic messages. Keep `logger.error(f"...: {exc}", exc_info=True)` for server-side logging.
- **Rationale:** Prevents leaking DB URLs, file paths, and stack traces to attackers.

### 3. WebSocket authentication via query parameter

- **Choice:** WebSocket clients pass JWT as query param: `ws://host/ws/progress/{job_id}?token=<jwt>`. Backend extracts, validates JWT, and checks `user_id` matches job owner. Reject with 4001 (unauthorized) or 4003 (forbidden).
- **Rationale:** WebSocket API doesn't support custom headers in the browser. Query param is the standard approach. Cookie-based auth is also possible since we're moving to HTTP-only cookies, but query param is explicit and works across all clients.
- **Alternative:** Read JWT from cookie on WS handshake — simpler for browser clients but fails for non-browser clients. We support both: try cookie first, then query param.

### 4. Rate limiting with slowapi

- **Choice:** Add `slowapi` (wraps `limits` library). Use in-memory storage (no Redis dependency). Configure limits per route group:
  - Auth endpoints: `10/minute` per IP (key: client IP)
  - Read endpoints (cards, stats, analytics, insights): `60/minute` per user (key: user_id from JWT)
  - Write endpoints (create, update, delete, quantity): `30/minute` per user
  - Trigger endpoints (process, price update, import): `5/minute` per user
  - File uploads: `5/minute` per user
- **Rationale:** `slowapi` is the de facto standard for FastAPI rate limiting. In-memory is sufficient for single-instance deployment. Redis backend can be added later for multi-instance.
- **Implementation:** Add `Limiter` instance in `main.py`. Apply decorators on route groups. Global exception handler for `RateLimitExceeded` returns 429.

### 5. JWT in HTTP-only cookie (spec alignment)

- **Choice:** Three changes:
  1. **Backend auth callback/exchange**: Set JWT as HTTP-only cookie (`httpOnly=True, samesite='lax', path='/', max_age=3600, secure=not_dev_mode`). Remove token from JSON response body on exchange endpoint.
  2. **Backend `get_current_user`**: Read token from cookie (primary) with Bearer header as fallback (for API/non-browser clients).
  3. **Frontend**: Remove all `sessionStorage.getItem/setItem('access_token')`. Remove `authHeaders()` Bearer injection. Ensure `fetch` calls use `credentials: 'include'` so cookies are sent automatically. Auth state comes purely from `GET /api/auth/me` response.
- **Rationale:** Aligns with the existing spec. HTTP-only cookies are immune to XSS token theft.
- **CSRF note:** `samesite='lax'` prevents CSRF for state-changing requests from cross-origin forms. For extra safety, all mutation endpoints already use POST/PATCH/DELETE (not GET), and CORS blocks cross-origin requests.

### 6. Token revocation (in-memory JTI blacklist)

- **Choice:** Add `jti` (JWT ID, UUID) claim to every JWT. On logout, add the JTI to an in-memory set with its expiry time. On token validation, check if JTI is blacklisted. Background cleanup removes expired entries every 10 minutes.
- **Rationale:** Simple, zero-dependency. Sufficient for single-instance. For multi-instance, swap to Redis later.
- **Trade-off:** Blacklist lost on restart — acceptable since tokens also expire in 1h and restart forces re-login anyway.

### 7. Auth code cleanup

- **Choice:** On each new auth code generation, iterate `_auth_codes` and remove entries where `created_at + 5min < now`. This is O(n) where n is number of pending codes — negligible.
- **Rationale:** Prevents unbounded memory growth under high login traffic.

### 8. File upload size limits

- **Choice:** Check `request.headers.get('content-length')` before reading. If > 10MB (10_485_760 bytes), return 413 immediately. Also add a streaming size check during `await file.read()` as defense-in-depth (content-length can be spoofed).
- **Rationale:** Prevents memory exhaustion from malicious uploads.
- **Where:** Import endpoints in `import_routes.py`. Avatar endpoint already has 500KB limit.

### 9. Shared DB connection pool

- **Choice:** Create `backend/api/db.py` module with a lazy singleton `get_engine()` function. Configures: `pool_size=20, max_overflow=40, pool_pre_ping=True, pool_recycle=3600`. All `get_*_repo()` functions in `dependencies.py` pass the shared engine to repository constructors. Repository classes accept optional `engine` parameter — if provided, use it instead of creating their own.
- **Rationale:** Current pattern creates 5+ separate pools (one per repo type). With default SQLAlchemy settings (pool_size=5, max_overflow=10), that's 75 max connections across all pools — uncontrolled. A shared pool of 60 max (20+40) is predictable and tunable.
- **Migration:** Repository `_get_engine()` methods gain `if self._eng is not None: return self._eng` early return (already exists). Constructor adds optional `engine` param that sets `self._eng` directly.

## Risks / Trade-offs

- **In-memory rate limiting**: Lost on restart, doesn't work across multiple instances. Acceptable for single-instance; Redis upgrade is straightforward later.
- **In-memory token blacklist**: Same limitation as above. Acceptable since token lifetime is only 1 hour.
- **Cookie + CORS interaction**: Must ensure CORS `allow_credentials=True` and exact origin matching (no wildcards). Already the case.
- **Breaking change for API clients**: Moving from Bearer to cookie changes how non-browser clients authenticate. Mitigated by keeping Bearer header as fallback in `get_current_user`.

## Migration Plan

- No database migrations required. All changes are application-level.
- Deploy: update backend first (supports both cookie and Bearer), then update frontend (removes Bearer).
- Rollback: revert frontend to Bearer, revert backend cookie logic. Independent of each other due to fallback.
