# User Profile & Avatar Crop Exploration (2026-03-07)

## Specs Reviewed
- `openspec/specs/user-auth/spec.md` -- Google OAuth, JWT, profile PATCH, avatar proxy
- `openspec/specs/user-profile/spec.md` -- ProfileModal, avatar crop, display name editing
- `openspec/specs/admin-backoffice/spec.md` -- is_admin column, admin routes, bootstrap admin
- `openspec/specs/external-apis-settings/spec.md` -- user_settings table, Scryfall toggle

## Architecture Overview

### Database
- `users` table (migration 005): id, google_id, email, display_name, avatar_url, created_at, last_login
- `is_admin` column (migration 013): BOOLEAN NOT NULL DEFAULT FALSE
- `user_settings` table (migration 012): user_id FK, settings JSONB, created_at, updated_at

### Backend (auth.py -- 623 lines, dependencies.py -- 509 lines)
- Google OAuth flow: GET /google -> callback -> one-time auth code -> exchange
- JWT cookie auth with JTI blacklist (in-memory)
- PATCH /profile: display_name + avatar_url update
- GET /avatar/{user_id}: proxy with disk cache, supports data URIs + external URLs
- GET /me: reads from DB (not JWT), includes is_admin
- POST /refresh: silent token refresh, blacklists old JTI
- POST /logout: blacklist + clear cookie
- Admin dependency: require_admin (checks is_admin column + DECKDEX_ADMIN_EMAIL env var)

### Frontend
- AuthContext.tsx: fetchMe(), refreshUser(), logout(), avatar proxy URL rewriting
- ProfileModal.tsx: display name editing + avatar upload with react-easy-crop
- Navbar.tsx: user dropdown with Profile/Settings/Logout, mobile menu
- AuthCallback.tsx: one-time code exchange page
- Login.tsx: Google OAuth login page
- utils/auth.ts: getBackendOrigin(), redirectToGoogleLogin()

### Tests
- test_auth_e2e.py: 40+ tests covering JWT, blacklist, exchange, refresh, logout, /me, profile update, OAuth callback

## CRITICAL BUGS

### BUG 1: Avatar upload is completely broken (PATCH /profile rejects data URIs)
- **Severity**: CRITICAL -- the entire avatar crop feature is non-functional
- **Location**: `backend/api/routes/auth.py` line 417-418
- `_validate_avatar_url()` requires HTTPS scheme from domain allowlist
- ProfileModal.tsx sends `data:image/jpeg;base64,...` (line 115-117)
- The `data:` scheme != `https:`, so the backend returns 400 every time
- The avatar proxy endpoint (GET /avatar/{user_id}) DOES handle data URIs (line 563-588)
- The spec explicitly says data URIs should work (user-auth spec line 75-77)
- **Fix**: Add `data:` URI bypass in `_validate_avatar_url()` -- if URL starts with `data:image/`, skip domain validation, just validate size

### BUG 2: ProfileModal uses raw fetch instead of API client
- **Severity**: MODERATE -- violates frontend convention
- **Location**: `frontend/src/components/ProfileModal.tsx` line 118-123
- Convention says ALL backend calls through `api/client.ts` + `useApi` hook
- `api/client.ts` has ZERO profile-related methods
- ProfileModal does raw `fetch('/api/auth/profile', ...)` directly
- Missing: no 401 interceptor/refresh logic on this call

## GAPS: Spec vs. Implementation

### Fully Implemented
1. Google OAuth flow (login, callback, exchange, redirect)
2. JWT cookie auth with JTI blacklist
3. GET /me reads from DB (not JWT), includes is_admin
4. PATCH /profile endpoint (display_name + avatar_url)
5. POST /refresh with JTI rotation
6. POST /logout with blacklist + cookie clear
7. Avatar proxy with disk caching
8. ProfileModal with react-easy-crop for avatar
9. Display name editing with validation
10. Navbar user dropdown (Profile, Settings, Logout)
11. AuthContext with refreshUser()
12. Admin bootstrap via DECKDEX_ADMIN_EMAIL
13. 401 handling in AuthContext (redirects to /login)
14. Mobile menu with user actions

