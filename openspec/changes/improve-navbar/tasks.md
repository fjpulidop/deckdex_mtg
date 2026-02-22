## 1. Create Navbar Component

- [x] 1.1 Create `frontend/src/components/Navbar.tsx` file
- [x] 1.2 Implement basic component structure with desktop and mobile layouts
- [x] 1.3 Add useLocation hook for active route detection
- [x] 1.4 Add useState for mobile menu open/close state
- [x] 1.5 Create logo/title as clickable Link to Dashboard (`/`)
- [x] 1.6 Implement navigation links for all routes (Dashboard, Decks, Analytics, Settings)
- [x] 1.7 Add alpha/beta badges to Decks and Analytics links
- [x] 1.8 Integrate ThemeToggle component in desktop and mobile layouts
- [x] 1.9 Implement active link styling (indigo color, font-semibold, border-b-2)
- [x] 1.10 Implement inactive link styling with hover effects
- [x] 1.11 Add sticky positioning (`sticky top-0 z-50`)
- [x] 1.12 Style navbar with border-b and appropriate background colors for light/dark mode

## 2. Implement Mobile Navigation

- [x] 2.1 Add hamburger menu icon button (visible only on mobile: `md:hidden`)
- [x] 2.2 Create mobile menu overlay with full-screen stacked links
- [x] 2.3 Implement menu open/close toggle on hamburger button click
- [x] 2.4 Add auto-close behavior when a navigation link is clicked
- [x] 2.5 Add click-outside-to-close functionality for mobile menu
- [x] 2.6 Add ESC key listener to close mobile menu
- [x] 2.7 Add smooth transition animations for menu open/close
- [x] 2.8 Ensure mobile menu has appropriate z-index (`z-50`)

## 3. Integrate Navbar in App.tsx

- [x] 3.1 Import Navbar component in `frontend/src/App.tsx`
- [x] 3.2 Place `<Navbar />` above `<Routes>` inside `<ActiveJobsProvider>`
- [x] 3.3 Verify navbar appears on all routes

## 4. Remove Navigation from Individual Pages

- [x] 4.1 Remove navigation links and header from `frontend/src/pages/Dashboard.tsx`
- [x] 4.2 Remove navigation links and header from `frontend/src/pages/Settings.tsx`
- [x] 4.3 Remove navigation links and header from `frontend/src/pages/Analytics.tsx`
- [x] 4.4 Remove navigation links and header from `frontend/src/pages/DeckBuilder.tsx`
- [x] 4.5 Remove unused Link imports from all pages
- [x] 4.6 Remove ThemeToggle imports and usage from all pages (now in Navbar)
- [x] 4.7 Adjust page header layout/spacing now that navigation is removed

## 5. Testing and Refinement

- [x] 5.1 Test active state indicator on all routes (Dashboard, Decks, Analytics, Settings)
- [x] 5.2 Test logo click navigation from each page back to Dashboard
- [x] 5.3 Test sticky navbar behavior on pages with scrollable content
- [x] 5.4 Test mobile hamburger menu open/close functionality
- [x] 5.5 Test mobile menu auto-close on link click
- [x] 5.6 Test mobile menu close on outside click
- [x] 5.7 Test mobile menu close on ESC key
- [x] 5.8 Test dark mode styling for navbar (background, text, borders, hover states)
- [x] 5.9 Test hover effects on inactive links (should show visual feedback)
- [x] 5.10 Test that active link does not show hover effects
- [x] 5.11 Test alpha/beta badges display correctly on Decks and Analytics links
- [x] 5.12 Test responsive breakpoint at 768px (desktop vs mobile layout)
- [x] 5.13 Verify navbar does not conflict with existing modals (z-index)
