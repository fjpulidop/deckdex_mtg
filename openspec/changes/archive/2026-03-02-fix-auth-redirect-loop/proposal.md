## Why

When a user visits `/login`, `ActiveJobsProvider` mounts and calls `api.getJobs()` on every page load. Since the user isn't authenticated, the backend returns 401, which triggers the `apiFetch` interceptor to attempt a token refresh — and when that also fails, it executes `window.location.href = '/login'`, causing an infinite page-reload loop (visible as constant flickering).

## What Changes

- Add a guard in `apiFetch` so it does NOT redirect to `/login` if the browser is already on `/login`
- Matches the existing `global-jobs-ui` spec requirement: "On API error: log, continue without blocking"

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
<!-- The fix is a pure implementation correction; no spec-level requirement changes -->

## Impact

- **frontend/src/api/client.ts** — one-line guard before `window.location.href = '/login'`
- No backend changes
- No API contract changes
- No new dependencies

## Non-goals

- Redesigning the token-refresh strategy
- Protecting additional routes from the redirect loop
- Changes to `ActiveJobsProvider` mount behavior
