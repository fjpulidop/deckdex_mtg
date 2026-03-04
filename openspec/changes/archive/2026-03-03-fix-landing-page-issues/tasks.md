## 1. Hide JobsBottomBar on public pages

- [x] 1.1 In `frontend/src/App.tsx`, wrap `<JobsBottomBar />` with the existing `isLandingPage`/`isLoginPage` condition: `{!isLandingPage && !isLoginPage && <JobsBottomBar />}`

## 2. Add LanguageSwitcher to LandingNavbar

- [x] 2.1 Import `LanguageSwitcher` in `frontend/src/components/landing/LandingNavbar.tsx`
- [x] 2.2 Add `<LanguageSwitcher />` to the desktop right-side section (alongside Source Code button)
- [x] 2.3 Add `<LanguageSwitcher />` to the mobile menu section
