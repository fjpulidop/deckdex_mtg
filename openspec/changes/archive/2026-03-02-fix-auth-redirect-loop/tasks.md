## 1. Fix API client redirect guard

- [x] 1.1 In `frontend/src/api/client.ts`, add a `window.location.pathname !== '/login'` guard before the `window.location.href = '/login'` redirect (line ~57)
- [x] 1.2 Extend the guard to also exclude `/` (Landing page) — unauthenticated users on the landing page were being redirected to `/login` by `ActiveJobsProvider`'s `getJobs()` call

## 2. Verify

- [x] 2.1 Open `http://localhost:5173/login` in a browser — confirm no flickering/reload loop
- [x] 2.2 Open `http://localhost:5173/` — confirm landing page loads without redirect
- [x] 2.3 Confirm that navigating to a protected route while unauthenticated still redirects to `/login` correctly
