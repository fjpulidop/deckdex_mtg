# Navigation UI Polish Exploration (2026-03-07)

## Area: Navigate UI polish (desktop/mobile)

### Current State

The navbar was built via an OpenSpec change (`2026-02-22-improve-navbar`, archived). The spec at `openspec/specs/navigation-ui/spec.md` defines 10 requirements. Most are implemented:

**Implemented (working well):**
- Sticky top navbar with `sticky top-0 z-40`
- Logo "DeckDex MTG" links to `/dashboard`
- Desktop nav links: Collection, Deck Builder (alpha), Analytics (beta), Admin (conditional)
- Active route indication: indigo-600 color + semibold + 2px bottom border
- Hover transitions on inactive links (200ms)
- Dark mode support throughout navbar
- Mobile hamburger menu (md breakpoint at 768px)
- Mobile menu closes on link click
- Outside click closes menus (mousedown listener)
- ESC key closes menus
- Theme toggle in navbar (desktop always visible)
- User dropdown with Profile, Settings, Logout + divider
- User avatar with fallback icon
- Status badges (alpha/beta pills)
- i18n via react-i18next (all labels use `t()`)
- Navbar hidden on login page and demo page
- LandingNavbar separate component for `/` route (different styling, scroll-aware transparency)

**Two navbar components:**
1. `Navbar.tsx` (253 lines) -- main app navbar, used on all authenticated pages
2. `LandingNavbar.tsx` (157 lines) -- landing page only, dark theme, smooth-scroll anchors

### Gaps Found

#### BUG: LanguageSwitcher invisible in light mode
- `LanguageSwitcher.tsx` uses hardcoded `text-slate-300` (inactive) and `text-white` (active lang)
- These colors were designed for the dark landing page background
- On the main Navbar (`bg-white` in light mode), both are nearly/completely invisible
- Active language (`text-white`) is literally invisible on white background
- **Severity: HIGH** -- users cannot see or use language switching in light mode on non-landing pages

#### Mobile menu backdrop broken
- Backdrop div uses `top-[calc(100%+4rem)]` which is wrong -- it calculates from the viewport, not the navbar
- The backdrop should cover the area below the navbar, but the calc doesn't reference the navbar height
- Result: backdrop may not cover the right area, making outside-click-to-close unreliable
- The mobile menu content itself is inside the `<nav>` (inline, not overlay), so it pushes page content down rather than overlaying

#### No mobile menu animation
- Menu appears/disappears instantly (`{mobileMenuOpen && ...}`)
- No slide-down, fade-in, or any transition -- feels jarring
- LandingNavbar has the same issue
- Competitors (Moxfield, Archidekt) use smooth slide animations

#### No focus management or keyboard navigation
- No `focus-visible` rings on any navbar element
- User dropdown missing `role="menu"`, `aria-haspopup`, `role="menuitem"`
- No focus trap in mobile menu
- No keyboard arrow-key navigation in user dropdown
- Tab order not managed when mobile menu opens (can tab to elements behind menu)

#### Import page not in nav
- `/import` route exists and is a protected page, but has no navbar link
- Users can only reach it through Dashboard action buttons
- Discoverability problem -- new users may not know Import exists

#### No breadcrumbs or secondary navigation
- No breadcrumb component anywhere in codebase
- On deeper pages (future deck detail, card detail), users have no path context
- Not critical now but becomes important as navigation depth increases

#### Page content container inconsistency
- Dashboard: `container mx-auto px-4 py-8`
- Analytics: `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8`
- DeckBuilder: `container mx-auto px-4 py-8`
- Settings: `container mx-auto px-4 py-8 max-w-2xl`
- Admin: `container mx-auto px-4 py-8 max-w-4xl`
- Import: `max-w-xl mx-auto`
- No shared layout wrapper -- each page defines its own container

#### No scroll-to-top on navigation
- When navigating between pages, scroll position may persist
- React Router v6 doesn't auto-scroll to top