### Missing / Broken
1. **Avatar upload broken** (BUG 1 above -- data URI validation)
2. **No API client methods for profile** (BUG 2 above)
3. **No 401 interceptor with silent refresh on profile save** -- spec requires concurrent 401 dedup
4. **No avatar cache invalidation** -- after profile update, old avatar stays cached on disk
5. **No display name length validation** -- backend accepts any length
6. **No email display in ProfileModal** -- spec doesn't require it, but it would be useful context
7. **Crop sub-modal lacks focus trap** -- ESC works, but Tab can escape to parent modal
8. **No avatar "remove" option** -- user can only change, not remove their avatar
9. **No optimistic UI update** -- avatar/name change only shows after refreshUser() completes

## IMPROVEMENT IDEAS

### Tier 1: Critical Fixes (must-do)

| ID | Idea | Value | Effort | Impact/Effort |
|----|------|-------|--------|---------------|
| P1 | Fix _validate_avatar_url to accept data: URIs | Critical | Small (30min) | Very High |
| P2 | Add updateProfile() to api/client.ts | High | Small (30min) | High |
| P3 | Update ProfileModal to use API client | High | Small (30min) | High |

### Tier 2: Quality Improvements (should-do)

| ID | Idea | Value | Effort | Impact/Effort |
|----|------|-------|--------|---------------|
| P4 | Avatar cache invalidation on profile update | Medium | Small (1hr) | Medium |
| P5 | Display name max length validation (backend + frontend) | Medium | Small (30min) | Medium |
| P6 | Focus trap in crop sub-modal | Medium | Small (30min) | Medium |
| P7 | Add role="alert" to save error in ProfileModal | Low | Tiny (10min) | High |
| P8 | 401 interceptor with silent refresh (shared with all API calls) | High | Medium (3hrs) | Medium |

### Tier 3: Enhancements (nice-to-have)

| ID | Idea | Value | Effort | Impact/Effort |
|----|------|-------|--------|---------------|
| P9 | "Remove avatar" option (reset to Google photo or placeholder) | Low | Small (1hr) | Low |
| P10 | Optimistic UI update (show new avatar/name immediately) | Medium | Medium (2hrs) | Medium |
| P11 | Show email (read-only) in ProfileModal for context | Low | Tiny (15min) | Medium |
| P12 | Avatar file size validation client-side (before upload) | Low | Small (30min) | Low |
| P13 | Compress avatar to WebP instead of JPEG (smaller payload) | Low | Small (1hr) | Low |

### Tier 4: Future Ideas (explore later)

| ID | Idea | Value | Effort | Impact/Effort |
|----|------|-------|--------|---------------|
| P14 | Profile completion indicator ("add a photo", "set display name") | Low | Medium (2hrs) | Low |
| P15 | Avatar history (keep last N avatars for easy switch-back) | Very Low | Medium (3hrs) | Very Low |
| P16 | Animated avatar border for premium/admin users | Very Low | Small (1hr) | Very Low |

## Recommended Priority Order
1. **P1** -- Fix avatar data URI validation (critical bug, blocks main feature)
2. **P2 + P3** -- API client methods + update ProfileModal (convention violation)
3. **P4** -- Avatar cache invalidation (stale avatars after update)
4. **P6** -- Focus trap in crop sub-modal (a11y)
5. **P5** -- Display name length validation (defense in depth)
6. **P8** -- 401 interceptor (affects all API calls, not just profile)

## Key Files
- Backend auth routes: `/Users/javi/repos/deckdex_mtg/backend/api/routes/auth.py`
- Backend dependencies: `/Users/javi/repos/deckdex_mtg/backend/api/dependencies.py`
- Frontend ProfileModal: `/Users/javi/repos/deckdex_mtg/frontend/src/components/ProfileModal.tsx`
- Frontend AuthContext: `/Users/javi/repos/deckdex_mtg/frontend/src/contexts/AuthContext.tsx`
- Frontend Navbar: `/Users/javi/repos/deckdex_mtg/frontend/src/components/Navbar.tsx`
- Frontend API client: `/Users/javi/repos/deckdex_mtg/frontend/src/api/client.ts`
- User migration: `/Users/javi/repos/deckdex_mtg/migrations/005_users_table.sql`
- Auth tests: `/Users/javi/repos/deckdex_mtg/tests/test_auth_e2e.py`
- User-auth spec: `/Users/javi/repos/deckdex_mtg/openspec/specs/user-auth/spec.md`
- User-profile spec: `/Users/javi/repos/deckdex_mtg/openspec/specs/user-profile/spec.md`
