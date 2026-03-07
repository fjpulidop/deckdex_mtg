# user-profile — Delta Spec

> Base spec: `openspec/specs/user-profile/spec.md`
> This file documents only the requirements that change or are added.

## Changed Requirement: User can save profile changes (API client usage)

**Clarifies the implementation requirement for scenario "Save calls PATCH /api/auth/profile" in `openspec/specs/user-profile/spec.md`.**

The `ProfileModal` SHALL invoke `PATCH /api/auth/profile` through the typed API client (`api.updateProfile()` in `frontend/src/api/client.ts`) and NOT through a raw `fetch` call.

This aligns `ProfileModal` with the project-wide convention that all backend calls go through `frontend/src/api/client.ts` (enforced in `frontend/CLAUDE.md` and `.claude/rules/frontend.md`).

### Scenario: Profile save uses API client (replaces raw fetch)
- **WHEN** the user clicks "Save" in the `ProfileModal`
- **THEN** the frontend SHALL call `api.updateProfile({ display_name?, avatar_url? })` from `frontend/src/api/client.ts`
- **THEN** the API client SHALL use `apiFetch` (which provides 401 auto-refresh and network error normalization)
- **THEN** if the call returns an error, the modal SHALL display the error `detail` message from the server response

### Scenario: Cropped avatar data URI is accepted by the server (end-to-end)
- **WHEN** the user applies a crop and clicks "Save"
- **THEN** the `data:image/jpeg;base64,...` produced by `getCroppedImg()` SHALL be accepted by the backend (HTTP 200)
- **THEN** `AuthContext.refreshUser()` SHALL be called
- **THEN** the navbar avatar SHALL update to reflect the new photo

## New Requirement: Display name max length enforced in frontend

**Added to `openspec/specs/user-profile/spec.md`.**

### Scenario: Display name exceeding max length is not submitted
- **WHEN** the user enters a display name longer than 100 characters in the `ProfileModal`
- **THEN** the frontend SHALL prevent submission and show a validation error message without calling the API

> Note: The backend also enforces 100-char max (HTTP 422). The frontend check is an optimistic guard for immediate user feedback.
