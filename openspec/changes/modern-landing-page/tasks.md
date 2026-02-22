## 1. Setup and Dependencies

- [x] 1.1 Install framer-motion package (`npm install framer-motion`)
- [x] 1.2 Install lucide-react package (`npm install lucide-react`)
- [x] 1.3 Install react-countup package (`npm install react-countup`)
- [x] 1.4 Create `frontend/src/components/landing/` directory structure
- [x] 1.5 Extend Tailwind config with custom colors (primary violet/purple, accent pink gradients)

## 2. Landing Page Components - LandingNavbar

- [x] 2.1 Create `LandingNavbar.tsx` component with logo, Features/Docs links, Login/Sign Up buttons
- [x] 2.2 Implement sticky navbar with scroll-triggered backdrop blur effect (transparent at top, blur on scroll)
- [x] 2.3 Add conditional rendering: show "Go to Dashboard" for authenticated users, Login/Sign Up for unauthenticated
- [x] 2.4 Implement smooth scroll to sections when clicking Features link
- [x] 2.5 Style navbar with dark background and light text (landing-specific theme)
- [x] 2.6 Make navbar responsive with hamburger menu on mobile (<768px)

## 3. Landing Page Components - Hero Section

- [x] 3.1 Create `Hero.tsx` component with main headline "Your MTG Collection, Supercharged"
- [x] 3.2 Add gradient text effect to headline (purple-to-pink gradient with bg-clip-text)
- [x] 3.3 Add subheadline explaining value proposition (track prices, build decks, AI insights)
- [x] 3.4 Create dual CTA buttons: "Get Started" (primary) and "Watch Demo" (secondary)
- [x] 3.5 Implement "Get Started" navigation to `/login`
- [x] 3.6 Implement "Watch Demo" smooth scroll to interactive demo section
- [x] 3.7 Add dashboard preview placeholder (1200x800px, gradient background with label)
- [x] 3.8 Add Framer Motion fade-in animation on hero load (initial: opacity 0, y: 20)
- [x] 3.9 Make hero responsive (adjust text sizes, stack on mobile)

## 4. Landing Page Components - Bento Grid

- [x] 4.1 Create `BentoGrid.tsx` container with CSS Grid layout (1 col mobile, 2 col tablet, 2-3 col desktop)
- [x] 4.2 Create `BentoCard.tsx` component with props: feature, size, title, description, preview
- [x] 4.3 Add Collection Management card (large, 600x500px) with gradient placeholder
- [x] 4.4 Add Deck Builder card (large, 600x500px) with gradient placeholder and "ALPHA" badge
- [x] 4.5 Add AI Insights card (medium, 600x400px) with gradient placeholder
- [x] 4.6 Add Real-time Progress card (small, 500x400px, optional) with gradient placeholder
- [x] 4.7 Implement hover effects on cards (translateY(-4px), enhanced glow shadow, 300ms transition)
- [x] 4.8 Add Framer Motion stagger animation when Bento Grid enters viewport (100ms stagger per card)
- [x] 4.9 Add descriptive labels to placeholders indicating required screenshot dimensions and content

## 5. Landing Page Components - Interactive Demo

- [x] 5.1 Create `InteractiveDemo.tsx` component with section header "Try DeckDex Right Now"
- [x] 5.2 Add hardcoded demo data array with 10-15 realistic MTG cards (Lightning Bolt, Black Lotus, Serra Angel, etc.)
- [x] 5.3 Implement search input field with real-time filtering (case-insensitive name match)
- [x] 5.4 Implement rarity filter buttons (All, Common, Uncommon, Rare, Mythic) with active state
- [x] 5.5 Add combined filtering logic (search AND rarity work together)
- [x] 5.6 Create simplified CardTable display (Name, Set, Rarity, Price columns)
- [x] 5.7 Add results count display (e.g., "Results: 3 cards") with proper singular/plural grammar
- [x] 5.8 Add "Demo data" disclaimer text in muted color
- [x] 5.9 Add CTA button below demo "Create Your Free Account" navigating to `/login`
- [x] 5.10 Make demo responsive (scrollable table on mobile, wrapping filter buttons)

## 6. Landing Page Components - Final CTA and Footer

