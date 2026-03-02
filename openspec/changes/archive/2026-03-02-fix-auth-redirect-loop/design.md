## Context

`apiFetch` in `frontend/src/api/client.ts` is the single wrapper for all API calls. On any 401 response (after a failed token refresh), it unconditionally redirects:

```typescript
window.location.href = '/login';
```

`ActiveJobsProvider` calls `api.getJobs()` on mount regardless of route — including `/login`. Since unauthenticated users get 401 on `/api/jobs`, the interceptor triggers a redirect to `/login`, reloading the page, re-mounting the provider, and repeating indefinitely.

## Goals / Non-Goals

**Goals:**
- Stop the infinite reload loop when a 401 occurs on the `/login` page
- Keep all other 401→redirect behavior intact for authenticated routes

**Non-Goals:**
- Redesigning the token refresh flow
- Preventing `ActiveJobsProvider` from mounting on public pages
- Any backend changes

## Decisions

### Decision: Guard the redirect in `apiFetch`, not in `ActiveJobsProvider`

The redirect logic lives in one place (`client.ts`). A guard there fixes the root cause for all current and future API calls that might be made on unauthenticated pages.

**Alternative considered — skip `getJobs()` when not authenticated:**
This would require `ActiveJobsProvider` to consume `AuthContext`, introducing a coupling between two independent providers and complicating the component tree. It also treats the symptom, not the cause.

**Chosen approach:**
```typescript
// Before redirecting, check we're not already on /login
if (window.location.pathname !== '/login') {
  window.location.href = '/login';
}
```

One line. No new dependencies. No structural changes.

## Risks / Trade-offs

- **Risk: Other public pages added in the future** → If new unauthenticated pages are added and they trigger API calls, they'd hit the same loop. **Mitigation:** The `/login` guard is minimal; if the app grows additional public pages they can be added to the exclusion list, or the logic can be refactored to check `isPublicPage()`.

- **Trade-off: Silently swallowing 401s on `/login`** → When the redirect is suppressed, the 401 response is still returned to the caller. `ActiveJobsProvider` already wraps the call in try/catch and logs errors, so the error is handled gracefully per the `global-jobs-ui` spec ("On API error: log, continue without blocking").
