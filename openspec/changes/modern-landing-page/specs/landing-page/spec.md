## ADDED Requirements

### Requirement: Landing page accessible without authentication
The landing page SHALL be publicly accessible at the root route `/` without requiring user authentication.

#### Scenario: Unauthenticated user views landing page
- **WHEN** an unauthenticated user navigates to `/`
- **THEN** the landing page SHALL display without redirecting to login
- **THEN** all landing page sections SHALL be visible (hero, features, demo, CTA, footer)

#### Scenario: Authenticated user views landing page
- **WHEN** an authenticated user navigates to `/`
- **THEN** the landing page SHALL display normally
- **THEN** the landing navbar SHALL show "Go to Dashboard" instead of "Login"

### Requirement: Hero section displays value proposition
The landing page hero section SHALL prominently display the product name, tagline, call-to-action buttons, and a visual preview of the dashboard.

#### Scenario: Hero content is visible above fold
- **WHEN** landing page loads on desktop (>=1024px)
- **THEN** the hero section SHALL occupy at least 80vh of viewport height
- **THEN** open source badge "100% Open Source • Community-Driven" SHALL be displayed
- **THEN** headline "Your MTG Collection, Supercharged" SHALL be displayed with purple-to-pink gradient text effect
- **THEN** subheadline explaining core value ("Community-driven, always evolving") SHALL be visible below headline
- **THEN** two CTA buttons ("Sign in" primary with Google icon, "Try Demo" secondary) SHALL be centered below text

#### Scenario: Hero dashboard preview displays
- **WHEN** hero section renders
- **THEN** a placeholder or screenshot (1200x800px, aspect ratio 3:2) SHALL display below CTAs on desktop
- **THEN** placeholder SHALL have gradient background and descriptive label if real screenshot not available
- **THEN** preview SHALL be horizontally centered and max-width constrained

#### Scenario: Hero CTAs are functional
- **WHEN** user clicks "Sign in" button
- **THEN** application SHALL redirect to Google OAuth endpoint (`http://localhost:8000/api/auth/google`)
- **WHEN** user clicks "Try Demo" button
- **THEN** application SHALL smoothly scroll to interactive demo section (smooth scroll behavior)

### Requirement: Bento Grid showcases key features
The landing page SHALL display a Bento Grid layout showcasing 3-4 key product features with visual previews.

#### Scenario: Bento Grid renders with proper layout on desktop
- **WHEN** landing page loads on desktop (>=1024px)
- **THEN** Bento Grid SHALL display in 2-3 column layout
- **THEN** Collection Management card SHALL be visible (large size, 600x500px, blue gradient)
- **THEN** Deck Builder card SHALL be visible (large size, 600x500px with "ALPHA" badge, purple gradient)
- **THEN** AI Insights card SHALL be visible (medium size, 600x400px, pink gradient)
- **THEN** Real-time Updates card SHALL be visible (small size, 500x400px, amber gradient)
- **THEN** Price Tracking & Analytics card SHALL be visible (medium size, 600x400px, green gradient)
- **THEN** Features section SHALL include message: "Missing a feature? Fork us or submit a Pull Request"
- **THEN** All feature cards SHALL have white icons and gradient backgrounds

#### Scenario: Bento Grid is responsive on tablet
- **WHEN** landing page loads on tablet (768px-1023px)
- **THEN** Bento Grid SHALL display in 2 column layout
- **THEN** cards SHALL stack vertically with appropriate gaps (1.5rem)

#### Scenario: Bento Grid is responsive on mobile
- **WHEN** landing page loads on mobile (<768px)
- **THEN** Bento Grid SHALL display in 1 column layout
- **THEN** all cards SHALL be full-width and stack vertically

#### Scenario: Feature cards have hover effects
- **WHEN** user hovers over a Bento Grid card on desktop
- **THEN** card SHALL translate upward by 4px (transform: translateY(-4px))
- **THEN** card SHALL display enhanced glow shadow effect
- **THEN** transition SHALL be smooth (300ms ease)

