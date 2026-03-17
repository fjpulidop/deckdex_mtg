# Design: Dracula Theme and Mana Symbol Rendering on Landing

## Overview

This change is purely frontend. It touches two independent concerns:

1. **Color system** — Add Dracula palette tokens to Tailwind and migrate landing components off `slate-*`
2. **Canvas rendering** — Replace `fillText` with `drawImage` in `CardMatrix.tsx` for WUBRG mana symbols

There are no backend changes, no i18n string additions, and no API changes.

---

## Part A: Dracula Color Tokens

### A.1 — `tailwind.config.js`

Add a `dracula` key under `theme.extend.colors`. Each Dracula palette color becomes a flat token (not a numeric scale), so they are used as `bg-dracula-bg`, `text-dracula-fg`, `border-dracula-current`, etc.

```js
// tailwind.config.js — new entries inside theme.extend.colors
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

Existing `primary` and `accent` tokens are untouched. Dracula tokens only appear in landing-scoped components.

### A.2 — Color Mapping Table

The following substitution table drives all component edits. Opacity modifiers (e.g., `/80`, `/40`, `/50`) are preserved on whichever token they appear with.

| Old class (slate)                    | New class (dracula)                      | Semantic role              |
|--------------------------------------|------------------------------------------|----------------------------|
| `bg-slate-900` / `bg-slate-950`      | `bg-dracula-bg`                          | Section / card background  |
| `bg-slate-800`                       | `bg-dracula-current`                     | Hover background           |
| `bg-slate-700`                       | `bg-dracula-current`                     | Hover background (lighter) |
| `border-slate-700` / `border-slate-800` | `border-dracula-current`              | Section borders            |
| `border-slate-600`                   | `border-dracula-current`                 | Card borders               |
| `text-slate-100` / `text-slate-300`  | `text-dracula-fg`                        | Primary body text          |
| `text-slate-400` / `text-slate-500`  | `text-dracula-comment`                   | Secondary / muted text     |
| `from-slate-900` / `to-slate-950`    | `from-dracula-bg` / `to-dracula-bg`      | Gradient endpoints         |
| `via-purple-900`                     | `via-dracula-purple/10`                  | Gradient midpoint accent   |
| `hover:bg-slate-700`                 | `hover:bg-dracula-current`               | Interactive states         |
| `hover:bg-slate-900`                 | `hover:bg-dracula-bg`                    | Icon hover background      |
| `focus-visible:ring-offset-slate-950` | `focus-visible:ring-offset-dracula-bg`  | Focus ring                 |
| `focus-visible:ring-offset-slate-900` | `focus-visible:ring-offset-dracula-bg`  | Focus ring (modal)         |

**Gradient accent classes** in headlines (`from-purple-300 via-purple-400 to-pink-500`) are replaced with Dracula equivalents:
- `from-purple-300` → `from-dracula-purple`
- `via-purple-400` → (drop or keep transparent mid)
- `to-pink-500` → `to-dracula-pink`
- `from-purple-300 to-pink-400` → `from-dracula-purple to-dracula-pink`

**BentoCard gradient colors** — the `gradientFrom`/`gradientTo` props in `BentoGrid.tsx` use Tailwind color utility classes, not `slate`. These map to Dracula where there is a semantically equivalent color:
- `from-blue-500/20` → `from-dracula-cyan/20`
- `to-blue-600/20` → `to-dracula-cyan/20`
- `from-amber-500/20` / `to-orange-600/20` → `from-dracula-orange/20` / `to-dracula-orange/20`
- `from-green-500/20` / `to-emerald-600/20` → `from-dracula-green/20` / `to-dracula-green/20`
- `from-purple-500/20` / `to-purple-600/20` → `from-dracula-purple/20` / `to-dracula-purple/20`
- `from-pink-500/20` / `to-rose-600/20` → `from-dracula-pink/20` / `to-dracula-pink/20`

And the icon color props:
- `text-blue-400/60 group-hover:text-blue-300/80` → `text-dracula-cyan/60 group-hover:text-dracula-cyan/80`
- `text-amber-400/60 group-hover:text-amber-300/80` → `text-dracula-orange/60 group-hover:text-dracula-orange/80`
- `text-green-400/60 group-hover:text-green-300/80` → `text-dracula-green/60 group-hover:text-dracula-green/80`
- `text-purple-400/60 group-hover:text-purple-300/80` → `text-dracula-purple/60 group-hover:text-dracula-purple/80`
- `text-pink-400/60 group-hover:text-pink-300/80` → `text-dracula-pink/60 group-hover:text-dracula-pink/80`

Inline purple text references (`text-purple-300`, `text-purple-400`, `text-purple-400/70`) that appear in `Hero.tsx` description card panels become `text-dracula-purple` and `text-dracula-purple/70`.

### A.3 — `index.css` body background

Change the `.dark body` background from `#111827` (gray-900) to `#282a36` (Dracula bg). The rule is scoped to `.dark body` so it only activates when the HTML element has the `dark` class — the authenticated app also applies this class. Per the issue, this change is acceptable app-wide since `#282a36` is the intended dark background. Authenticated pages set their own section backgrounds via component classes and will not be visually affected.

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

