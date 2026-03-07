# Auth E2E Tests

## Goal

Add comprehensive end-to-end tests for the authentication flow in `tests/test_auth_e2e.py`.

## Scenarios

- JWT creation and validation (valid, expired, malformed)
- OAuth callback (mock Google, new user creation, existing user login)
- Auth code exchange (valid, expired, reused)
- Token refresh (new token issued, old JTI blacklisted)
- Logout (JTI blacklisted, cookie cleared)
- Get current user (/api/auth/me)
- Token blacklist enforcement
- Error cases (missing credentials, invalid tokens)
- Profile update (valid, invalid avatar URL, unauthenticated)

## Implementation

File: `tests/test_auth_e2e.py`

Pattern: `unittest.TestCase` classes with `setUp`/`tearDown`.
Cleanup `_auth_codes` and `_token_blacklist` in `tearDown`.
Mock `httpx.AsyncClient` for Google OAuth calls.