#### Scenario: Feature cards display content
- **WHEN** a feature card renders
- **THEN** card SHALL display feature title (e.g., "Collection Management")
- **THEN** card SHALL display brief description (1-2 sentences)
- **THEN** card SHALL display visual preview (screenshot or gradient placeholder)
- **THEN** placeholder SHALL include label indicating required screenshot dimensions

### Requirement: Interactive demo provides hands-on experience
The landing page SHALL include an interactive demo section allowing users to search and filter sample MTG cards without signup.

#### Scenario: Demo section is visible
- **WHEN** user scrolls to demo section (id="demo")
- **THEN** section header "Try Collection Library" SHALL be visible
- **THEN** subtitle "Preview our interactive collection management tool — no signup required" SHALL be displayed
- **THEN** prominent box SHALL explain "This is just one of many features. Once you sign in, unlock Deck Builder, AI Insights, Price Tracking, and more! 🚀"
- **THEN** embedded demo component SHALL render below header
- **THEN** NO sign in button SHALL appear at bottom of demo section

#### Scenario: Demo data is pre-loaded
- **WHEN** demo component initializes
- **THEN** 15 hardcoded realistic MTG cards SHALL be loaded (Lightning Bolt, Black Lotus, Serra Angel, Counterspell, Mox Jet, etc.)
- **THEN** cards SHALL display realistic data (name, set, rarity, price)
- **THEN** disclaimer "Demo data — actual prices vary" SHALL be visible in results footer

#### Scenario: Demo search is functional
- **WHEN** user types "Lightning" in demo search input
- **THEN** card list SHALL filter to show only cards matching "Lightning" (case-insensitive)
- **THEN** results count SHALL update (e.g., "Results: 1 card")

#### Scenario: Demo filters are functional
- **WHEN** user clicks "Rare" rarity filter button
- **THEN** card list SHALL filter to show only Rare rarity cards
- **THEN** filter button SHALL display active state (highlighted)
- **THEN** results count SHALL update

#### Scenario: Demo combines search and filters
- **WHEN** user has both search text ("Bolt") and rarity filter (Common) active
- **THEN** card list SHALL show only cards matching both criteria
- **THEN** results count SHALL reflect combined filters

### Requirement: Final CTA encourages signup
The landing page SHALL include a final call-to-action section before the footer to convert visitors.

#### Scenario: Final CTA content is visible
- **WHEN** user scrolls to final CTA section
- **THEN** headline "Ready to supercharge your collection?" SHALL be visible
- **THEN** subtext encouraging signup SHALL be displayed
- **THEN** primary CTA button "Get Started Free" SHALL be centered

#### Scenario: Final CTA button navigates to signup
- **WHEN** user clicks "Sign in Free" button
- **THEN** application SHALL redirect to Google OAuth endpoint (`http://localhost:8000/api/auth/google`)

### Requirement: Footer provision - REMOVED FOR MVP
The footer was initially planned but removed from the MVP implementation to focus on core conversion features. Footer can be added in a future phase if needed.

**Rationale for removal:**
- Not essential for MVP landing page conversion goals
- Reduces complexity and page size
- Simplifies maintenance
- Can be added as a separate enhancement when marketing content grows

### Requirement: Landing page supports dark mode
The landing page SHALL adapt its appearance based on the active theme (light or dark mode).

#### Scenario: Dark mode styling is applied
- **WHEN** user has dark mode enabled
- **THEN** landing page background SHALL use dark gradient (slate-900 to purple-900)
- **THEN** text colors SHALL use light variants (slate-50, slate-100)
- **THEN** card backgrounds SHALL use dark semi-transparent overlays
- **THEN** borders and shadows SHALL use appropriate dark mode variants

### Requirement: Landing page has smooth scroll animations
The landing page SHALL use scroll-triggered animations to reveal content progressively.

