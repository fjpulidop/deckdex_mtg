## Context

Both animated background components (`AetherParticles` and `CardMatrix`) live in `frontend/src/components/backgrounds/`. They are canvas-based React components that:

- Cap animation at 30 FPS via a `lastFrameRef` timestamp guard
- Are DPR-aware (HiDPI canvas scaling via `ctx.setTransform`)
- Debounce viewport resize (200 ms)
- Respect `prefers-reduced-motion` via the shared `useReducedMotion` hook
- Use `useTheme()` from `ThemeContext` to adapt colors/opacity to dark/light mode

Three defects were identified in the current implementation. See `proposal.md` for motivation. This design document describes how to fix each defect.

## Goals / Non-Goals

**Goals:**

- Pause animation loops when the browser tab is hidden (Page Visibility API)
- Eliminate `ctx.shadowBlur` in `CardMatrix` by pre-rendering glow onto an off-screen canvas
- Prevent theme-toggle flash in both components by decoupling animation callbacks from React's render cycle via refs

**Non-Goals:**

- No changes to FPS cap, particle/drop counts, or animation aesthetics
- No changes to `constants.ts`, `useReducedMotion.ts`, or any other file
- No new custom hooks, contexts, or shared utilities
- No backend changes of any kind

## Decisions

### Decision 1: Page Visibility — listener inside the animation `useEffect`, not a separate effect

**Chosen approach:** Add a `visibilitychange` listener directly inside the same `useEffect` that owns the `requestAnimationFrame` loop. When `document.hidden` becomes `true`, call `cancelAnimationFrame` and store a `paused` flag in a `useRef`. When the document becomes visible again, clear the flag and re-invoke `requestAnimationFrame(animate)` to restart the loop.

**Alternative considered:** A separate `useEffect` that reads a `pausedRef` and calls `cancelAnimationFrame` / restarts the loop. Rejected because it requires coordinating two effects with shared mutable refs, and the ownership of the rAF handle becomes ambiguous.

**Why this approach:** Keeps all animation lifecycle management (start, tick, pause, resume, stop, resize) in a single `useEffect` that has a single cleanup function. Consistent with the existing pattern in both components.

**Implementation note:** The paused state uses a `useRef<boolean>` (not `useState`) so writes from the visibility handler do not trigger re-renders.

```
// Pseudocode pattern
const pausedRef = useRef(false);

const handleVisibility = () => {
  if (document.hidden) {
    pausedRef.current = true;
    cancelAnimationFrame(animFrameRef.current);
  } else {
    pausedRef.current = false;
    animFrameRef.current = requestAnimationFrame(animate);
  }
};
document.addEventListener('visibilitychange', handleVisibility);
// cleanup: document.removeEventListener('visibilitychange', handleVisibility)
```

### Decision 2: Glow rendering in CardMatrix — off-screen canvas cache keyed by `colorHex + fontSize`

**Chosen approach:** Before the main draw loop, build (or reuse) a `Map<string, HTMLCanvasElement>` stored in a `useRef`. The cache key is `"${hex}:${fontSize}"`. Each cached canvas is sized to `(fontSize * 4) x (fontSize * 4)` — large enough to hold the blurred text plus blur radius spread — and is pre-drawn once: render the symbol at center with `shadowBlur=8`, `shadowColor=hex`. In the main draw loop, instead of calling `ctx.shadowBlur = 8` and `fillText`, call `ctx.drawImage(cachedCanvas, x - half, y - half)`.

**Cache invalidation:** The theme change causes `isDark` to flip, which changes the hex values looked up via `MANA_COLORS`. The existing entries become stale. Since the cache is a `useRef`, it survives re-renders; we explicitly clear it inside the theme-sync `useEffect` (Decision 3 below) when `isDark` changes.

**Alternative considered:** Using `ctx.filter: blur()` CSS filter instead of `shadowBlur`. Rejected because CSS filters apply to the entire canvas context state, requiring save/restore on every glyph, and browser support for `CanvasRenderingContext2D.filter` is less consistent than `shadowBlur` on off-screen canvases.

**Alternative considered:** Simply removing the glow pass entirely. Rejected — the glow is a visible design feature that users will notice its absence. The goal is performance parity, not visual regression.

**Why this approach:** Off-screen canvas drawing with `drawImage` is the canonical browser technique for caching expensive canvas operations. The cache population cost is O(unique color×fontSize combinations) which at runtime is at most 5 colors × ~3 fontSize buckets = 15 entries, each drawn once.