#### JobsBottomBar overlaps mobile content
- Fixed `bottom-4 right-4` pill can overlap page content on small screens
- Expanded panel is `w-96` (384px) which exceeds most phone widths (375px iPhone SE)
- No responsive width on the jobs panel

#### LanguageSwitcher in mobile menu is duplicated
- Desktop: LanguageSwitcher shown in right section (always visible, line 117)
- Mobile: LanguageSwitcher also shown inside mobile menu (line 230)
- But LanguageSwitcher is ALSO visible in the right section on mobile (it's not hidden with `hidden md:flex`)
- So on mobile, users see the (invisible) language switcher in the top bar AND inside the hamburger menu

### Improvement Ideas

| # | Idea | Value | Complexity | Impact/Effort | Notes |
|---|------|-------|------------|---------------|-------|
| 1 | Fix LanguageSwitcher colors for light/dark mode | Critical | Small | **5.0** | BUG FIX: Use gray-600/dark:gray-400 like other nav elements. ~15min fix |
| 2 | Add mobile menu slide animation | Medium | Small | **3.5** | CSS transition or Headless UI Transition. Smooth open/close. ~1hr |
| 3 | Fix mobile backdrop positioning | Medium | Small | **3.5** | Replace calc hack with proper overlay. ~30min |
| 4 | Add shared page layout wrapper | Medium | Medium | **3.0** | `<PageLayout maxWidth="7xl">` component to standardize containers. ~2hrs |
| 5 | Hide LanguageSwitcher from top bar on mobile | Low | Small | **3.0** | Add `hidden md:block` to desktop LanguageSwitcher. ~5min |
| 6 | Add focus-visible rings to all interactive elements | Medium | Small | **3.0** | `focus-visible:ring-2 focus-visible:ring-indigo-500`. ~1hr |
| 7 | Add ARIA roles to user dropdown | Medium | Small | **2.5** | role="menu", aria-haspopup, role="menuitem". ~30min |
| 8 | Make JobsBottomBar responsive | Medium | Medium | **2.5** | `w-[calc(100vw-2rem)] md:w-96` on expanded panel. ~1hr |
| 9 | Add scroll-to-top on navigation | Low | Small | **2.5** | ScrollRestoration component or useEffect in App. ~15min |
| 10 | Add Import link to navbar | Low | Small | **2.0** | Add to navLinks array with appropriate badge. ~10min |
| 11 | Add keyboard arrow navigation in dropdown | Low | Medium | **1.5** | Arrow keys cycle through menu items. ~2hrs |
| 12 | Add breadcrumb component | Low | Medium | **1.0** | Not needed until sub-pages exist (deck detail, etc.) |
| 13 | Mobile-optimized bottom tab bar | High | Large | **1.5** | Replace hamburger with iOS/Android-style bottom tabs on mobile. Big UX win but significant rework |

### Recommended Top Pick

**Idea #1: Fix LanguageSwitcher colors** is the highest-priority item. It's a genuine bug -- the language switcher is effectively invisible in light mode on the main app navbar. The fix is trivial (change hardcoded `text-slate-300`/`text-white` to context-aware `text-gray-600 dark:text-gray-300` and `text-gray-900 dark:text-white font-semibold`).

**Best bundle for a single PR:** Ideas #1 + #3 + #5 + #6 together. All are small fixes that can ship as a "nav polish" PR in under 2 hours total. They fix the most visible bugs and add baseline accessibility polish.

**Highest long-term value:** Idea #4 (shared page layout wrapper). Every page reinvents its container, and as more pages are added this divergence will worsen. A `<PageLayout>` component wrapping `<main>` with consistent padding, max-width, and scroll-to-top behavior would standardize all pages at once.

### Architecture Notes

- Navbar is rendered at App.tsx level (line 38), outside Routes -- correct pattern
- No layout route wrapper (React Router `<Outlet>`) -- pages are individually wrapped in `<ProtectedRoute>`
- Two separate navbar components with duplicated patterns (hamburger, menu state, click-outside) -- could share a custom hook
- Mobile menu is inline (pushes content down) rather than overlay (covers content) -- this is an intentional design choice per the spec, but overlay would feel more app-like