#### Scenario: Sections fade in on scroll
- **WHEN** user scrolls and a section enters viewport
- **THEN** section SHALL animate from opacity 0 to 1
- **THEN** section SHALL slide up from 20px below to final position
- **THEN** animation SHALL last 600ms with ease-out timing

#### Scenario: Bento Grid cards stagger animation
- **WHEN** Bento Grid section enters viewport
- **THEN** cards SHALL animate in sequence with 100ms stagger delay
- **THEN** each card SHALL fade in and slide up individually

### Requirement: Landing page performance is optimized
The landing page SHALL load quickly and be responsive to user interactions.

#### Scenario: Landing page lazy loads
- **WHEN** user navigates to `/` for first time
- **THEN** landing page component SHALL be code-split and lazy loaded
- **THEN** Framer Motion library SHALL only load for landing page route

#### Scenario: Images have appropriate placeholders
- **WHEN** screenshot images are loading
- **THEN** gradient placeholders SHALL display immediately
- **THEN** placeholders SHALL have same aspect ratio as final images

### Requirement: Landing navbar differs from dashboard navbar
The landing page SHALL use a specialized navbar variant optimized for conversion with GitHub integration.

#### Scenario: Landing navbar structure
- **WHEN** landing page renders for unauthenticated user
- **THEN** navbar SHALL display: Logo | Features (✨) | Source Code (🔗) | Sign in button
- **THEN** navbar SHALL NOT display dashboard navigation links
- **WHEN** landing page renders for authenticated user
- **THEN** navbar SHALL display: Logo | Features (✨) | Source Code (🔗) | Go to Dashboard button

#### Scenario: Landing navbar is sticky with backdrop blur
- **WHEN** user scrolls down landing page
- **THEN** navbar SHALL remain fixed at top of viewport
- **THEN** navbar background SHALL transition from transparent to dark solid with backdrop-filter blur (300ms)
- **THEN** border bottom shall appear on scroll

#### Scenario: Landing navbar structure and positioning
- **WHEN** landing page renders
- **THEN** navbar SHALL display in three sections:
  - Left: DeckDex logo
  - Center: Features link with Sparkles icon
  - Right: Source Code link with GitHub icon
- **THEN** navbar SHALL be sticky and remain at top when scrolling
- **THEN** on scroll, background SHALL transition to dark with backdrop blur

#### Scenario: Landing navbar navigation items
- **WHEN** user clicks "Features" link
- **THEN** page SHALL smoothly scroll to features section (id="features")
- **WHEN** user clicks "Source Code" link
- **THEN** elegant modal SHALL open showing GitHub information
- **THEN** modal SHALL NOT open new tab or navigate away
- **WHEN** user clicks GitHub repository button in modal
- **THEN** new tab SHALL open to `https://github.com/fjpulidop/deckdex_mtg`
- **WHEN** user clicks logo/title in landing navbar
- **THEN** page SHALL scroll smoothly to top of landing page (no route change)

#### Scenario: Dynamic CTA buttons based on auth state
- **WHEN** unauthenticated user visits landing page
- **THEN** Hero "Sign in" button SHALL show with Google icon
- **THEN** Final CTA "Sign in Free" button SHALL show with Google icon
- **WHEN** authenticated user visits landing page
- **THEN** Hero button SHALL change to "Go to Dashboard"
- **THEN** Final CTA button SHALL change to "Go to Dashboard"

#### Scenario: Post-login redirect
- **WHEN** user clicks "Sign in" button
- **THEN** application SHALL redirect to Google OAuth (`http://localhost:8000/api/auth/google`)
- **WHEN** user completes OAuth authentication
- **THEN** backend SHALL set JWT cookie
- **THEN** backend SHALL redirect to `http://localhost:5173/dashboard` (NOT landing page)
- **THEN** user SHALL see dashboard immediately

#### Scenario: Logout flow
- **WHEN** authenticated user logs out from dashboard
- **THEN** application SHALL clear JWT cookie
- **THEN** application SHALL redirect to `/` (landing page)
- **THEN** user SHALL see landing page with unauthenticated state
