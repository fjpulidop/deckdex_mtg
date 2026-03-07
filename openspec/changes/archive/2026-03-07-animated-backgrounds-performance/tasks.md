## 1. AetherParticles — Theme Ref Stability

- [x] 1.1 Add `isDarkRef` and `opacityMaxRef` as `useRef<boolean>` / `useRef<number>` in `AetherParticles`. Add a dedicated `useEffect` that syncs `isDark` and `opacityMax` into these refs whenever `theme` changes. File: `frontend/src/components/backgrounds/AetherParticles.tsx`. Done when: refs are declared and the sync effect runs whenever theme toggles (verified by reading `isDarkRef.current` in a console.log before removing it).

- [x] 1.2 Rewrite `AetherParticles.draw` to read `isDarkRef.current` and `opacityMaxRef.current` instead of the captured `isDark` / `opacityMax` variables. Remove `isDark` and `opacityMax` from the `draw` `useCallback` dependency array. Add a targeted `// eslint-disable-next-line react-hooks/exhaustive-deps` comment with explanation, consistent with the existing `react-hooks/immutability` pattern in the file. Done when: `draw` has no `isDark` or `opacityMax` in its dep array and `npm run lint` passes.

- [x] 1.3 Rewrite `AetherParticles.update` to read `opacityMaxRef.current` instead of the captured `opacityMax` variable. Remove `opacityMax` from the `update` `useCallback` dependency array. Done when: `update` dep array is empty and lint passes.

- [x] 1.4 Remove `draw` and `update` from the animation `useEffect` dependency array in `AetherParticles` (they are now stable refs-reading callbacks). The dep array should contain only `[reducedMotion, initParticles]`. Done when: `useEffect` dep array is `[reducedMotion, initParticles]` and theme toggle in the browser produces no canvas blank frame.

## 2. AetherParticles — Page Visibility Pause

- [x] 2.1 Add a `pausedRef = useRef(false)` to `AetherParticles`. At the top of the animation `useEffect`, before calling `requestAnimationFrame`, check `document.hidden`: if hidden, set `pausedRef.current = true` and skip starting the loop. File: `frontend/src/components/backgrounds/AetherParticles.tsx`. Done when: component mounting while tab is hidden does not start an rAF loop.

- [x] 2.2 Add a `visibilitychange` event listener on `document` inside the animation `useEffect`. On `hidden=true`: set `pausedRef.current = true` and call `cancelAnimationFrame(animFrameRef.current)`. On `hidden=false`: set `pausedRef.current = false` and call `animFrameRef.current = requestAnimationFrame(animate)`. Add `document.removeEventListener('visibilitychange', handleVisibility)` to the cleanup return. Done when: switching tabs stops the loop (verified via Performance DevTools showing no rAF calls) and returning to the tab resumes it with no visual discontinuity.

## 3. CardMatrix — Theme Ref Stability

- [x] 3.1 Add `isDarkRef` and `opacityMaxRef` refs to `CardMatrix`. Add the same theme-sync `useEffect` from task 1.1. File: `frontend/src/components/backgrounds/CardMatrix.tsx`. Done when: refs are declared and sync effect is in place.

- [x] 3.2 Rewrite `CardMatrix.draw` to read `isDarkRef.current` and `opacityMaxRef.current` instead of captured variables. Remove `isDark` and `opacityMax` from the `draw` dep array with a lint-disable comment. Done when: `draw` dep array has no theme-derived values and lint passes.

- [x] 3.3 Remove `draw` from the animation `useEffect` dependency array in `CardMatrix`. The dep array should contain only `[reducedMotion, initDrops]`. Done when: theme toggle produces no canvas blank frame in `CardMatrix` and lint passes.

## 4. CardMatrix — Off-Screen Glow Cache

- [x] 4.1 Add a `glowCacheRef = useRef<Map<string, HTMLCanvasElement>>(new Map())` to `CardMatrix`. File: `frontend/src/components/backgrounds/CardMatrix.tsx`. Done when: ref is declared and `glowCacheRef.current` is accessible in `draw`.

- [x] 4.2 Extend the theme-sync `useEffect` (task 3.1) to also call `glowCacheRef.current.clear()` when `isDark` or `opacityMax` changes. Done when: switching themes clears the cache (can add temporary `console.log('cache cleared')` to verify, then remove).

- [x] 4.3 Write a helper function `getGlowCanvas(cache: Map<string, HTMLCanvasElement>, hex: string, fontSize: number, symbol: string): HTMLCanvasElement` inside `CardMatrix.tsx` (module-level pure function, not a hook). The function: checks the cache for key `"${hex}:${fontSize}"`; on miss, creates an off-screen canvas of size `fontSize * 4` × `fontSize * 4`, draws the symbol at center with `ctx.shadowBlur = 8`, `ctx.shadowColor = hex`, `ctx.fillStyle = hex`, `ctx.globalAlpha = 1`, stores it in the cache, and returns it. On hit, returns the cached canvas directly. Done when: calling `getGlowCanvas` twice with the same key returns the same canvas object (referential equality).

- [x] 4.4 Replace the `shadowBlur` glow pass in `CardMatrix.draw` with a `drawImage` call. Remove the `ctx.shadowBlur = 8` / `ctx.shadowColor = hex` / `ctx.shadowBlur = 0` lines. Instead: call `getGlowCanvas(glowCacheRef.current, hex, d.fontSize, d.symbol)`, set `ctx.globalAlpha = alpha * 0.4`, and call `ctx.drawImage(glowCanvas, d.x - glowCanvas.width / 2, d.y - glowCanvas.height / 2)`. Done when: dark mode glow is visually present, no `shadowBlur` assignments appear on the main canvas context, and the approach is confirmed in DevTools (no blur filter in the rendering pipeline).

## 5. CardMatrix — Page Visibility Pause

- [x] 5.1 Add `pausedRef = useRef(false)` and a `visibilitychange` listener to `CardMatrix` using the same pattern as tasks 2.1 and 2.2. File: `frontend/src/components/backgrounds/CardMatrix.tsx`. Done when: switching tabs stops the `CardMatrix` loop and returning resumes it with drop positions continuous.

## 6. Verification

- [x] 6.1 Run `npm run lint` from `frontend/` and confirm zero new lint errors. Pay particular attention to `react-hooks/exhaustive-deps` warnings — each should either be resolved or covered by a targeted inline disable with a comment. Done when: `npm run lint` exits with code 0.

- [x] 6.2 Run `npm run build` from `frontend/` and confirm the build completes without TypeScript errors. Done when: build exits with code 0 and no type errors are reported.

- [x] 6.3 Manual smoke test — dark mode: open the landing page, observe `CardMatrix` glow renders correctly; toggle to dark mode on the dashboard, confirm no blank frame on `AetherParticles`; switch browser tabs and confirm animation pauses (CPU usage drops) then resumes on return. Done when: all three observations pass.

- [x] 6.4 Manual smoke test — light mode: toggle to light mode on the dashboard, confirm no blank frame and no glow artifact in `AetherParticles`; confirm `CardMatrix` on the landing page shows no glow in light mode. Done when: both observations pass.
