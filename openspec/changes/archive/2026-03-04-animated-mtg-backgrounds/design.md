## Context

The app currently uses flat solid backgrounds (gray-100/gray-900 for dashboard, static slate/purple gradient for landing). We want to add animated, MTG-themed backgrounds to give the app personality. Two distinct components: "Card Matrix" (mana symbols rain) for the landing, and "Aether Particles" (floating mana-colored dots) for all authenticated pages.

Currently `App.tsx` renders navbars and routes. Landing.tsx is a simple wrapper with a gradient div. Dashboard and other pages each set their own `bg-*` classes.

## Goals / Non-Goals

**Goals:**
- Two reusable background components: `CardMatrix` and `AetherParticles`
- Visually themed around MTG's 5 mana colors (WUBRG)
- Respect light/dark theme and `prefers-reduced-motion`
- Lightweight — no jank, no dependencies

**Non-Goals:**
- No 3D, WebGL, or heavy GPU work
- No user-configurable animation settings
- No changes to existing color palette or theme system
- No backend changes

## Decisions

### D1: Canvas-based rendering (not CSS/DOM animations)

**Choice**: HTML5 Canvas for both components.

**Why**: Animating dozens of independent elements via DOM/CSS creates layout thrash and hurts performance. Canvas runs outside the DOM layout pipeline — one `<canvas>` element, no reflows, requestAnimationFrame loop. This is the standard approach for particle systems in React apps.

**Alternatives considered**:
- CSS animations with absolute-positioned divs: simpler for <10 elements, but we need 30-80 particles/symbols — too many DOM nodes.
- SVG animations: good for path-based effects but overkill for particles, and SVG DOM still causes reflow.

### D2: Component placement — fixed viewport layer in App.tsx

**Choice**: Render background components as fixed, full-viewport layers in `AppContent` (App.tsx), positioned behind all content with `z-index: 0` and `pointer-events: none`.

```
┌─ AppContent ───────────────────────────┐
│  <AetherParticles />    ← z-0, fixed   │  (app pages only)
│  <CardMatrix />         ← z-0, fixed   │  (landing only)
│  ┌─ Navbar ──────────────────────┐     │
│  │  ...                          │     │  ← z-10+
│  └───────────────────────────────┘     │
│  ┌─ Page content ────────────────┐     │
│  │  ...                          │     │  ← z-auto (above 0)
│  └───────────────────────────────┘     │
│  <JobsBottomBar />                     │
└────────────────────────────────────────┘
```

**Why**: Centralizes the background layer. Each page doesn't need to know about it. Conditional rendering based on route (landing vs app pages) keeps it simple.

**Alternatives considered**:
- Per-page background: each page imports its own background. Scattered, duplicated logic.
- CSS background on body: can't use canvas.

### D3: Theme awareness via `useTheme()` hook

**Choice**: Each background component reads `useTheme()` to adjust particle colors/opacity.

- **Dark mode**: Brighter particles, glow effect (higher opacity ~0.15-0.4)
- **Light mode**: Muted, desaturated variants (lower opacity ~0.05-0.15)

### D4: WUBRG color palette

Canonical MTG mana colors used for particles/symbols:

| Mana | Dark mode          | Light mode          |
|------|--------------------|---------------------|
| W    | `#FFFBD5` (warm)   | `#B8860B` (gold)    |
| U    | `#0E68AB` (blue)   | `#0A4F8A` (deep)    |
| B    | `#A070B0` (purple) | `#5C3D6E` (deep)    |
| R    | `#D3202A` (red)    | `#A01820` (deep)    |
| G    | `#00733E` (green)  | `#005A2E` (deep)    |

### D5: Animation parameters

| Param              | AetherParticles     | CardMatrix           |
|--------------------|---------------------|----------------------|
| Element count      | 40-60               | 8-12 columns         |
| Speed              | 0.2-0.5 px/frame    | 0.3-0.8 px/frame     |
| Element size       | 2-5px radius dots   | 14-18px font symbols |
| Opacity range      | 0.05-0.3            | 0.03-0.2             |
| FPS cap            | 30                  | 30                   |
| Canvas resize      | On window resize (debounced) | Same        |

### D6: Reduced motion support

**Choice**: When `prefers-reduced-motion: reduce` is active, render a single static frame (particles in random positions, no animation loop). This gives the visual flavor without motion.

## Risks / Trade-offs

- **[Performance on low-end devices]** → 30 FPS cap + low particle count. Canvas is already GPU-friendly. If issues arise, particle count can be reduced further.
- **[Readability over animated background]** → Very low opacity + blur on particles. Content always sits above via z-index. Dark mode opacities are the maximum (0.3), light mode even lower.
- **[Canvas resize jank]** → Debounce resize handler (200ms). Only recreate canvas dimensions, particles persist.
- **[Landing page already has gradients]** → CardMatrix renders on top of existing gradient. The gradient provides the base atmosphere, the matrix adds motion on top.
