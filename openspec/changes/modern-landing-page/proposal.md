## Why

DeckDex MTG currently sends unauthenticated users directly to a login page with no information about the product's features or value proposition. This is a major conversion blocker - potential users cannot see what the app does before committing to sign up. A modern, vibrant landing page showcasing Collection Management, Deck Builder, and AI Insights will increase signups and communicate the product's unique value before authentication.

## What Changes

- New public landing page at `/` route with modern, vibrant design (dark theme with purple/pink gradients, glows, animations)
- Hero section with gradient text, open source badge, dual CTAs ("Sign in" primary + "Try Demo" secondary), and large dashboard preview placeholder
- Bento Grid layout showcasing 5 key features with visual previews (Collection Management, Deck Builder, AI Insights, Real-time Updates, Price Tracking)
- Interactive Collection Library demo component allowing users to search and filter sample MTG cards without signup
- Landing navbar with: Logo (left) | Features (center) | Source Code (right, opens GitHub in modal)
- Final CTA section with conversion messaging
- GitHub modal for accessing source code without leaving the landing page
- Move current authenticated dashboard from `/` to `/dashboard` route
- Simplify login page to minimal form (remove marketing content)
- Add Framer Motion for smooth animations, Lucide React for icons
- Emphasize 100% open source and community-driven positioning throughout

## Capabilities

### New Capabilities

- `landing-page`: Public homepage showcasing product features, interactive demo, and conversion-focused design with modern UI patterns (Bento Grid, gradients, animations). No authentication required.
- `interactive-demo`: Embedded mini-dashboard with live search and filtering on hardcoded sample MTG cards, allowing prospective users to try the core experience without signup.

### Modified Capabilities

- `navigation-ui`: Change root route `/` from authenticated dashboard to public landing page; move dashboard to `/dashboard`; update landing navbar with Features link, GitHub source code link, and conditional sign in button (only for unauthenticated users); add GitHub modal instead of external link.

## Impact

- **Frontend**: New `pages/Landing.tsx` and `components/landing/` folder (LandingNavbar, Hero, BentoGrid, BentoCard, InteractiveDemo, FinalCTA); route changes in `App.tsx`; updated `Navbar` component for dashboard; added path aliases (@/) in vite.config.ts and tsconfig; new dependencies (framer-motion, lucide-react)
- **Auth flow**: Login redirect changes from `/` to `/dashboard`; unauthenticated users see landing at `/`, authenticated users can access both landing and dashboard
- **UX**: 
  - Improved conversion funnel - users see product value before committing to signup
  - Clear positioning as open source and community-driven project
  - GitHub access via modal maintains user engagement without leaving page
  - Demo section clearly labeled as "Collection Library" with messaging about additional features
- **Assets**: Gradient placeholders with labels for Bento cards (1200x800 hero, 600x500 features, 600x400 features, 500x400 features)
- **No backend changes**: Landing page is entirely client-side; uses hardcoded demo data with 15 realistic MTG cards
