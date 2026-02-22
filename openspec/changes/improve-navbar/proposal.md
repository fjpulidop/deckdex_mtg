## Why

The current navigation consists of simple text links scattered inconsistently across pages, with different layouts in each view (Dashboard, Settings, Analytics, DeckBuilder). This creates a fragmented user experience and lacks professional polish. Users need clear visual feedback about their current location and a consistent way to navigate between sections.

## What Changes

- Create a unified `Navbar` component with consistent styling and behavior across all pages
- Implement sticky top positioning so navigation remains accessible during scroll
- Add visual indicators for the active/current route (color, font weight, underline)
- Support responsive design with hamburger menu for mobile devices (<768px)
- Make the logo/title clickable to return to Dashboard
- Integrate existing `ThemeToggle` component into the navbar
- Remove redundant navigation code from individual page components
- Maintain existing badges (alpha/beta) on navigation items

## Capabilities

### New Capabilities
- `navigation-ui`: Unified navigation component with route awareness, active state indication, sticky positioning, and responsive mobile support

### Modified Capabilities
<!-- No existing spec-level requirements are changing -->

## Impact

**New Files:**
- `frontend/src/components/Navbar.tsx` - Main navigation component

**Modified Files:**
- `frontend/src/App.tsx` - Add Navbar component at top level (outside router)
- `frontend/src/pages/Dashboard.tsx` - Remove inline navigation links
- `frontend/src/pages/Settings.tsx` - Remove inline navigation and nav element
- `frontend/src/pages/Analytics.tsx` - Remove inline navigation links
- `frontend/src/pages/DeckBuilder.tsx` - Remove inline navigation links

**Dependencies:**
- Uses `react-router-dom` (already installed) for `useLocation` hook and route detection
- Uses existing Tailwind classes for styling
- Integrates existing `ThemeToggle` component

**UI/UX Impact:**
- More professional appearance with consistent navigation
- Better user orientation with active state indicators
- Improved mobile experience with hamburger menu
- Cleaner page components without duplicated navigation logic
