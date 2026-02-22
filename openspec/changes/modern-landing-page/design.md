## Context

DeckDex MTG is a React 19 + TypeScript + Vite + Tailwind CSS frontend currently routing unauthenticated users directly to `/login`. The authenticated app lives at `/` (Dashboard, Analytics, Decks, Settings). Users cannot see product features before signup, reducing conversion. We need a public landing page at `/` showcasing features with modern, vibrant design (Stripe-inspired: gradients, glows, Bento Grid, smooth animations).

Current routing:
- `/` → Dashboard (protected)
- `/login` → Login page (public)
- `/dashboard`, `/analytics`, `/decks`, `/settings` → Not used

Current tech: React Router v6, AuthContext, Tailwind CSS v4, no animation libraries.

## Goals / Non-Goals

**Goals:**
- Create conversion-optimized public landing page at `/` with no authentication
- Showcase 3-4 key features (Collection Management, Deck Builder, AI Insights) via Bento Grid with visual previews
- Provide interactive demo allowing search/filter on hardcoded MTG card data
- Implement Stripe-inspired vibrant design (gradients, glows, smooth animations via Framer Motion)
- Move authenticated dashboard to `/dashboard` route
- Update navbar to show landing variant (top-right login/signup) vs. dashboard variant (current)
- Minimize login page to simple form

**Non-Goals:**
- Backend changes (landing is entirely client-side)
- Real API calls in interactive demo (uses hardcoded data)
- Multi-page marketing site (single landing page only)
- SEO optimization or meta tags (can be added later)
- Mobile-specific video or heavy media (use placeholders for now)
- A/B testing or analytics tracking (can be added later)

## Decisions

### 1. Routing Strategy: Root vs. Subdomain

**Decision:** Move authenticated app to `/dashboard` and use `/` for public landing.

**Rationale:**
- SEO and marketing best practice: public content at root URL
- Simpler architecture than subdomain (no CORS, no separate deployment)
- React Router handles this trivially with route order

**Alternatives considered:**
- **Subdomain** (app.deckdex.com): More complex deployment, CORS issues, not worth it for MVP
- **Keep dashboard at `/`**: Misses conversion opportunity, against industry standard

**Implementation:**
- Update `App.tsx` route order: Landing at `/`, Dashboard at `/dashboard`
- Update `ProtectedRoute` redirect logic: unauthenticated → `/login`, authenticated home → `/dashboard`
- Update login success redirect: `/` → `/dashboard`
- Update navbar links in authenticated views to use `/dashboard`

### 2. Component Architecture: Monolithic vs. Composable

**Decision:** Create modular components in `components/landing/` folder.

**Rationale:**
- Reusability: Hero, BentoGrid, BentoCard, InteractiveDemo, Footer can be tested independently
- Maintainability: Clear boundaries, easier to swap designs
- Landing-specific: Keeps landing code separate from dashboard code

**Structure:**
```
frontend/src/
├── pages/
│   └── Landing.tsx          // Main orchestrator
├── components/
│   ├── landing/             // Landing-specific components
│   │   ├── LandingNavbar.tsx
│   │   ├── Hero.tsx
│   │   ├── BentoGrid.tsx
│   │   ├── BentoCard.tsx
│   │   ├── InteractiveDemo.tsx
│   │   ├── FinalCTA.tsx
│   │   └── Footer.tsx
│   └── Navbar.tsx           // Dashboard navbar (existing)
```

**Alternatives considered:**
- **Monolithic Landing.tsx**: Harder to test, less reusable
- **Shared components folder**: Mixes landing and dashboard concerns

### 3. Navbar Handling: Conditional Rendering vs. Separate Components

**Decision:** Create separate `LandingNavbar` component, conditionally render in `App.tsx`.

**Rationale:**
- Landing navbar (logo, features, source code, sign in) differs significantly from dashboard navbar (logo, nav links, user menu)
- Simpler logic than complex conditional props in single component
- Landing navbar is sticky with backdrop blur on scroll; dashboard navbar is always visible

**Landing Navbar Structure:**
- Logo (clickable, smooth scroll to top)
- Features link (with Sparkles icon, smooth scroll to features section)
- Source Code link (with GitHub icon, opens modal showing GitHub repo)
- Sign in button (only visible when unauthenticated, uses Google OAuth)
- Go to Dashboard button (only visible when authenticated)

**GitHub Modal Design:**
- Elegant dark themed modal with backdrop blur
- Shows GitHub logo and project name
- Encourages contributions and community involvement
- "Open GitHub Repository" button that opens in new tab
- Can be dismissed by clicking backdrop or X button

**Implementation:**
```tsx
function AppContent() {
  const location = useLocation();
  const isLandingPage = location.pathname === '/';
  const isLoginPage = location.pathname === '/login';

  return (
    <>
      {isLandingPage && <LandingNavbar />}
      {!isLandingPage && !isLoginPage && <Navbar />}
      <Routes>...</Routes>
    </>
  );
}
```

