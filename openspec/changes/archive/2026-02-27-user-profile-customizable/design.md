## Context

User identity data currently flows: Google OAuth → JWT cookie → `/api/auth/me` returns JWT payload. This means once the JWT is issued, user data is frozen for its 1-hour lifetime — even if the DB is updated. The `users` table (`id`, `google_id`, `email`, `display_name`, `avatar_url`, `created_at`, `last_login`) already has all needed columns. The seed user has `display_name = 'Seed User'` baked in from DB initialization.

On the frontend, Settings lives at `/settings` as a top-level route and navbar link. The user dropdown only has Logout.

## Goals / Non-Goals

**Goals:**
- Profile data is always fresh: `/me` reads from DB, not JWT
- Users can change `display_name` and upload a profile photo with circular crop
- Settings and Profile are accessed from the user dropdown as modals (no route navigation)
- Avatar stored as base64 data URI — zero extra infrastructure

**Non-Goals:**
- Multi-user or role management
- Password authentication (Google OAuth only)
- Image hosting / CDN / external storage
- Cover photos, bios, or any other profile fields beyond name and avatar

## Decisions

### D1: `/me` reads from DB on every call

**Decision**: `GET /api/auth/me` does `SELECT * FROM users WHERE id = :id` using the `sub` from the JWT, instead of returning the JWT payload directly.

**Rationale**: After profile update the frontend needs to see new data immediately. Refreshing the JWT on every profile update is more complex and still has a brief stale window. DB reads on `/me` are cheap (primary key lookup, single row) and the endpoint is only called on page load.

**Alternative considered**: Issue a new JWT after profile update and set a new cookie. Rejected: adds complexity and still leaves a window where old cached data is shown.

### D2: Avatar as base64 data URI in `users.avatar_url`

**Decision**: Client resizes image to max 256×256 via Canvas, converts to JPEG at quality 0.85, encodes as base64 data URI string, sends in `PATCH /profile` body. Stored as-is in `avatar_url TEXT`.

**Rationale**: App is localhost-only — no S3, no static file server needed. A 256×256 JPEG at q=0.85 is ~15–25KB; base64 overhead is ~33%, so ~20–35KB in the DB. Negligible. The data URI works directly in `<img src>` tags with zero extra serving logic.

**Alternative considered**: Store files under `backend/static/avatars/` and serve via FastAPI `StaticFiles`. Rejected: adds a directory to manage and a separate URL to construct; base64 is simpler for a localhost app.

### D3: Interactive crop with `react-easy-crop`

**Decision**: Use the `react-easy-crop` npm package (v5, ~15KB gzipped) for the crop UI.

**Rationale**: Implementing drag+zoom+circular-crop from scratch with Canvas and mouse events is fragile and ~300+ lines of code. `react-easy-crop` is the de facto standard for this pattern (used by Slack, Notion, etc.), has circular crop support built in, and integrates cleanly with our React + TypeScript setup.

**Integration**: After crop confirmation, use `getCroppedImg` helper (Canvas-based, ~30 lines) to produce the final `HTMLCanvasElement`, then `canvas.toDataURL('image/jpeg', 0.85)` for the base64 string.

### D4: Settings becomes a modal, `/settings` route redirects

**Decision**: Extract `Settings.tsx` content into `SettingsModal.tsx`. The `/settings` route renders a redirect to `/dashboard`. Settings is opened only from the user dropdown.

**Rationale**: Settings is not a destination users navigate to directly — it's contextual to the user session. Modal pattern avoids full page navigation and matches the proposed Profile modal, keeping the UX consistent.

### D5: `AuthContext` gains `refreshUser()`

**Decision**: Add `refreshUser(): Promise<void>` to `AuthContext` that re-calls `GET /api/auth/me` and updates the `user` state. `ProfileModal` calls this after a successful `PATCH /profile`.

**Rationale**: After saving profile changes, the navbar should instantly reflect the new name/avatar without requiring a page reload. Since `/me` now reads from DB, `refreshUser()` is always correct.

## Risks / Trade-offs

- **Large avatars inflate DB row size** → Mitigated by client-side resize to 256×256 before upload; enforce max payload size on `PATCH /profile` (e.g., 200KB)
- **`react-easy-crop` adds a dependency** → Small, stable, MIT-licensed; acceptable for the UX gain
- **`/me` DB read on every page load** → Negligible cost; single primary key lookup; acceptable trade-off for always-fresh data
- **Existing JWTs still have stale `display_name`/`picture`** → Doesn't matter — those fields are only used for the initial auth check; after D1, `/me` ignores JWT payload fields other than `sub`

## Migration Plan

1. Deploy backend changes (D1 + new `PATCH /profile` + repository method) — backward compatible, existing sessions still work
2. Deploy frontend changes — modal replaces page, old `/settings` bookmark redirects to dashboard
3. No DB migration required

## Open Questions

- None — all decisions made during exploration.
