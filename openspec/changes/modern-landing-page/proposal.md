## Why

DeckDex MTG currently sends unauthenticated users directly to a login page with no information about the product's features or value proposition. This is a major conversion blocker - potential users cannot see what the app does before committing to sign up. A modern, vibrant landing page showcasing Collection Management, Deck Builder, and AI Insights will increase signups and communicate the product's unique value before authentication.

## What Changes

- New public landing page at `/` route with modern, Stripe-inspired design (vibrant gradients, glows, animations)
- Hero section with gradient text, dual CTAs (Get Started + Watch Demo), and large dashboard preview placeholder
- Bento Grid layout showcasing 3-4 key features with visual previews (Collection Management, Deck Builder, AI Insights, Real-time Progress)
- Interactive demo component allowing users to search and filter sample MTG cards without signup
- Navbar with login/signup buttons positioned top-right (replacing centered login)
- Final CTA section and professional footer
- Move current authenticated dashboard from `/` to `/dashboard` route
- Simplify login page to minimal form (remove marketing content)
- Add Framer Motion for smooth animations, Lucide React for icons, and react-countup for stats

## Capabilities

### New Capabilities

- `landing-page`: Public homepage showcasing product features, interactive demo, and conversion-focused design with modern UI patterns (Bento Grid, gradients, animations). No authentication required.
- `interactive-demo`: Embedded mini-dashboard with live search and filtering on hardcoded sample MTG cards, allowing prospective users to try the core experience without signup.

### Modified Capabilities

- `navigation-ui`: Change root route `/` from authenticated dashboard to public landing page; move dashboard to `/dashboard`; update navbar to include landing-specific variant with top-right login/signup buttons.

## Impact

- **Frontend**: New `pages/Landing.tsx` and `components/landing/` folder (Hero, BentoGrid, InteractiveDemo, Footer); route changes in `App.tsx`; updated `Navbar` component with landing variant; new dependencies (framer-motion, lucide-react, react-countup)
- **Auth flow**: Login redirect changes from `/` to `/dashboard`
- **UX**: Improved conversion funnel - users see product value before committing to signup
- **Assets**: Requires 4-5 screenshot placeholders (1200x800 hero, 600x500 features) with specific instructions for content capture
- **No backend changes**: Landing page is entirely client-side; uses hardcoded demo data
