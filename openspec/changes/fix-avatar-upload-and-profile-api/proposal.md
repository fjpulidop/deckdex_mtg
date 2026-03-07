## Why

The avatar crop feature is completely broken: `_validate_avatar_url()` in `backend/api/routes/auth.py` rejects `data:` URIs with a 400 error because it only allows HTTPS URLs — but the frontend sends a base64 data URI produced by `getCroppedImg()`. This means users cannot save a locally-cropped avatar at all. Additionally, `ProfileModal.tsx` bypasses the project's mandatory `api/client.ts` abstraction with a raw `fetch`, missing 401 auto-refresh and network error handling.

## What Changes

- **Backend**: Extend `_validate_avatar_url()` to accept `data:image/*;base64,...` URIs in addition to HTTPS URLs from the allowlist. Add avatar cache invalidation: when a user's avatar is updated via `PATCH /api/auth/profile`, delete the stale cached files for that user from `_AVATAR_CACHE_DIR` so the proxy endpoint re-serves the new image.
- **Backend**: Add `display_name` max-length validation (100 characters) to `ProfileUpdateRequest`.
- **Frontend**: Migrate `ProfileModal.tsx` to use `api.updateProfile()` from `api/client.ts` instead of raw `fetch`.
- **Frontend**: Add `updateProfile` method to the `api` object in `frontend/src/api/client.ts`.
- **Tests**: Add backend tests for data URI acceptance, data URI rejection (invalid format), cache invalidation on profile update, and display name length validation. Update existing `TestProfileUpdate` tests to cover the data URI happy path.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `user-auth`: `PATCH /api/auth/profile` now accepts `data:image/*;base64,...` URIs (in addition to HTTPS allowlist URLs) and invalidates the avatar disk cache on update. `display_name` is validated for max length (100 chars). These are spec-level behavior changes.
- `user-profile`: Frontend profile save path now routes through the typed API client. The spec requires all backend calls go through `api/client.ts` — currently violated. This aligns implementation to the existing requirement.

## Impact

- `backend/api/routes/auth.py`: `_validate_avatar_url()`, `update_profile()` route handler.
- `frontend/src/api/client.ts`: new `updateProfile` method + `ProfilePayload` / `ProfileUpdateBody` types.
- `frontend/src/components/ProfileModal.tsx`: `handleSave` rewired to `api.updateProfile()`.
- `tests/test_auth_e2e.py`: new test cases in `TestProfileUpdate` class.

## Non-goals

- Changing the avatar storage mechanism (stays in `users.avatar_url` column as a raw data URI or external HTTPS URL).
- Adding server-side image resizing or format conversion (client already produces 256×256 JPEG at 0.85 quality).
- Adding a focus trap to the crop sub-modal (accessibility debt tracked separately).
- Migrating `AuthContext.fetchMe()` raw fetch (scope limited to profile save path).
