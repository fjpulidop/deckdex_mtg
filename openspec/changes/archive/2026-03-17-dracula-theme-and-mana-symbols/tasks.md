# Tasks: Dracula Theme and Mana Symbol Rendering on Landing

All tasks are `[frontend]`. No backend or core changes required.

---

## Task 1 — Add Dracula color tokens to Tailwind config [frontend]

**Description:** Extend `tailwind.config.js` with a `dracula` namespace containing all 10 Dracula palette colors as flat named tokens. These tokens must be live before any component edits, since Tailwind generates utility classes from this config at build time.

**Files:**
- `frontend/tailwind.config.js`

**Changes:**
Inside `theme.extend.colors`, add:
```js
dracula: {
  bg:      '#282a36',
  current: '#44475a',
  fg:      '#f8f8f2',
  comment: '#6272a4',
  purple:  '#bd93f9',
  pink:    '#ff79c6',
  cyan:    '#8be9fd',
  green:   '#50fa7b',
  orange:  '#ffb86c',
  yellow:  '#f1fa8c',
},
```

**Acceptance Criteria:**
- `npm run build` passes (Tailwind processes the new tokens without error)
- The keys `bg-dracula-bg`, `text-dracula-fg`, `border-dracula-current`, etc. are valid Tailwind utility classes (verified by build output or dev server CSS)
- No existing token (`primary`, `accent`) is removed or modified

**Dependencies:** None — this is the first task.

---

## Task 2 — Update `index.css` dark body background [frontend]

**Description:** Change the `.dark body` background color from `#111827` (Tailwind gray-900) to `#282a36` (Dracula bg) so the page chrome behind all sections matches the Dracula dark theme.

**Files:**
- `frontend/src/index.css`

**Changes:**
```css
/* Before */
.dark body {
  background-color: #111827;
}

/* After */
.dark body {
  background-color: #282a36;
}
```

**Acceptance Criteria:**
- In dark mode, the body background renders as `#282a36`
- Light mode (`body { background-color: #f3f4f6; }`) is untouched
- No other rules in `index.css` are modified

**Dependencies:** Task 1 (Dracula tokens available, though this change uses a literal hex value).

---

## Task 3 — Migrate `Hero.tsx` to Dracula palette [frontend]

**Description:** Replace all `slate-*` Tailwind classes in `Hero.tsx` with their Dracula equivalents per the mapping table in `design.md`. Preserve opacity modifiers (e.g., `/50`, `/20`) and all gradient directives.

**Files:**
- `frontend/src/components/landing/Hero.tsx`

**Key substitutions:**
- `bg-slate-900/20` → `bg-dracula-bg/20` (section background gradient stop)
- `bg-slate-900/60` → `bg-dracula-bg/60` (description card background)
- `border-slate-700/50` → `border-dracula-current/50`
- `border-slate-700/30` → `border-dracula-current/30`
- `border-slate-600` → `border-dracula-current`
- `text-slate-300` → `text-dracula-fg`
- `text-slate-400` → `text-dracula-comment`
- `from-purple-300 via-purple-400 to-pink-500` → `from-dracula-purple to-dracula-pink` (headline gradient)
- `from-accent-500/10 to-primary-500/10` badge — keep as-is (uses existing tokens)
- `hover:bg-slate-800/50 hover:border-slate-500` → `hover:bg-dracula-current/50 hover:border-dracula-current`
- `via-purple-900/10` → `via-dracula-purple/10`

**Acceptance Criteria:**
- No `slate-` class strings remain in this file
- The bilingual description card renders with Dracula background and border
- Hero section gradient background uses Dracula tokens
- Demo button hover states use Dracula colors
- `npm run build` passes

**Dependencies:** Task 1.

---

## Task 4 — Migrate `BentoGrid.tsx` to Dracula palette [frontend]

**Description:** Replace `slate-*` classes in `BentoGrid.tsx` and update the `gradientFrom`/`gradientTo`/`iconColor` prop values passed to `BentoCard` to use Dracula equivalents.

**Files:**
- `frontend/src/components/landing/BentoGrid.tsx`