**Alternatives considered:**
- **Single Navbar with `variant` prop**: More complex conditionals, harder to maintain
- **No navbar on landing**: Against best practices, users expect navigation
- **External GitHub link**: External link breaks user engagement; modal keeps users on page

### 4. Bento Grid Layout: CSS Grid vs. Manual Positioning

**Decision:** Use CSS Grid with Tailwind's grid utilities.

**Rationale:**
- Responsive by default (1 col mobile, 2 col tablet, 2-3 col desktop)
- Tailwind provides `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- Easier to maintain than absolute positioning
- Auto-flow handles variable card sizes naturally

**Implementation:**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <BentoCard size="large" feature="collection" />
  <BentoCard size="large" feature="deck-builder" />
  <BentoCard size="medium" feature="ai-insights" />
  <BentoCard size="small" feature="realtime" />
</div>
```

**Card sizes via Tailwind:**
- `large`: `col-span-1 row-span-2` (600x500px)
- `medium`: `col-span-2 row-span-1` (600x400px)
- `small`: `col-span-1 row-span-1` (500x400px)

**Alternatives considered:**
- **Flexbox**: Less control over 2D layout
- **Absolute positioning**: Not responsive, hard to maintain

### 5. Interactive Demo: Embedded Mini-Dashboard vs. Iframe

**Decision:** Embedded React component with hardcoded data (10-15 cards).

**Rationale:**
- Full control over styling and behavior
- No iframe sandbox issues
- Can share Tailwind styles and components
- Faster load time (no separate page)

**Data strategy:**
```typescript
const demoCards = [
  { id: 1, name: "Lightning Bolt", set: "M11", rarity: "Common", price: 0.50 },
  { id: 2, name: "Black Lotus", set: "Alpha", rarity: "Rare", price: 50000 },
  // ... 8-13 more cards
];
```

**Features:**
- Live search (client-side filter by name)
- Rarity filters (Common, Uncommon, Rare, Mythic)
- Simplified CardTable component (reuse styling, not full CRUD)

**Alternatives considered:**
- **Iframe to demo site**: Slow, sandbox issues
- **API calls to real backend**: Requires backend changes, slower, overkill

### 6. Animation Library: Framer Motion vs. CSS Animations

**Decision:** Framer Motion for complex animations, CSS for simple ones.

**Rationale:**
- Framer Motion: Declarative, supports variants, stagger, scroll triggers
- CSS: Better for hover effects, simple fades
- Hybrid approach: use best tool for each job

**Key animations:**
- Hero fade-in: Framer Motion (`initial`, `animate`)
- Bento cards stagger: Framer Motion (`variants`, `staggerChildren`)
- Card hover lift: CSS (`transform: translateY(-4px)`)
- Navbar backdrop blur on scroll: CSS (`backdrop-filter`)
- Glow effects: CSS (`box-shadow` with color opacity)

**Alternatives considered:**
- **React Spring**: More imperative, steeper learning curve
- **CSS only**: Can't do stagger or scroll-triggered animations easily
- **GSAP**: Overkill for this use case, larger bundle

### 7. Design Tokens: Custom Theme vs. Tailwind Defaults

**Decision:** Extend Tailwind config with custom colors, use Tailwind spacing/typography.

**Custom palette (Stripe-inspired vibrant):**
```javascript
// tailwind.config.js
theme: {
  extend: {
    colors: {
      primary: {
        500: '#8b5cf6',  // Violet
        600: '#7c3aed',
        700: '#6d28d9',
      },
      accent: {
        400: '#f472b6',  // Pink
        500: '#ec4899',
      },
    },
  },
}
```

**Gradients:**
- Hero background: `bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900`
- Headline text: `bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent`
- Card backgrounds: `bg-gradient-to-br from-primary-600/10 to-accent-500/10`

**Rationale:**
- Tailwind defaults cover 80% of needs (spacing, typography, transitions)
- Custom colors provide brand identity
- No need for full design system (overkill for landing page)

**Alternatives considered:**
- **CSS variables**: More manual, less integration with Tailwind utilities
- **Fully custom theme**: Reinventing the wheel, slower development

### 8. Screenshot Placeholders: SVG vs. Image Service

**Decision:** Use gradient rectangles with text labels as placeholders.

**Rationale:**
- No external dependencies (placeholder.com can be slow)
- Responsive by default (SVG scales)
- Clear indication of what screenshot goes where
- Can be replaced with real images by updating `src` prop

**Implementation:**
```tsx
<div className="relative w-full aspect-[3/2] bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg flex items-center justify-center">
  <p className="text-white/60 text-sm">Hero Dashboard Preview (1200x800px)</p>
</div>
```