---

## Part B: SVG Mana Icons in CardMatrix

### B.1 — `constants.ts` — Export SVG data URIs

The five base64 SVG strings for W, U, B, R, G are already present in `mana-symbols-scryfall.css` as the `background-image` property values of `.card-symbol-W`, `.card-symbol-U`, `.card-symbol-B`, `.card-symbol-R`, `.card-symbol-G`. Each value is a `url("data:image/svg+xml;base64,...")` string.

Extract the raw base64 payload (without the `url("...")` wrapper) from each rule and export them as a typed record:

```ts
// constants.ts additions

/** SVG data URIs for WUBRG mana symbols (sourced from mana-symbols-scryfall.css) */
export const MANA_SVGS: Record<string, string> = {
  W: 'data:image/svg+xml;base64,<base64-for-W>',
  U: 'data:image/svg+xml;base64,<base64-for-U>',
  B: 'data:image/svg+xml;base64,<base64-for-B>',
  R: 'data:image/svg+xml;base64,<base64-for-R>',
  G: 'data:image/svg+xml;base64,<base64-for-G>',
};
```

Also narrow `MANA_SYMBOLS` to only the five WUBRG symbols that have SVG icons:

```ts
// Before
export const MANA_SYMBOLS = ['{W}', '{U}', '{B}', '{R}', '{G}', '{T}', '{X}', '{1}', '{2}', '{3}'];

// After
export const MANA_SYMBOLS = ['{W}', '{U}', '{B}', '{R}', '{G}'];
```

The colorless symbols (`{T}`, `{X}`, `{1}`, `{2}`, `{3}`) are dropped because `symbolToColorKey` already maps them to a random WUBRG key — there is no direct colorless SVG in `MANA_SVGS`, and the visual benefit of including them is zero once we have the actual circular WUBRG icons.

### B.2 — `CardMatrix.tsx` — Pre-load SVG images

Add a `svgImagesRef` to hold pre-loaded `HTMLImageElement` instances, one per WUBRG key. Images are loaded once at component mount via a `useEffect` with an empty dependency array. Loading is asynchronous; the animation loop only draws SVG images for a symbol once its `HTMLImageElement.complete` is true (or the `onload` callback has fired).

```ts
// New ref
const svgImagesRef = useRef<Map<string, HTMLImageElement>>(new Map());

// New useEffect (runs once at mount)
useEffect(() => {
  Object.entries(MANA_SVGS).forEach(([key, uri]) => {
    const img = new Image();
    img.src = uri;
    svgImagesRef.current.set(key, img);
  });
}, []);
```

### B.3 — `CardMatrix.tsx` — Update `getGlowCanvas`

The existing `getGlowCanvas` helper renders text to an off-screen canvas and returns it. Replace the `fillText` call with a `drawImage` call using the pre-loaded SVG image.

Cache key changes from `"${hex}:${fontSize}"` to `"${key}:${fontSize}"` (using the WUBRG color key rather than the hex, since the SVG image is the same regardless of theme — only the glow color differs). The off-screen canvas tints the symbol with a `source-atop` composite over a filled rect of the glow color.

New signature:

```ts
function getGlowCanvas(
  cache: Map<string, HTMLCanvasElement>,
  svgImages: Map<string, HTMLImageElement>,
  key: string,
  hex: string,
  fontSize: number
): HTMLCanvasElement | null
```

Rendering logic inside `getGlowCanvas`:

1. Retrieve `svgImages.get(key)`. If not loaded yet (`!img || !img.complete`), return `null` — caller falls back to no glow.
2. Create off-screen canvas of size `fontSize * 4 x fontSize * 4`.
3. Draw the SVG image centered: `offCtx.drawImage(img, padding, padding, fontSize, fontSize)`.
4. Apply colored glow tint:
   - Set `offCtx.globalCompositeOperation = 'source-atop'`
   - Set `offCtx.fillStyle = hex` with low alpha (e.g., `offCtx.globalAlpha = 0.6`)
   - Fill a rect over the image area
   - Reset `globalCompositeOperation` to `'source-over'`