**Key substitutions:**
- `bg-gradient-to-b from-slate-900/80 to-slate-950/80` (section) → `from-dracula-bg/80 to-dracula-bg/80`
- `text-slate-400` (subtitle) → `text-dracula-comment`
- `text-slate-500` (contribute text) → `text-dracula-comment`
- `from-purple-300 to-pink-400` (section title gradient) → `from-dracula-purple to-dracula-pink`
- BentoCard prop updates:
  - Collection: `from-blue-500/20 to-blue-600/20` → `from-dracula-cyan/20 to-dracula-cyan/20`, icon color `text-blue-400/60 group-hover:text-blue-300/80` → `text-dracula-cyan/60 group-hover:text-dracula-cyan/80`
  - Deck Builder: `from-purple-500/20 to-purple-600/20` → `from-dracula-purple/20 to-dracula-purple/20`, icon `text-purple-400/60 group-hover:text-purple-300/80` → `text-dracula-purple/60 group-hover:text-dracula-purple/80`
  - AI Insights: `from-pink-500/20 to-rose-600/20` → `from-dracula-pink/20 to-dracula-pink/20`, icon `text-pink-400/60 group-hover:text-pink-300/80` → `text-dracula-pink/60 group-hover:text-dracula-pink/80`
  - Real-time: `from-amber-500/20 to-orange-600/20` → `from-dracula-orange/20 to-dracula-orange/20`, icon `text-amber-400/60 group-hover:text-amber-300/80` → `text-dracula-orange/60 group-hover:text-dracula-orange/80`
  - Price Tracking: `from-green-500/20 to-emerald-600/20` → `from-dracula-green/20 to-dracula-green/20`, icon `text-green-400/60 group-hover:text-green-300/80` → `text-dracula-green/60 group-hover:text-dracula-green/80`

**Acceptance Criteria:**
- No `slate-` class strings remain in this file
- All five `BentoCard` instances use Dracula gradient and icon color tokens
- Section background gradient uses `dracula-bg`
- `npm run build` passes

**Dependencies:** Task 1.

---

## Task 5 — Migrate `BentoCard.tsx` to Dracula palette [frontend]

**Description:** Replace `slate-*` classes in the `BentoCard` component's own structural classes. This is the container/border/hover layer — the gradient fill and icon color come from props (already updated in Task 4).

**Files:**
- `frontend/src/components/landing/BentoCard.tsx`

**Key substitutions:**
- `border-slate-700/50` → `border-dracula-current/50` (card border)
- `bg-slate-900/50` → `bg-dracula-bg/50` (card background)
- `hover:border-slate-600` → `hover:border-dracula-current` (hover border)
- `border-slate-600/30` → `border-dracula-current/30` (illustration box border)
- `from-purple-500/20 via-transparent to-pink-500/20` (hover glow) → `from-dracula-purple/20 via-transparent to-dracula-pink/20`
- `text-slate-300` (description text) → `text-dracula-fg`

**Acceptance Criteria:**
- No `slate-` class strings remain in this file
- Card borders and backgrounds use Dracula tokens
- Hover glow uses Dracula purple/pink
- Description text uses `dracula-fg`
- `npm run build` passes

**Dependencies:** Task 1.

---

## Task 6 — Migrate `FinalCTA.tsx` to Dracula palette [frontend]

**Description:** Replace `slate-*` classes in `FinalCTA.tsx`.

**Files:**
- `frontend/src/components/landing/FinalCTA.tsx`

**Key substitutions:**
- `from-slate-900/80 via-purple-900/40 to-slate-900/80` → `from-dracula-bg/80 via-dracula-purple/40 to-dracula-bg/80`
- `text-slate-300` → `text-dracula-fg`
- `text-slate-400` → `text-dracula-comment`
- `border-slate-600` → `border-dracula-current`
- `hover:bg-slate-800/50 hover:border-slate-500` → `hover:bg-dracula-current/50 hover:border-dracula-current`
- `from-purple-300 to-pink-400` → `from-dracula-purple to-dracula-pink`

**Acceptance Criteria:**
- No `slate-` class strings remain in this file
- Section gradient background uses Dracula tokens
- Body text and subtitle text use Dracula colors
- Demo button hover uses Dracula colors
- `npm run build` passes

**Dependencies:** Task 1.

---

## Task 7 — Migrate `Footer.tsx` to Dracula palette [frontend]

**Description:** Replace `slate-*` classes in `Footer.tsx`.

**Files:**
- `frontend/src/components/landing/Footer.tsx`