**Alternatives considered:**
- **placeholder.com**: External dependency, slower
- **Blank divs**: Less clear what goes where

## Risks / Trade-offs

**[Risk] Framer Motion bundle size (~60KB gzipped)**
→ Mitigation: Lazy load landing page route, only loads when user visits `/`

**[Risk] Route change breaks existing bookmarks to `/`**
→ Mitigation: `/` now shows better UX (landing); authenticated users auto-redirect to `/dashboard` via `ProtectedRoute`

**[Risk] Interactive demo with hardcoded data feels fake**
→ Mitigation: Use realistic MTG cards (Lightning Bolt, Black Lotus, etc.) with real prices; add disclaimer "Demo data"

**[Risk] Bento Grid cards look empty without real screenshots**
→ Mitigation: Gradient placeholders with clear labels; document exact screenshot requirements (size, content)

**[Risk] Landing page increases bundle size**
→ Mitigation: Use code splitting (`React.lazy`) for Landing page and Framer Motion

**[Trade-off] Landing page is not SSR (client-side only)**
→ Acceptable: No SEO requirement for MVP; can add Next.js later if needed

**[Trade-off] No real-time data in interactive demo**
→ Acceptable: Purpose is to show UX, not live data; hardcoded cards are sufficient

## Migration Plan

**Phase 1: Setup (no user impact)**
1. Install dependencies: `npm install framer-motion lucide-react react-countup`
2. Create `components/landing/` folder structure
3. Add custom colors to `tailwind.config.js`

**Phase 2: Build landing components (no user impact)**
1. Create `LandingNavbar` (with GitHub modal), `Hero`, `BentoGrid`, `BentoCard`, `InteractiveDemo`, `FinalCTA`
2. Create `Landing.tsx` page importing all components
3. Test in isolation (no routing changes yet)
4. Note: Footer removed from final implementation (MVP focus)

**Phase 3: Update routing (user-facing change)**
1. Update `App.tsx`:
   - Add `<Route path="/" element={<Landing />} />`
   - Change Dashboard route to `/dashboard`
   - Update navbar conditional rendering
2. Update `AuthContext`:
   - Change login redirect from `/` to `/dashboard`
   - Update `ProtectedRoute` to redirect unauthenticated users from `/dashboard` to `/login`
3. Update all internal links:
   - Navbar logo link: `/` → `/dashboard` (when authenticated)
   - Sidebar links: relative paths work as-is

**Phase 4: Simplify login page (optional, can be separate change)**
1. Remove marketing content from `Login.tsx`
2. Keep only form and error handling

**Rollback strategy:**
- If landing page breaks: revert `App.tsx` routes (5 minute fix)
- If auth flow breaks: revert `AuthContext` changes
- All changes are frontend-only, no database migrations

**Testing checklist:**
- [x] Unauthenticated user visits `/` → sees landing page
- [x] User clicks "Sign in" → redirects to Google OAuth
- [x] User logs in → redirects to `/dashboard`
- [x] Authenticated user visits `/` → can see landing page with "Go to Dashboard" button
- [x] Dashboard links work at `/dashboard` route
- [x] Interactive demo search and filters work
- [x] GitHub "Source Code" link opens in modal (not new tab)
- [x] Demo section clearly labeled as "Collection Library" preview
- [x] Mobile responsive (test Bento Grid collapse to 1 column)
- [x] All buttons consolidated to single CTA per section

## Decisions Made (Closed Questions)

**Q: Should authenticated users see landing page at `/` or auto-redirect to `/dashboard`?**
- **Decision**: Show landing page to authenticated users (Option B)
- **Rationale**: Allows authenticated users to revisit landing and share with others; simpler implementation than redirect
- **Implementation**: Shows "Go to Dashboard" button in navbar when authenticated

**Q: What screenshot sizes and content for Bento Grid cards?**
- **Decision**: Use gradient placeholders with clear labels (MVP approach)
- **Sizes**: 1200x800 (hero), 600x500 (collection, deck-builder), 600x400 (ai-insights), 500x400 (realtime), 600x400 (pricing analytics)
- **Labels**: Cards show placeholder text indicating screenshot dimensions and content
- **Future**: Real screenshots can be replaced without code changes

**Q: Should landing page have dark mode toggle?**
- **Decision**: Dark theme only (no toggle)
- **Rationale**: Matches dashboard aesthetic, simplifies MVP, single cohesive brand experience

**Q: Footer necessary for MVP?**
- **Decision**: No footer for MVP (removed from final implementation)
- **Rationale**: Not essential for conversion, reduces complexity, can be added in future phase

**Q: How many CTA buttons per section?**
- **Decision**: Maximum one primary CTA per section
- **Rationale**: Reduces decision fatigue, clearer user intent, improved conversion
- **Layout**: Hero (Sign in + Try Demo), Demo (no CTA), Final CTA (Sign in Free)
