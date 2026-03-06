## 1. Shared utilities

- [x] 1.1 Create `frontend/src/components/backgrounds/` directory and shared WUBRG color constants (dark/light variants) plus a `useReducedMotion` hook

## 2. AetherParticles component

- [x] 2.1 Create `AetherParticles.tsx` — canvas-based floating particles in WUBRG colors with 30 FPS cap, theme-aware opacity, and reduced-motion static fallback
- [x] 2.2 Wire AetherParticles into `App.tsx` — render as fixed z-0 layer on app pages (not landing, not login)

## 3. CardMatrix component

- [x] 3.1 Create `CardMatrix.tsx` — canvas-based falling mana symbols ({W}, {U}, {B}, {R}, {G}, {T}, {X}) in columns, WUBRG-colored, 30 FPS cap, theme-aware, reduced-motion fallback
- [x] 3.2 Wire CardMatrix into `Landing.tsx` — render as fixed z-0 layer behind all landing sections

## 4. Integration and polish

- [x] 4.1 Ensure page content renders above backgrounds (z-index, relative positioning on content containers)
- [x] 4.2 Test both themes (toggle light/dark) and verify opacity adjustments look good
- [x] 4.3 Verify canvas resizes correctly on window resize (debounced)