**Key substitutions:**
- `bg-slate-950/80` (footer bg) → `bg-dracula-bg/80`
- `border-slate-800` (top border) → `border-dracula-current`
- `border-t border-slate-800` (divider) → `border-t border-dracula-current`
- `text-slate-400` (link text, social icons) → `text-dracula-comment`
- `text-slate-500` (copyright) → `text-dracula-comment`
- `hover:bg-slate-900` (icon hover) → `hover:bg-dracula-bg`

**Acceptance Criteria:**
- No `slate-` class strings remain in this file
- Footer background, borders, link text, and copyright text use Dracula tokens
- Social icon hover backgrounds use `dracula-bg`
- `npm run build` passes

**Dependencies:** Task 1.

---

## Task 8 — Migrate `LandingNavbar.tsx` to Dracula palette [frontend]

**Description:** Replace `slate-*` classes in `LandingNavbar.tsx`, including the scrolled state, mobile menu, and GitHub modal.

**Files:**
- `frontend/src/components/landing/LandingNavbar.tsx`

**Key substitutions:**
- `bg-slate-950/80` (scrolled navbar) → `bg-dracula-bg/80`
- `border-slate-700/50` (navbar bottom border) → `border-dracula-current/50`
- `ring-offset-slate-950` (focus ring offset) → `ring-offset-dracula-bg`
- `hover:bg-slate-700` (mobile menu item hover) → `hover:bg-dracula-current`
- `bg-slate-950/95` (mobile menu background) → `bg-dracula-bg/95`
- `bg-slate-900` (GitHub modal background) → `bg-dracula-bg`
- `border-slate-700` (GitHub modal border) → `border-dracula-current`
- `text-slate-400` (close button, modal body) → `text-dracula-comment`
- `ring-offset-slate-900` (focus ring inside modal) → `ring-offset-dracula-bg`

**Acceptance Criteria:**
- No `slate-` class strings remain in this file
- Scrolled navbar uses Dracula background
- Mobile menu and GitHub modal use Dracula backgrounds and borders
- Focus ring offsets use `dracula-bg`
- `npm run build` passes

**Dependencies:** Task 1.

---

## Task 9 — Export SVG data URIs in `constants.ts` [frontend]

**Description:** Extract the base64 SVG data URIs for the five WUBRG mana symbols from `mana-symbols-scryfall.css` and export them as a typed `MANA_SVGS` record in `constants.ts`. Also narrow `MANA_SYMBOLS` to only the five WUBRG symbols.

**Files:**
- `frontend/src/components/backgrounds/constants.ts`
- `frontend/src/mana-symbols-scryfall.css` (read-only reference)

**How to extract:** In `mana-symbols-scryfall.css`, find the rules for `.card-symbol-W`, `.card-symbol-U`, `.card-symbol-B`, `.card-symbol-R`, `.card-symbol-G` (exact single-letter rules only — not `.card-symbol-WB`, etc.). Each has a `background-image: url("data:image/svg+xml;base64,...")` value. Copy the full `data:image/svg+xml;base64,...` string (without the surrounding `url("")` wrapper) into `MANA_SVGS`.

**Line references in CSS file:**
- `.card-symbol-W` starts at line 421
- `.card-symbol-U` starts at line 397
- `.card-symbol-B` starts at line 237
- `.card-symbol-R` starts at line 361
- `.card-symbol-G` starts at line 301

**Changes to `constants.ts`:**
```ts
/** SVG data URIs for WUBRG mana symbols (sourced from mana-symbols-scryfall.css) */
export const MANA_SVGS: Record<string, string> = {
  W: 'data:image/svg+xml;base64,<extracted-W>',
  U: 'data:image/svg+xml;base64,<extracted-U>',
  B: 'data:image/svg+xml;base64,<extracted-B>',
  R: 'data:image/svg+xml;base64,<extracted-R>',
  G: 'data:image/svg+xml;base64,<extracted-G>',
};

// Update MANA_SYMBOLS — remove colorless symbols
export const MANA_SYMBOLS = ['{W}', '{U}', '{B}', '{R}', '{G}'];
```

**Acceptance Criteria:**
- `MANA_SVGS` is exported with all five WUBRG keys
- Each value is a valid `data:image/svg+xml;base64,...` string (loadable via `new Image().src = ...`)
- `MANA_SYMBOLS` contains exactly 5 entries: `['{W}', '{U}', '{B}', '{R}', '{G}']`
- No colorless symbols remain in `MANA_SYMBOLS`
- TypeScript strict mode: no type errors
- `npm run build` passes

