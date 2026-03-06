## Why

The app's backgrounds are flat solid colors (gray-100 / gray-900) in the dashboard and a static gradient on the landing page. For an MTG collection manager, this misses an opportunity to reinforce the magical theme. Adding subtle programmatic animations themed around the five mana colors (WUBRG) gives the app personality and a premium feel without sacrificing usability.

## What Changes

- **Landing page**: Add a "Card Matrix" animated background — mana symbols ({W}, {U}, {B}, {R}, {G}, {T}, {X}…) slowly falling like a subtle Matrix rain, colored per mana type. Low opacity, behind all content.
- **Dashboard / app pages**: Add an "Aether Particles" animated background — small glowing dots in WUBRG colors drifting slowly across the viewport. Very subtle, non-distracting.
- Both backgrounds respect light/dark theme (opacity and brightness adjust).
- Both use `prefers-reduced-motion` to disable animation for accessibility.
- Backgrounds render behind all page content via a fixed, full-viewport layer with `pointer-events: none`.

## Non-goals

- No WebGL or heavy GPU usage — keep it lightweight (CSS animations or 2D canvas).
- No user-configurable background settings (speed, density, etc.).
- No changes to the color palette, component styling, or theme toggle behavior.

## Capabilities

### New Capabilities
- `animated-backgrounds`: Reusable animated background components (AetherParticles, CardMatrix) themed around MTG mana colors, with light/dark and reduced-motion support.

### Modified Capabilities
- `landing-page`: Landing page sections render on top of the CardMatrix animated background instead of relying solely on static gradients.
- `web-dashboard-ui`: Dashboard and app pages render on top of the AetherParticles animated background.

## Impact

- **Frontend only** — no backend changes.
- New components: `frontend/src/components/backgrounds/AetherParticles.tsx`, `CardMatrix.tsx`.
- Modified: Landing.tsx (add CardMatrix layer), Dashboard.tsx / App layout (add AetherParticles layer).
- Performance: canvas or CSS-only, throttled to ≤30 FPS, minimal DOM nodes.
- Dependencies: none (pure React + canvas/CSS).
