## Context

The DeckDex MTG frontend is a React 19 + TypeScript + Vite application using Tailwind CSS for styling and react-router-dom for routing. Currently, each page (Dashboard, Settings, Analytics, DeckBuilder) implements its own navigation with inconsistent layouts and styling. The navigation consists of simple `<Link>` components with basic hover effects, no active state indication, and duplicated code across all pages.

The application already has:
- ThemeToggle component for dark mode
- Established Tailwind design system (indigo for primary actions, gray scale for neutrals)
- Four main routes: `/` (Dashboard), `/settings`, `/analytics`, `/decks`
- Beta/alpha badges on some navigation items

## Goals / Non-Goals

**Goals:**
- Create a reusable Navbar component that works across all pages
- Provide clear visual feedback for the current active route
- Maintain consistent navigation UX between desktop and mobile
- Improve perceived professionalism with polished hover/active states
- Reduce code duplication by centralizing navigation logic
- Preserve existing theme integration (dark mode)

**Non-Goals:**
- Change the routing structure or add new routes
- Redesign the overall application layout or color scheme
- Add authentication-based navigation (future feature)
- Implement breadcrumbs or nested navigation
- Create a sidebar alternative (sticking with top navbar)

## Decisions

### 1. Component Placement: App.tsx vs. Layout Component

**Decision:** Place `<Navbar />` directly in `App.tsx` outside the `<Routes>` component.

**Rationale:** This is the simplest approach that ensures the navbar appears on all pages without creating an unnecessary layout abstraction. Since we only have one layout type (all pages have the same navbar), introducing a layout component would add complexity without benefit.

**Alternative Considered:** Create a `Layout` component that wraps routes. This is better for apps with multiple layout types (e.g., public vs. authenticated layouts), but overkill for our current needs.

### 2. Active Route Detection: useLocation vs. NavLink

**Decision:** Use `useLocation()` hook to manually detect the active route and apply styles conditionally.

**Rationale:** React Router's `NavLink` component supports active styling, but we want custom behavior (styled underline, font weight changes) that's easier to control with explicit state checking. This also gives us flexibility for future enhancements (e.g., highlighting parent routes for nested navigation).

**Implementation:**
```tsx
const location = useLocation();
const isActive = (path: string) => location.pathname === path;
```

### 3. Mobile Navigation: Hamburger Menu vs. Always Visible

**Decision:** Implement a hamburger menu that shows a full-screen overlay on mobile (<768px breakpoint).

**Rationale:** Mobile screens don't have space for a horizontal navbar with 4+ items plus logo and theme toggle. A hamburger menu is the industry standard for responsive navigation and keeps the mobile experience clean.

**Behavior:**
- Hamburger icon (☰) in top-right on mobile
- Clicking opens a full-screen overlay with stacked navigation links
- Clicking a link closes the menu and navigates
- Clicking outside or pressing ESC also closes the menu

### 4. Sticky Positioning: Always Sticky vs. Scroll Behavior

**Decision:** Use `position: sticky` with `top: 0` so the navbar stays visible during scroll.

**Rationale:** Users expect navigation to be always accessible, especially on pages with scrollable content (Dashboard card list, Analytics charts). Sticky positioning is well-supported in modern browsers and provides the best UX.

**CSS:**
```tsx
className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b ..."
```

### 5. Active State Styling: Underline vs. Background Highlight

**Decision:** Use a colored bottom border (2px underline effect) plus font-weight and color change for the active link.

**Rationale:** This matches modern web app conventions (e.g., GitHub, Linear, Notion) and is visually distinct without being overwhelming. Background highlights can make the navbar feel cluttered.

**Styles:**
- Active: `text-indigo-600 dark:text-indigo-400 font-semibold border-b-2 border-indigo-600`
- Inactive: `text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white`
- Transition: `transition-all duration-200`

### 6. Logo Clickability: Home Link vs. Non-Interactive

**Decision:** Make the logo/title clickable and navigate to `/` (Dashboard).

**Rationale:** This is a universal UX pattern. Users expect clicking the logo to return home. We'll use a `<Link>` component for accessibility and standard routing behavior.

## Risks / Trade-offs

**[Risk]** Mobile menu overlay could conflict with modals or other overlays  
→ **Mitigation:** Use a high z-index (`z-50`) and ensure modals use even higher values (`z-[60]` or above). Test with existing modals (CardFormModal, CardDetailModal, DeckDetailModal).

**[Risk]** Active route detection breaks if we introduce nested routes  
→ **Mitigation:** Current implementation uses exact path matching (`location.pathname === path`). If we add nested routes (e.g., `/decks/:id`), we'll need to update the `isActive` logic to check path prefixes.

**[Trade-off]** Sticky navbar reduces vertical space on small screens  
→ **Acceptance:** This is standard behavior and expected by users. The navbar is ~64px tall, which is reasonable. If needed, we can make it slightly shorter (48px) on mobile.

**[Trade-off]** Adding a new route requires updating the Navbar component  
→ **Acceptance:** This is acceptable for a small app with 4 routes. If we scale to 10+ routes, we could move navigation config to a data structure, but that's premature optimization now.

## Migration Plan

**Phase 1: Create Navbar Component**
1. Create `frontend/src/components/Navbar.tsx` with desktop and mobile implementations
2. Test in isolation (temporarily add to one page)

**Phase 2: Integrate in App.tsx**
1. Import and place `<Navbar />` above `<Routes>` in `App.tsx`
2. Verify all routes show the navbar correctly

**Phase 3: Clean Up Pages**
1. Remove navigation-related code from Dashboard, Settings, Analytics, DeckBuilder
2. Remove local `<Link>` imports and ThemeToggle usage in page headers
3. Adjust top padding/margin if needed (pages no longer need header space)

**Phase 4: Test**
1. Verify active state on all routes
2. Test mobile hamburger menu (open/close, navigation)
3. Test dark mode compatibility
4. Check responsiveness at breakpoints (768px)

**Rollback Strategy:**
If issues arise, we can quickly revert by:
1. Removing `<Navbar />` from App.tsx
2. Restoring navigation code in individual pages (git revert)

No database or API changes, so rollback is trivial.

## Open Questions

None - all decisions are clear and ready for implementation.