5. Apply `shadowBlur` glow: draw image again with `shadowColor = hex; shadowBlur = 8` over the composited layer.

### B.4 — `CardMatrix.tsx` — Update `draw` function

Replace the `ctx.fillText(d.symbol, ...)` call with `ctx.drawImage(img, ...)`:

```ts
// In draw():
const img = svgImagesRef.current.get(d.colorKey);
if (img && img.complete) {
  const halfSize = d.fontSize / 2;
  ctx.globalAlpha = alpha;
  ctx.drawImage(img, d.x - halfSize, d.y - halfSize, d.fontSize, d.fontSize);
}
// Glow layer (unchanged call structure, updated helper signature)
if (isDarkRef.current) {
  const glowCanvas = getGlowCanvas(glowCacheRef.current, svgImagesRef.current, d.colorKey, hex, d.fontSize);
  if (glowCanvas) {
    ctx.globalAlpha = alpha * 0.4;
    ctx.drawImage(glowCanvas, d.x - glowCanvas.width / 2, d.y - glowCanvas.height / 2);
  }
}
```

The `svgImagesRef` must be passed into `draw` or accessed via a ref closure. Since `draw` is already a `useCallback` with an empty dependency array that reads everything through refs, `svgImagesRef` follows the same pattern — it is a stable ref.

### B.5 — `SymbolDrop` interface update

Remove the `fontSize` dependency from the glow cache key lookup. The `SymbolDrop` interface and `createDrop` remain unchanged. No changes to `update()`.

---

## Scope Boundary

| File | Changed? | Reason |
|------|----------|--------|
| `frontend/tailwind.config.js` | Yes | Add `dracula` color tokens |
| `frontend/src/index.css` | Yes | Update `.dark body` background |
| `frontend/src/components/landing/Hero.tsx` | Yes | Replace `slate-*` → `dracula-*` |
| `frontend/src/components/landing/BentoGrid.tsx` | Yes | Replace `slate-*` and gradient tokens |
| `frontend/src/components/landing/BentoCard.tsx` | Yes | Replace `slate-*` in border/bg classes |
| `frontend/src/components/landing/FinalCTA.tsx` | Yes | Replace `slate-*` → `dracula-*` |
| `frontend/src/components/landing/Footer.tsx` | Yes | Replace `slate-*` → `dracula-*` |
| `frontend/src/components/landing/LandingNavbar.tsx` | Yes | Replace `slate-*` → `dracula-*` |
| `frontend/src/components/backgrounds/constants.ts` | Yes | Add `MANA_SVGS`, narrow `MANA_SYMBOLS` |
| `frontend/src/components/backgrounds/CardMatrix.tsx` | Yes | SVG image rendering |
| `frontend/src/pages/__tests__/Landing.test.tsx` | No | Existing tests verify structure not classes |
| All authenticated-page components | No | Out of scope |

---

## Key Design Decisions

### Decision: Scoped Tailwind namespace `dracula` (not overriding `slate`)

Overriding the `slate` scale would affect every component in the app, not just landing. Namespacing under `dracula` means only components that explicitly opt in are affected, which matches the scope requirement that authenticated pages remain unchanged.

### Decision: Drop colorless symbols from `MANA_SYMBOLS`

The colorless symbols (`{T}`, `{X}`, `{1}`, `{2}`, `{3}`) have no corresponding SVG in the exported set. Keeping them would require a fallback text rendering path in `draw()`, adding complexity. Since these symbols add no visual value once actual circular WUBRG icons are rendered, they are removed. The animation density remains adequate with 5 symbol types and the existing column/count logic.

### Decision: Reuse existing SVG data URIs from `mana-symbols-scryfall.css`

Rather than fetching SVGs from Scryfall at runtime or bundling separate SVG files, the data URIs already in the CSS file are the most reliable source — they are offline-capable, already bundled, and consistent with the `ManaText` component. Extracting them into `constants.ts` avoids any CSS parsing at runtime.

### Decision: `null` return from `getGlowCanvas` when image not yet loaded

SVG images load asynchronously. A `null` return means the glow layer is simply skipped for that frame — the plain symbol image is still drawn (with `ctx.drawImage`). This produces a brief no-glow appearance at first frame, which is imperceptible at 30fps given that data URI loading completes synchronously in most browsers before the first animation frame.

### Decision: `source-atop` composite for glow tinting

MTG mana symbol SVGs have white backgrounds in some cases (e.g., White mana). Using `source-atop` lets us tint only the opaque pixels of the SVG with the mana color, preserving the circular symbol shape while adding the colored glow that was previously achieved via `shadowColor`. This matches the visual intent of the original text glow.
