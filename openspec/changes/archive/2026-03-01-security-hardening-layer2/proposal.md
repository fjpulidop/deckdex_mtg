# Proposal: Security Hardening Layer 2

## Why

Layer 1 closed the critical auth/CORS/rate-limiting gaps. Layer 2 addresses defense-in-depth: security headers, unprotected endpoints, path traversal, request tracing, session continuity (refresh tokens), deep health checks, and frontend error handling. These are the remaining gaps identified by a full security audit before internet exposure.

## What Changes

- **Security headers middleware**: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS (when not dev)
- **Fix 3 unprotected endpoints**: `/prices/update/{card_id}`, `/jobs/{job_id}` GET, `/jobs/{job_id}/cancel` — add auth
- **Path traversal protection**: Validate image store keys cannot escape base directory
- **Request ID middleware**: Generate UUID per request, include in logs and `X-Request-ID` response header
- **Silent token refresh**: New `/api/auth/refresh` endpoint; frontend auto-refreshes before expiry
- **Deep health check**: `/api/health` verifies DB connectivity
- **Frontend 401 interceptor**: Auto-redirect to login on 401 responses
- **Global request body limit**: Middleware rejects bodies > 25MB

## Non-goals

- Database-level roles/permissions
- Full CSP with nonce-based scripts (deployment-specific)
- Structured JSON logging (separate change)
- SQL pattern refactoring (f-string → SQLAlchemy builder)
