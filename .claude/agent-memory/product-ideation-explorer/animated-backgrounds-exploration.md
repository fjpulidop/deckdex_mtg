# Animated Backgrounds Performance Exploration (2026-03-07)

## Current State
- Two canvas-based components: AetherParticles (app pages) and CardMatrix (landing page)
- Shared constants (MANA_COLORS, MANA_SYMBOLS) and useReducedMotion hook
- Spec exists: openspec/specs/animated-backgrounds/spec.md
- No archived changes found

## What's Working Well
- FPS capped at 30 via timestamp check in rAF loop
- DPR-aware canvas sizing (handles Retina)
- Debounced resize (200ms)
- Reduced motion support (static frame + listener for dynamic changes)
- pointer-events: none + aria-hidden on canvas
- Proper cleanup (cancelAnimationFrame + removeEventListener + clearTimeout)
- Particles/drops stored in refs (no React re-renders for animation state)
- useCallback for draw/update functions

## Gaps Found

### CRITICAL: No Page Visibility API pause
- Animation loops run continuously even when tab is hidden/background
- rAF IS throttled by browsers in background tabs, but still fires (1fps in Chrome)
- Wastes CPU/battery; particularly bad on mobile or laptop

### MAJOR: Theme change remounts entire canvas
- draw/update depend on isDark/opacityMax via useCallback deps
- When theme toggles, useEffect re-runs (deps include draw, update)
- This calls cancelAnimationFrame, re-creates animation loop
- Particles are preserved (ref check: length === 0), but there's a visual flash

### MODERATE: No offscreen culling awareness
- AetherParticles: 50 particles always updated even if out of viewport
- CardMatrix: 30-50 drops always updated
- For these small counts this is fine, but no architecture for scaling

### MODERATE: CardMatrix shadow rendering is expensive
- Dark mode: ctx.shadowBlur = 8 causes expensive Gaussian blur per symbol
- Applied on every frame for every drop (~30-50 draws with shadow per frame)
- shadowBlur is one of the most expensive Canvas 2D operations

### MINOR: No DPR change detection
- devicePixelRatio is read once on mount/resize
- If user drags window between displays with different DPR, canvas won't adapt
- Edge case but causes blurry rendering on multi-monitor setups

### MINOR: symbolToColorKey uses Math.random for colorless
- Called on every drop reset, produces non-deterministic color assignment
- Minor: could seed from symbol index for consistency

### MINOR: AetherParticles glow uses redundant arc draws
- Dark mode draws each particle twice (main + 3x radius glow)
- Doubling draw calls; could use radialGradient or shadowBlur instead
- But shadowBlur is also expensive (see CardMatrix issue)

### SPEC GAP: No explicit "user toggle" for backgrounds
- Spec doesn't mention ability to disable backgrounds entirely
- Some users may find them distracting regardless of reduced-motion setting
- Settings page could add a toggle

## Performance Profile Summary
- AetherParticles: 50 particles x 2 draws (dark) = 100 arc calls per frame at 30fps
- CardMatrix: ~40 drops x 2 draws (dark, with shadowBlur) = 80 text draws per frame at 30fps
- Both are lightweight by canvas standards; shadowBlur is the main bottleneck
