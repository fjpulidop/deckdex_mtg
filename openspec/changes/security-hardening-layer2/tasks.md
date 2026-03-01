# Tasks: Security Hardening Layer 2

All tasks completed.

- [x] Add security headers middleware to `backend/api/main.py`
- [x] Add request ID middleware with UUID generation to `backend/api/main.py`
- [x] Add global body size limit middleware (25 MB) to `backend/api/main.py`
- [x] Replace shallow health check with deep DB probe in `backend/api/main.py`
- [x] Add `Depends(get_current_user_id)` to 3 unprotected endpoints in `backend/api/routes/process.py`
- [x] Add `_validate_key()` path traversal protection to `deckdex/storage/image_store.py`
- [x] Add `POST /api/auth/refresh` endpoint in `backend/api/routes/auth.py`
- [x] Add 401 interceptor with silent refresh + login redirect in `frontend/src/api/client.ts`
- [x] Run all tests (179 backend + 20 frontend pass)
- [x] Commit and push
