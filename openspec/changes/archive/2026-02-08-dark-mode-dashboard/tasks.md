# Tasks: Dark mode dashboard

## 1. Tailwind and theme infrastructure

- [x] 1.1 Enable Tailwind dark mode with class strategy (e.g. `darkMode: 'class'` or v4 equivalent in config)
- [x] 1.2 Add theme state: read from localStorage key `deckdex-theme` (values `dark` | `light`), default to `dark` when missing or invalid; apply class to `document.documentElement` on init and on change; expose `theme` and `setTheme` (e.g. React context or hook used at app root)

## 2. Persistence and nav control

- [x] 2.1 On theme change, persist value to localStorage immediately so next load uses it
- [x] 2.2 Add theme control (e.g. sun/moon toggle or selector) in the shared nav on Dashboard and Settings pages

## 3. Global and layout styling

- [x] 3.1 Update `frontend/src/index.css`: remove or make conditional the hardcoded light `body` background so theme drives it; ensure `html.dark` and light root both have appropriate background
- [x] 3.2 Add `dark:` variants to Dashboard and Settings layout (page container, nav bar, headings, links) so both themes look correct

## 4. Component styling

- [x] 4.1 Add `dark:` variants to StatsCards, Filters, ActionButtons, CardTable (cards, table, pagination, chips)
- [x] 4.2 Add `dark:` variants to CardFormModal, ActiveJobs bar and job cards, ErrorBoundary, PriceChart placeholder
- [x] 4.3 Add `dark:` variants to buttons, inputs, borders, and feedback (errors, toasts) used across components so they match the active theme

## 5. Verification

- [ ] 5.1 Manually verify: first visit shows dark; switching to light and reload restores light; switching to dark and reload restores dark
- [ ] 5.2 Manually verify: Dashboard and Settings and all modals/overlays respect the selected theme with no obvious light-only or dark-only patches
