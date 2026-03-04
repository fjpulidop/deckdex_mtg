## Context

The landing page (`/`) and login page (`/login`) are public routes that don't require authentication. Two components have incorrect visibility on these pages:

1. `JobsBottomBar` renders globally in `App.tsx` (line 91) with no route filtering — it appears on every page including landing and login.
2. `LanguageSwitcher` was added to the authenticated `Navbar` but not to `LandingNavbar`, so pre-login users cannot switch language.

## Goals / Non-Goals

**Goals:**
- Hide `JobsBottomBar` on public pages (landing, login)
- Add `LanguageSwitcher` to `LandingNavbar` (desktop and mobile)

**Non-Goals:**
- Changing JobsBottomBar behavior (auto-hide when empty, styling, etc.)
- Modifying the LanguageSwitcher component itself
- Adding language switching to the login page

## Decisions

### 1. Conditional rendering of JobsBottomBar via route check

Use the existing `isLandingPage` and `isLoginPage` variables already in `AppContent()` to conditionally render `<JobsBottomBar />`.

```tsx
{!isLandingPage && !isLoginPage && <JobsBottomBar />}
```

**Why this over a ProtectedRoute wrapper**: The bar doesn't need auth context — it just shouldn't appear on public pages. A simple route check is the minimal change. This follows the same pattern already used for the Navbar (line 30).

### 2. LanguageSwitcher placement in LandingNavbar

Add `<LanguageSwitcher />` to the right side of the desktop nav (between the center links and Source Code button) and inside the mobile menu. This mirrors the authenticated Navbar's layout.

**Layer**: Frontend only. No backend or core changes.

## Risks / Trade-offs

- [Minimal risk] If new public routes are added in the future, `JobsBottomBar` would appear on them unless the condition is updated. Acceptable since new routes are rare and the pattern is clear.
