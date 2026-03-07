## Why

The two animated canvas backgrounds (`AetherParticles` and `CardMatrix`) contain three concrete performance and correctness defects that waste CPU/battery and cause visible rendering artifacts:

1. **No Page Visibility API pause.** Both animation loops call `requestAnimationFrame` unconditionally. When the user switches to another tab, the loops continue running at 30 FPS burning CPU and battery for no visible benefit.

2. **`shadowBlur` on every draw call (CardMatrix).** In dark mode, `CardMatrix` draws up to 40 drops per frame, each triggering a full Gaussian blur by setting `ctx.shadowBlur = 8` before `fillText`. At 30 FPS this is ~1,200 blur operations per second. Shadow blur is the single most expensive 2D canvas operation and it forces GPU compositing on every frame.

3. **Theme-change flash (both components).** `draw` and `update` are `useCallback` hooks that declare `isDark` and `opacityMax` as dependencies. When the user toggles the theme, React recreates these callbacks, which triggers the `useEffect` cleanup (cancels the running `rAF` loop) and re-runs the effect (starts a new loop). During that React microtask gap the canvas is blank, causing a visible flash.

These are not cosmetic issues: battery drain and frame drops affect all users; the theme flash affects every theme toggle. This change addresses all three with minimal scope.

## What Changes

- Both components gain a `visibilitychange` event listener. When `document.hidden` becomes `true`, `cancelAnimationFrame` stops the loop; when the document becomes visible again, the loop restarts from the current state.
- `CardMatrix.draw` replaces `ctx.shadowBlur` with a second `drawImage` pass onto an off-screen canvas that is pre-rendered once per color per font size. The pre-rendered glow cache is keyed by `colorKey` and invalidated only when the color set changes (i.e., never at runtime).
- Both components move `isDark` and `opacityMax` into `useRef` values that are kept in sync with the current theme via a dedicated `useEffect`. The animation callbacks (`draw`, `update`) are removed from the `useEffect` dependency array; instead they read directly from refs. This eliminates the callback recreation cycle on theme change.

## Capabilities

### Modified Capabilities
- `animated-backgrounds`: Adds three new performance requirements: tab-hidden pause, shadow-blur elimination, and theme-ref stability.

## Impact

- `frontend/src/components/backgrounds/AetherParticles.tsx`: Page Visibility pause, theme via refs.
- `frontend/src/components/backgrounds/CardMatrix.tsx`: Page Visibility pause, glow cache, theme via refs.
- `openspec/specs/animated-backgrounds/spec.md`: Three new performance requirement scenarios.

## Non-goals

- No changes to particle count, FPS cap, color palette, or animation behavior.
- No changes to reduced-motion handling (already correct).
- No changes to `constants.ts` or `useReducedMotion.ts`.
- No backend, API, or data-model changes.
- No new components, hooks, or context files.