**Dependencies:** None (can run in parallel with Tasks 1–8).

---

## Task 10 — Update `CardMatrix.tsx` to render SVG mana icons [frontend]

**Description:** Replace the `ctx.fillText(symbol, ...)` path in `CardMatrix.tsx` with `ctx.drawImage(img, ...)` using pre-loaded `HTMLImageElement` instances from `MANA_SVGS`. Update `getGlowCanvas` to render SVG icons with color tinting instead of text.

**Files:**
- `frontend/src/components/backgrounds/CardMatrix.tsx`

**Step-by-step changes:**

1. **Import `MANA_SVGS`** from `./constants`.

2. **Add `svgImagesRef`** after existing refs:
   ```ts
   const svgImagesRef = useRef<Map<string, HTMLImageElement>>(new Map());
   ```

3. **Add image pre-load `useEffect`** (runs once):
   ```ts
   useEffect(() => {
     Object.entries(MANA_SVGS).forEach(([key, uri]) => {
       const img = new Image();
       img.src = uri;
       svgImagesRef.current.set(key, img);
     });
   }, []);
   ```

4. **Update `getGlowCanvas` signature and body:**
   - New signature: `(cache, svgImages, key, hex, fontSize)` where `svgImages: Map<string, HTMLImageElement>`
   - Cache key: `"${key}:${hex}:${fontSize}"` (includes hex since tint color varies)
   - Return type: `HTMLCanvasElement | null`
   - Body:
     - Get `img = svgImages.get(key)`. If `!img || !img.complete` → return `null`.
     - Create `offscreen` canvas of `size = fontSize * 4`.
     - Draw SVG: `offCtx.drawImage(img, size/4, size/4, fontSize, fontSize)` (centered with padding).
     - Tint with glow color using composite:
       ```ts
       offCtx.globalCompositeOperation = 'source-atop';
       offCtx.globalAlpha = 0.5;
       offCtx.fillStyle = hex;
       offCtx.fillRect(0, 0, size, size);
       offCtx.globalCompositeOperation = 'source-over';
       offCtx.globalAlpha = 1;
       ```
     - Apply glow: `offCtx.shadowColor = hex; offCtx.shadowBlur = 10; offCtx.drawImage(img, size/4, size/4, fontSize, fontSize)`.
     - Cache and return.

5. **Update `draw` function body:**
   - Remove: `ctx.font = ...`, `ctx.fillText(d.symbol, d.x, d.y)`
   - Replace with:
     ```ts
     const img = svgImagesRef.current.get(d.colorKey);
     if (img && img.complete) {
       const half = d.fontSize / 2;
       ctx.globalAlpha = alpha;
       ctx.drawImage(img, d.x - half, d.y - half, d.fontSize, d.fontSize);
     }
     ```
   - Update glow call:
     ```ts
     const glowCanvas = getGlowCanvas(
       glowCacheRef.current,
       svgImagesRef.current,
       d.colorKey,
       hex,
       d.fontSize
     );
     if (isDarkRef.current && glowCanvas) { ... }
     ```
   - Remove `ctx.textAlign` and `ctx.textBaseline` setup (no longer needed).

6. **`SymbolDrop` interface** — no changes needed.

7. **`update()` function** — no changes needed.

**Acceptance Criteria:**
- Canvas renders circular mana symbol icons (W, U, B, R, G) instead of `{W}`, `{U}`, etc. text
- Each symbol retains its colored glow in dark mode
- No `ctx.fillText` calls remain for mana symbols in `draw()`
- Symbols that haven't finished loading (first frame edge case) are silently skipped
- No TypeScript strict-mode errors (`svgImagesRef` typed correctly, `getGlowCanvas` return type is `HTMLCanvasElement | null`)
- `npm run build` passes
- `useEffect` for image preloading has `[]` dependency array (ESLint clean)

**Dependencies:** Task 9 (needs `MANA_SVGS` export).

---

## Execution Order

```
Task 1  (tailwind config)
   ├── Tasks 2–8  (component + CSS migrations, all parallel)
   └── Task 9  (constants.ts, parallel with 2–8)
          └── Task 10  (CardMatrix.tsx, depends on Task 9)
```

Tasks 2–9 can be executed in parallel after Task 1 completes. Task 10 requires Task 9.