**Implementation note:** The off-screen canvas draws the symbol at `(halfW, halfH)` with the blur context state active. The `ctx.globalAlpha` for the glow pass is applied on the main canvas via `ctx.globalAlpha = alpha * 0.4` before `drawImage`, identical to current behavior.

### Decision 3: Theme-ref stability — sync `isDark`/`opacityMax` into refs, remove from useCallback deps

**Chosen approach:** Add a single dedicated `useEffect` that runs whenever `theme` changes:

```typescript
const isDarkRef = useRef(isDark);
const opacityMaxRef = useRef(opacityMax);

useEffect(() => {
  isDarkRef.current = isDark;
  opacityMaxRef.current = opacityMax;
}, [isDark, opacityMax]);
```

Then rewrite `draw` and `update` as stable `useCallback` functions with no dependency on `isDark` or `opacityMax` — they read from the refs instead. The animation `useEffect` dependency array shrinks to `[reducedMotion, initParticles]` (or `[reducedMotion, initDrops]`), so it never re-runs on theme change.

**Alternative considered:** Keeping `draw`/`update` as non-memoized inline functions inside the animation `useEffect`. Rejected because it would require moving the entire animation setup inline, reducing readability and making future changes harder.

**Alternative considered:** Using a single `settingsRef` object holding `{ isDark, opacityMax }`. Acceptable but adds unnecessary object allocation. Two separate refs map directly to two separate variables already in the code.

**Why this approach:** It is the minimal-change path. The `draw` and `update` `useCallback` hooks keep their existing structure and ESLint `react-hooks/exhaustive-deps` satisfaction — we just swap `isDark` reads for `isDarkRef.current` reads inside them, then remove `isDark`/`opacityMax` from their dependency arrays. No animation loop is ever restarted on theme change.

**ESLint note:** `isDarkRef.current` inside `useCallback` with an empty dep array would trigger `react-hooks/exhaustive-deps`. Use `// eslint-disable-next-line react-hooks/exhaustive-deps` with an explanatory comment, consistent with the existing `/* eslint-disable react-hooks/immutability */` pattern already in both files.

### Decision 4: Glow cache clearing on theme change

The glow cache ref in `CardMatrix` must be cleared when the theme changes (dark → light switches hex values). This is done inside the same theme-sync `useEffect` from Decision 3:

```typescript
useEffect(() => {
  isDarkRef.current = isDark;
  opacityMaxRef.current = opacityMax;
  glowCacheRef.current.clear();  // invalidate stale cached canvases
}, [isDark, opacityMax]);
```

The cache is lazily repopulated on the next draw frame — no perceptible delay because each cache entry is trivially cheap to render once.

## Risks / Trade-offs

**[Risk] Off-screen canvas creation during first draw in dark mode** → Each of the ~40 drops may initially have a distinct `fontSize`. On the very first dark-mode frame after cache invalidation, up to 15 cache misses could each create an `HTMLCanvasElement`. This is negligible (canvas creation is ~0.1 ms each) and happens only once per theme toggle, not per frame.

**[Risk] `visibilitychange` fires before the animation `useEffect` has run** (i.e., component mounts but effect deferred) → The listener is added inside the effect, so if the document is already hidden at mount time, the listener is not yet registered. Mitigation: at the top of the animation effect, check `document.hidden` before calling `requestAnimationFrame` and set `pausedRef.current = true` immediately if hidden.

**[Risk] ESLint `exhaustive-deps` lint warnings on the callbacks that read from refs** → Addressed by targeted inline disable comments, same as the existing `react-hooks/immutability` disables already present in both files.

**[Trade-off] Glow cache for `AetherParticles`** → `AetherParticles` uses `ctx.arc` (not `fillText`) for its glow pass, which does NOT use `shadowBlur`. Its glow is a second `ctx.arc` at 3× radius with reduced opacity — this is already cheap. No off-screen cache is needed there.

## Migration Plan

This is a pure frontend refactor with no data model, API, or migration concerns. Deployment is:

1. Merge to the feature branch
2. `npm run build` (Vite) — static output only
3. No server restart, no DB migration, no feature flag required

Rollback: revert the two changed files. The animation behavior is functionally identical; only the internal execution path changes.

## Open Questions

None. All design decisions are resolved above.