- [x] 6.1 Create `FinalCTA.tsx` with headline "Ready to supercharge your collection?"
- [x] 6.2 Add subtext encouraging signup and primary button "Get Started Free" navigating to `/login`
- [x] 6.3 Create `Footer.tsx` with 4 columns: Product, Company, Resources, Legal
- [x] 6.4 Add footer links (Features, Pricing, Docs, Blog, About, etc.) with placeholders
- [x] 6.5 Add copyright notice and social media icon placeholders (Twitter, Discord, GitHub)
- [x] 6.6 Make footer responsive (stack columns vertically on mobile)

## 7. Landing Page - Main Orchestrator

- [x] 7.1 Create `pages/Landing.tsx` importing all landing components
- [x] 7.2 Compose Landing page structure: LandingNavbar, Hero, Bento Grid, Interactive Demo, Final CTA, Footer
- [x] 7.3 Add dark theme background gradient (slate-900 to purple-900)
- [x] 7.4 Ensure proper spacing between sections (py-16 or py-24)
- [x] 7.5 Test Landing page in isolation before routing changes

## 8. Routing Changes

- [x] 8.1 Update `App.tsx`: add route `<Route path="/" element={<Landing />} />`
- [x] 8.2 Update `App.tsx`: change Dashboard route to `<Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />`
- [x] 8.3 Update `AppContent` to conditionally render LandingNavbar (when `pathname === '/'`) vs. Navbar (dashboard routes)
- [x] 8.4 Ensure login page route still hides all navbars (`isLoginPage` check)
- [x] 8.5 Update `ProtectedRoute` component: redirect unauthenticated users to `/login`, authenticated users accessing protected routes should work normally

## 9. Auth Flow Updates

- [x] 9.1 Update `AuthContext` or `Login.tsx`: change post-login redirect from `/` to `/dashboard`
- [x] 9.2 Update dashboard Navbar logo link: navigate to `/dashboard` instead of `/` (for authenticated users)
- [x] 9.3 Test authenticated user flow: login → redirects to `/dashboard`
- [x] 9.4 Test authenticated user visits `/` → should see landing page (or optionally redirect to `/dashboard`)
- [x] 9.5 Test unauthenticated user visits `/dashboard` → redirects to `/login`

## 10. Login Page Simplification (Optional)

- [x] 10.1 Remove marketing content from `Login.tsx` (if any exists beyond the form)
- [x] 10.2 Ensure login page shows minimal form: Google OAuth button, error messages, footer text
- [x] 10.3 Test login page renders correctly at `/login` route

## 11. Code Splitting and Performance

- [x] 11.1 Wrap Landing page import with React.lazy() for code splitting
- [x] 11.2 Add Suspense boundary in App.tsx for lazy-loaded Landing
- [x] 11.3 Test that landing page bundle loads separately (check network tab)
- [x] 11.4 Verify Framer Motion only loads when landing page is visited

## 12. Testing and Validation

- [x] 12.1 Test unauthenticated user visits `/` → landing page displays
- [x] 12.2 Test clicking "Get Started" → navigates to `/login`
- [x] 12.3 Test clicking "Watch Demo" → smooth scrolls to demo section
- [x] 12.4 Test interactive demo search functionality (type "bolt", see filtered results)
- [x] 12.5 Test interactive demo rarity filters (click "Rare", see only Rare cards)
- [x] 12.6 Test combined filters (search + rarity) work correctly
- [x] 12.7 Test login flow → redirects to `/dashboard` after successful authentication
- [x] 12.8 Test authenticated user navigates to `/dashboard` → Dashboard page loads
- [x] 12.9 Test dashboard navbar logo → navigates to `/dashboard`
- [x] 12.10 Test landing page on mobile (responsive layout, hamburger menu works)
- [x] 12.11 Test Bento Grid on tablet (2 columns) and mobile (1 column stack)
- [x] 12.12 Test all animations work (hero fade-in, Bento stagger, hover effects)
- [x] 12.13 Test dark mode styling on landing page (gradients, text colors, borders)

## 13. Documentation and Assets

- [x] 13.1 Document screenshot requirements in `frontend/README.md` or separate doc (sizes, content, filenames)
- [x] 13.2 Add placeholder gradient images for Bento cards with clear labels (Collection, Deck Builder, AI, Real-time)
- [x] 13.3 Update main README.md to reflect new routing structure (`/` = landing, `/dashboard` = app)
- [x] 13.4 Add instructions for capturing real screenshots to replace placeholders
