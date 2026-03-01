## 1. Core — Repository engine injection

- [ ] 1.1 Modify `deckdex/storage/repository.py` `CollectionRepository.__init__` to accept optional `engine` parameter; if provided, set `self._eng = engine` directly
- [ ] 1.2 Modify `deckdex/storage/deck_repository.py` `DeckRepository.__init__` same pattern
- [ ] 1.3 Modify `deckdex/storage/job_repository.py` `JobRepository.__init__` same pattern
- [ ] 1.4 Modify `deckdex/storage/user_settings_repository.py` `UserSettingsRepository.__init__` same pattern
- [ ] 1.5 Modify `deckdex/catalog/repository.py` `CatalogRepository.__init__` same pattern
- [ ] 1.6 Verify: existing tests still pass with no engine provided (backward compatible)

## 2. Backend — Shared DB connection pool

- [ ] 2.1 Create `backend/api/db.py` with lazy singleton `get_engine()`: reads DATABASE_URL, creates engine with `pool_size=20, max_overflow=40, pool_pre_ping=True, pool_recycle=3600`; returns None if no DATABASE_URL
- [ ] 2.2 Update all `get_*_repo()` functions in `dependencies.py` to call `db.get_engine()` and pass result to repository constructors
- [ ] 2.3 Remove redundant `load_config()` + `create_engine()` patterns from each `get_*_repo()` function
- [ ] 2.4 Verify: backend starts and serves requests with shared pool

## 3. Backend — CORS configurable

- [ ] 3.1 In `main.py`, read `DECKDEX_CORS_ORIGINS` env var (comma-separated), default to `["http://localhost:5173"]`. Pass to `CORSMiddleware(allow_origins=...)`
- [ ] 3.2 Verify: dev still works without env var; setting env var changes allowed origins

## 4. Backend — Error sanitization

- [ ] 4.1 In `main.py` global exception handler: remove `"error": str(exc)` from response. Return only `{"detail": "Internal server error"}`
- [ ] 4.2 Audit `backend/api/routes/cards.py`: replace `f"Failed to fetch cards: {str(e)}"` with generic message; log full error
- [ ] 4.3 Audit `backend/api/routes/import_routes.py`: replace `f"Failed to parse file: {e}"` and similar with generic messages
- [ ] 4.4 Audit all other route files for `str(e)` or `str(exc)` in HTTPException detail; replace with generic messages
- [ ] 4.5 Verify: trigger an error and confirm response contains no internal details

## 5. Backend — JWT HTTP-only cookie + JTI

- [ ] 5.1 In `auth.py`: add `jti` (uuid4) claim to JWT payload when signing tokens
- [ ] 5.2 In `auth.py` callback endpoint: set JWT as HTTP-only cookie (`httpOnly=True, samesite='lax', path='/', max_age=3600, secure=True` when not dev). Remove redirect that returns token in URL/body
- [ ] 5.3 In `auth.py` exchange endpoint: set JWT as HTTP-only cookie in response. Return `{"ok": true}` without token in body
- [ ] 5.4 In `dependencies.py` `get_current_user`: read cookie first (primary), Bearer header second (fallback for API clients)
- [ ] 5.5 In `auth.py` logout endpoint: clear cookie (`max_age=0`)
- [ ] 5.6 Verify: auth flow works end-to-end with cookie-based auth

## 6. Backend — Token revocation

- [ ] 6.1 In `dependencies.py` (or new `token_blacklist.py`): create `_blacklist: Dict[str, datetime]` and functions `blacklist_token(jti, exp)`, `is_blacklisted(jti)`, `cleanup_expired()`
- [ ] 6.2 In `get_current_user`: after decoding JWT, check `is_blacklisted(payload['jti'])`; raise 401 if blacklisted
- [ ] 6.3 In `auth.py` logout endpoint: extract JTI from current token and call `blacklist_token(jti, exp)`
- [ ] 6.4 Add background cleanup: on each blacklist check, if last cleanup > 10 minutes ago, remove expired entries
- [ ] 6.5 Verify: after logout, old token is rejected

## 7. Backend — Auth code cleanup

- [ ] 7.1 In `auth.py`: in the function that generates new auth codes, add cleanup loop that removes entries from `_auth_codes` where `created_at + 300s < now`
- [ ] 7.2 Verify: stale codes are cleaned up on next code generation

## 8. Backend — Rate limiting

- [ ] 8.1 Add `slowapi` to `backend/requirements-api.txt`
- [ ] 8.2 In `main.py`: create `Limiter` instance with `key_func=get_remote_address` (default). Add `SlowAPIMiddleware`. Add `RateLimitExceeded` exception handler returning 429
- [ ] 8.3 Apply rate limit decorators to auth routes: `@limiter.limit("10/minute")` on `/api/auth/google`, `/api/auth/callback`, `/api/auth/exchange`
- [ ] 8.4 Apply rate limit decorators to read routes: `@limiter.limit("60/minute")` on cards GET, stats GET, analytics GET, insights GET
- [ ] 8.5 Apply rate limit decorators to write routes: `@limiter.limit("30/minute")` on cards POST/PUT/DELETE, decks POST/PATCH/DELETE, quantity PATCH, settings PUT
- [ ] 8.6 Apply rate limit decorators to trigger routes: `@limiter.limit("5/minute")` on process POST, price update POST, import POST
- [ ] 8.7 Verify: exceeding rate limit returns 429 with `Retry-After` header

## 9. Backend — File upload size limits

- [ ] 9.1 In `import_routes.py`: add size check before `await file.read()` — check `content-length` header, reject > 10MB with 413
- [ ] 9.2 Add streaming size guard: read in chunks, abort if accumulated > 10MB
- [ ] 9.3 Verify: uploading > 10MB file returns 413

## 10. Backend — WebSocket authentication

- [ ] 10.1 In `progress.py`: before `await websocket.accept()`, extract JWT from query param `token` or from cookies
- [ ] 10.2 Validate JWT (reuse `decode_jwt_token`); reject with close code 4001 if invalid/missing
- [ ] 10.3 Extract `user_id` from JWT payload; verify user owns the job (check against job metadata or skip ownership check if job_id is UUID and guessing is impractical — note in code)
- [ ] 10.4 Verify: unauthenticated WebSocket connection is rejected

## 11. Frontend — Cookie-based auth

- [ ] 11.1 In `client.ts`: remove `authHeaders()` function. Remove Bearer header injection from `apiFetch()`. Add `credentials: 'include'` to all fetch calls so cookies are sent automatically
- [ ] 11.2 In `AuthContext.tsx`: remove `sessionStorage.getItem/setItem('access_token')` references. `fetchMe()` calls `/api/auth/me` with `credentials: 'include'` (no manual header)
- [ ] 11.3 In `AuthContext.tsx` logout: remove `sessionStorage.removeItem('access_token')`. Just call `POST /api/auth/logout` (backend clears cookie) and reset state
- [ ] 11.4 Find and update any other frontend code that references `sessionStorage` or `access_token`
- [ ] 11.5 Update WebSocket connections to pass token via query param (or rely on cookie) — check how frontend creates WS connections
- [ ] 11.6 Verify: full auth flow works with cookies (login → dashboard → logout → login again)

## 12. Integration verification

- [ ] 12.1 Run `pytest tests/` and fix any failures
- [ ] 12.2 Manual smoke test: login, navigate, create/edit/delete card, trigger process, check WebSocket progress, logout, verify token rejected after logout
