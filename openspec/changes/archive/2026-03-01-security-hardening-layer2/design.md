# Design: Security Hardening Layer 2

## Middleware Stack (backend/api/main.py)

Three new middlewares execute in this order (outermost first):

1. **Body size limit** — checks `Content-Length` header, returns 413 if > 25 MB
2. **Request ID + logging** — generates UUID (or uses incoming `X-Request-ID`), attaches to `request.state`, sets `X-Request-ID` response header, logs request/response
3. **Security headers** — sets defensive headers on every response:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
   - `Strict-Transport-Security` (production only)

## Deep Health Check (GET /api/health)

Returns JSON with `status`, `database` fields. Probes DB via `SELECT 1`.
Returns 503 with `status: "degraded"` if DB probe fails.

## Unprotected Endpoints Fix (backend/api/routes/process.py)

Added `Depends(get_current_user_id)` to:
- `POST /prices/update/{card_id}` — single-card price update
- `GET /jobs/{job_id}` — job status polling
- `POST /jobs/{job_id}/cancel` — job cancellation

## Path Traversal Protection (deckdex/storage/image_store.py)

`_validate_key()` static method rejects keys containing `..`, starting with `/`, or containing null bytes. Called at the top of `get()`, `put()`, `exists()`, `delete()`.

## Silent Token Refresh (POST /api/auth/refresh)

- Reads JWT from cookie (primary) or Bearer header (fallback)
- Validates current token via `decode_jwt_token()`
- Blacklists old token's JTI
- Issues new JWT with same user info, sets as HTTP-only cookie
- Returns `{"ok": true}`

## Frontend 401 Interceptor (frontend/src/api/client.ts)

- On 401 from any API call (except `/auth/refresh` and `/auth/me`), attempts silent refresh
- Deduplicates concurrent refreshes via shared promise (`_refreshPromise`)
- If refresh succeeds, retries original request
- If refresh fails, redirects to `/login`
