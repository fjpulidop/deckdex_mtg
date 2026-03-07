# user-auth — Delta Spec

> Base spec: `openspec/specs/user-auth/spec.md`
> This file documents only the requirements that change or are added.

## Changed Requirement: Profile update avatar URL validation

**Replaces scenario "Invalid avatar URL rejected" in `openspec/specs/user-auth/spec.md`.**

The `PATCH /api/auth/profile` endpoint SHALL accept two classes of `avatar_url` value:

1. An HTTPS URL whose hostname is in the allowlist (`googleusercontent.com`, `gravatar.com`, `avatars.githubusercontent.com`).
2. A data URI matching the pattern `data:image/(jpeg|png|gif|webp);base64,<base64-data>`.

All other values SHALL be rejected with HTTP 400.

### Scenario: Data URI avatar accepted
- **WHEN** an authenticated client calls `PATCH /api/auth/profile` with `{ "avatar_url": "data:image/jpeg;base64,<valid-base64>" }`
- **THEN** the backend SHALL accept the value, persist it in `users.avatar_url`, and return HTTP 200 with the updated user payload

### Scenario: Malformed data URI rejected
- **WHEN** an authenticated client calls `PATCH /api/auth/profile` with a `avatar_url` starting with `data:` but not matching the expected pattern (e.g., wrong MIME type, missing base64 marker, empty data)
- **THEN** the backend SHALL return HTTP 400 Bad Request

### Scenario: Non-HTTPS, non-data URI rejected (unchanged)
- **WHEN** `avatar_url` is `http://` or a scheme other than `https` or `data:`
- **THEN** the backend SHALL return HTTP 400

### Scenario: Disallowed HTTPS domain rejected (unchanged)
- **WHEN** `avatar_url` is HTTPS but the domain is not in the allowlist
- **THEN** the backend SHALL return HTTP 400

## New Requirement: Avatar cache invalidation on profile update

**Added to `openspec/specs/user-auth/spec.md`.**

When a user's `avatar_url` is updated via `PATCH /api/auth/profile`, the backend SHALL invalidate any locally cached avatar files for that user.

### Scenario: Cache cleared after avatar update
- **WHEN** `PATCH /api/auth/profile` successfully updates `avatar_url`
- **THEN** the backend SHALL delete all cached avatar files for that `user_id` from `_AVATAR_CACHE_DIR` (files matching `{user_id}_*.img` and `{user_id}_*.ct`)
- **THEN** the next call to `GET /api/auth/avatar/{user_id}` SHALL re-fetch/decode from the updated `avatar_url` stored in the database

### Scenario: Cache invalidation failure is non-fatal
- **WHEN** deletion of a cached avatar file fails (e.g., OS error)
- **THEN** the profile update SHALL still return HTTP 200 (deletion failure SHALL NOT cause the request to fail)

## Changed Requirement: Display name max length validation

**Extends existing "PATCH /api/auth/profile — update display name" requirement.**

### Scenario: Display name exceeding max length rejected
- **WHEN** an authenticated client calls `PATCH /api/auth/profile` with a `display_name` longer than 100 characters
- **THEN** the backend SHALL return HTTP 422 Unprocessable Entity

### Scenario: Display name at max length accepted
- **WHEN** an authenticated client calls `PATCH /api/auth/profile` with a `display_name` of exactly 100 characters
- **THEN** the backend SHALL accept it and return HTTP 200
