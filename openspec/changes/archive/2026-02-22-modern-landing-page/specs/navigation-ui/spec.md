## MODIFIED Requirements

### Requirement: Logo navigates to home
The navbar logo/title SHALL be clickable and navigate to the appropriate home page based on authentication state and current context.

#### Scenario: Logo click from authenticated dashboard routes
- **WHEN** authenticated user is on any dashboard page (e.g., Settings, Analytics, Decks)
- **THEN** user clicks the "DeckDex MTG" logo/title
- **THEN** the application navigates to the Dashboard page (path: `/dashboard`)

#### Scenario: Logo click from landing page scrolls to top
- **WHEN** user is on the landing page (path: `/`)
- **THEN** user clicks the "DeckDex MTG" logo/title in landing navbar
- **THEN** the page SHALL scroll smoothly to the top of the landing page
- **THEN** no route navigation SHALL occur

### Requirement: Active route is visually indicated
The navigation component SHALL provide clear visual feedback showing which route is currently active in dashboard navbar.

#### Scenario: Active link has distinctive styling on dashboard
- **WHEN** user is on the Dashboard page (path: `/dashboard`)
- **THEN** the Dashboard link displays with primary color (indigo-600), semibold font weight, and a 2px bottom border
- **THEN** all other navigation links display in neutral gray color

#### Scenario: Active state updates on navigation
- **WHEN** user clicks the Analytics link from the Dashboard page
- **THEN** the Analytics link becomes the active link with distinctive styling
- **THEN** the Dashboard link returns to neutral inactive styling

#### Scenario: Landing navbar has no active state
- **WHEN** user is on the landing page (path: `/`)
- **THEN** landing navbar SHALL NOT display active state indicators for any links
- **THEN** landing navbar links (Features, Docs) SHALL have consistent styling

### Requirement: Navbar hidden on login page
The navbar SHALL NOT be displayed on the `/login` route.

#### Scenario: No navbar on login page
- **WHEN** the current route is `/login`
- **THEN** neither dashboard navbar NOR landing navbar SHALL render

#### Scenario: Landing navbar shown on landing page
- **WHEN** the current route is `/`
- **THEN** landing navbar SHALL render (NOT dashboard navbar)

#### Scenario: Dashboard navbar shown on authenticated routes
- **WHEN** the current route is `/dashboard`, `/analytics`, `/decks`, or `/settings`
- **THEN** dashboard navbar SHALL render (NOT landing navbar)

## ADDED Requirements

### Requirement: Landing navbar displays conversion-focused elements
The landing navbar SHALL display elements optimized for converting visitors to signups.

#### Scenario: Landing navbar shows login and signup buttons
- **WHEN** landing navbar renders for unauthenticated user
- **THEN** navbar right section SHALL display "Login" button with ghost/outline style
- **THEN** navbar right section SHALL display "Sign Up" button with primary solid style
- **THEN** "Sign Up" button SHALL be positioned to the right of "Login" button

#### Scenario: Landing navbar shows Go to Dashboard for authenticated users
- **WHEN** landing navbar renders for authenticated user
- **THEN** navbar right section SHALL display "Go to Dashboard" button instead of "Login"
- **THEN** "Sign Up" button SHALL be hidden
- **THEN** clicking "Go to Dashboard" SHALL navigate to `/dashboard`

#### Scenario: Landing navbar login button navigates to login
- **WHEN** user clicks "Login" button in landing navbar
- **THEN** application SHALL navigate to `/login` route

#### Scenario: Landing navbar signup button navigates to login
- **WHEN** user clicks "Sign Up" button in landing navbar
- **THEN** application SHALL navigate to `/login` route
- **THEN** login page MAY display signup-specific messaging (future enhancement)

### Requirement: Landing navbar has sticky behavior with backdrop blur
The landing navbar SHALL remain visible during scroll with progressive backdrop blur effect.

#### Scenario: Landing navbar is initially transparent
- **WHEN** landing page loads and scroll position is at top (scrollY === 0)
- **THEN** landing navbar background SHALL be semi-transparent or fully transparent
- **THEN** navbar SHALL have no backdrop blur

#### Scenario: Landing navbar gains backdrop blur on scroll
- **WHEN** user scrolls down landing page (scrollY > 50px)
- **THEN** landing navbar background SHALL transition to semi-opaque
- **THEN** navbar SHALL apply backdrop-filter blur effect (blur(10px))
- **THEN** transition SHALL be smooth (300ms duration)

#### Scenario: Landing navbar returns to transparent on scroll top
- **WHEN** user scrolls back to top of landing page (scrollY < 50px)
- **THEN** landing navbar SHALL transition back to transparent state
- **THEN** backdrop blur SHALL be removed

### Requirement: Landing navbar shows navigation links
The landing navbar SHALL display links to sections and resources.

#### Scenario: Landing navbar shows Features and Docs links
- **WHEN** landing navbar renders on desktop (>=768px)
- **THEN** navbar center section SHALL display "Features" link
- **THEN** navbar center section SHALL display "Docs" link (if docs exist)
- **THEN** links SHALL use neutral color (not primary)

#### Scenario: Landing navbar links scroll to sections
- **WHEN** user clicks "Features" link in landing navbar
- **THEN** page SHALL smooth-scroll to features/Bento Grid section
- **THEN** no route navigation SHALL occur

#### Scenario: Landing navbar is responsive on mobile
- **WHEN** landing navbar renders on mobile (<768px)
- **THEN** navigation links SHALL be hidden behind hamburger menu
- **THEN** hamburger menu SHALL include Features, Docs, Login, and Sign Up

### Requirement: Landing navbar uses landing-specific styling
The landing navbar SHALL use visual styling distinct from dashboard navbar.

#### Scenario: Landing navbar has dark background
- **WHEN** landing navbar renders
- **THEN** navbar SHALL have dark background (slate-900/indigo-900) matching landing page theme
- **THEN** text SHALL use light colors (white/slate-100)

#### Scenario: Landing navbar buttons have distinct styling
- **WHEN** landing navbar renders
- **THEN** "Login" button SHALL have border with transparent background (ghost style)
- **THEN** "Sign Up" button SHALL have solid primary background (purple/violet gradient)
- **THEN** buttons SHALL have hover effects (scale, glow)
