# Context Bundle: Dracula Theme and Mana Symbol Rendering on Landing

This document bundles all context a developer needs to implement this change without reading the full codebase.

---

## What This Change Does

Two independent visual fixes for the landing page (`/`):

1. **Dracula theme** — Replace Tailwind `slate-*` colors in all landing components with named Dracula palette tokens added to `tailwind.config.js`. The dark body background in `index.css` is also updated.

2. **Mana symbol icons** — The `CardMatrix` animated background currently renders literal text like `{B}`, `{W}` on canvas. This change replaces that with actual circular MTG mana symbol SVGs already bundled in the project.

**No backend changes. No i18n changes. No authenticated-page changes.**

---

## Project Conventions (frontend)

- Functional components only (no class components)
- Tailwind CSS for all styling — no inline styles, no CSS modules
- TypeScript strict mode — no `any`, all function signatures typed
- `npm run build` must pass (TypeScript + Vite)
- Tests use Vitest + React Testing Library
- Pytest fixture rule does not apply here (frontend only)

---

## Repo Layout (relevant paths)

```
frontend/
  tailwind.config.js                         ← Add Dracula tokens here
  src/
    index.css                                ← Update .dark body background
    mana-symbols-scryfall.css                ← Source of SVG data URIs (read-only)
    components/
      landing/
        Hero.tsx                             ← Replace slate-* classes
        BentoGrid.tsx                        ← Replace slate-* + gradient props
        BentoCard.tsx                        ← Replace slate-* in structural classes
        FinalCTA.tsx                         ← Replace slate-* classes
        Footer.tsx                           ← Replace slate-* classes
        LandingNavbar.tsx                    ← Replace slate-* classes
      backgrounds/
        constants.ts                         ← Add MANA_SVGS, narrow MANA_SYMBOLS
        CardMatrix.tsx                       ← Replace fillText with drawImage
        useReducedMotion.ts                  ← Do not touch
```

---

## Current `tailwind.config.js`

```js
export default {
  theme: {
    extend: {
      colors: {
        primary: {
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
        },
        accent: {
          400: '#f472b6',
          500: '#ec4899',
          600: '#db2777',
        },
      },
    },
  },
};
```

Add the `dracula` key inside `theme.extend.colors` — do not remove or modify `primary`/`accent`.

---

## Dracula Palette Tokens to Add

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

Usage: `bg-dracula-bg`, `text-dracula-fg`, `border-dracula-current`, etc. Opacity modifiers work normally: `bg-dracula-bg/80`, `border-dracula-current/50`.

---

## Color Substitution Reference

| Old `slate-*` class | New `dracula-*` class | Notes |
|---|---|---|
| `bg-slate-900`, `bg-slate-950` | `bg-dracula-bg` | Background fills |
| `bg-slate-800`, `bg-slate-700` | `bg-dracula-current` | Hover/nested fills |
| `border-slate-700`, `border-slate-800` | `border-dracula-current` | Borders |
| `border-slate-600` | `border-dracula-current` | Card borders |
| `text-slate-100`, `text-slate-300` | `text-dracula-fg` | Primary text |
| `text-slate-400`, `text-slate-500` | `text-dracula-comment` | Secondary text |
| `hover:bg-slate-700` | `hover:bg-dracula-current` | Hover states |
| `hover:bg-slate-800/50` | `hover:bg-dracula-current/50` | Semi-transparent hover |
| `hover:bg-slate-900` | `hover:bg-dracula-bg` | Icon hover fill |
| `hover:border-slate-500` | `hover:border-dracula-current` | Hover border |
| `from-slate-900`, `to-slate-950` | `from-dracula-bg`, `to-dracula-bg` | Gradient stops |
| `via-purple-900` | `via-dracula-purple/10` | Gradient midpoint |
| `ring-offset-slate-950`, `ring-offset-slate-900` | `ring-offset-dracula-bg` | Focus ring offset |

**Gradient accent classes (headlines, buttons):**
| Old | New |
|---|---|
| `from-purple-300 via-purple-400 to-pink-500` | `from-dracula-purple to-dracula-pink` |
| `from-purple-300 to-pink-400` | `from-dracula-purple to-dracula-pink` |

**BentoCard gradient prop classes:**
| Old | New |
|---|---|
| `from-blue-500/20 to-blue-600/20` | `from-dracula-cyan/20 to-dracula-cyan/20` |
| `text-blue-400/60 group-hover:text-blue-300/80` | `text-dracula-cyan/60 group-hover:text-dracula-cyan/80` |
| `from-purple-500/20 to-purple-600/20` | `from-dracula-purple/20 to-dracula-purple/20` |
| `text-purple-400/60 group-hover:text-purple-300/80` | `text-dracula-purple/60 group-hover:text-dracula-purple/80` |
| `from-pink-500/20 to-rose-600/20` | `from-dracula-pink/20 to-dracula-pink/20` |
| `text-pink-400/60 group-hover:text-pink-300/80` | `text-dracula-pink/60 group-hover:text-dracula-pink/80` |
| `from-amber-500/20 to-orange-600/20` | `from-dracula-orange/20 to-dracula-orange/20` |
| `text-amber-400/60 group-hover:text-amber-300/80` | `text-dracula-orange/60 group-hover:text-dracula-orange/80` |
| `from-green-500/20 to-emerald-600/20` | `from-dracula-green/20 to-dracula-green/20` |
| `text-green-400/60 group-hover:text-green-300/80` | `text-dracula-green/60 group-hover:text-dracula-green/80` |

**Inline purple text in Hero.tsx description card:**
| Old | New |
|---|---|
| `text-purple-300` | `text-dracula-purple` |
| `text-purple-400` | `text-dracula-purple` |
| `text-purple-400/70` | `text-dracula-purple/70` |

---

## Current `index.css` (relevant section)

```css
body {
  margin: 0;
  min-height: 100vh;
  background-color: #f3f4f6;   /* light mode — do not change */
}
.dark body {
  background-color: #111827;   /* ← change this to #282a36 */
}
```

---

## Current `constants.ts`

```ts
export interface ManaColor {
  dark: string;
  light: string;
}

export const MANA_COLORS: Record<string, ManaColor> = {
  W: { dark: '#FFFBD5', light: '#B8860B' },
  U: { dark: '#0E68AB', light: '#0A4F8A' },
  B: { dark: '#A070B0', light: '#5C3D6E' },
  R: { dark: '#D3202A', light: '#A01820' },
  G: { dark: '#00733E', light: '#005A2E' },
};

// Current — includes colorless symbols that have no SVG:
export const MANA_SYMBOLS = ['{W}', '{U}', '{B}', '{R}', '{G}', '{T}', '{X}', '{1}', '{2}', '{3}'];

export function symbolToColorKey(symbol: string): string {
  const key = symbol.replace(/[{}]/g, '');
  if (key in MANA_COLORS) return key;
  const keys = Object.keys(MANA_COLORS);
  return keys[Math.floor(Math.random() * keys.length)];
}
```

**Required additions:**
- Export `MANA_SVGS: Record<string, string>` with W/U/B/R/G data URI strings
- Narrow `MANA_SYMBOLS` to `['{W}', '{U}', '{B}', '{R}', '{G}']`
- Keep `MANA_COLORS` and `symbolToColorKey` unchanged

**Where to get the SVG data URIs:** From `mana-symbols-scryfall.css`. Find these rules:
- `.card-symbol-W` at line ~421
- `.card-symbol-U` at line ~397
- `.card-symbol-B` at line ~237
- `.card-symbol-R` at line ~361
- `.card-symbol-G` at line ~301

Each has: `background-image: url("data:image/svg+xml;base64,...")`. Copy the full `data:image/svg+xml;base64,...` value (strip the `url("")` wrapper).

---

## Current `CardMatrix.tsx` — Key Sections to Change

### What currently renders the symbol (in `draw` callback):
```ts
ctx.globalAlpha = alpha;
ctx.font = `${d.fontSize}px monospace`;
ctx.fillStyle = hex;
ctx.fillText(d.symbol, d.x, d.y);   // ← renders "{B}", "{W}", etc.
```

### What currently renders the glow:
```ts
if (isDarkRef.current) {
  const glowCanvas = getGlowCanvas(glowCacheRef.current, hex, d.fontSize, d.symbol);
  ctx.globalAlpha = alpha * 0.4;
  ctx.drawImage(glowCanvas, d.x - glowCanvas.width / 2, d.y - glowCanvas.height / 2);
}
```

### Current `getGlowCanvas` signature:
```ts
function getGlowCanvas(
  cache: Map<string, HTMLCanvasElement>,
  hex: string,
  fontSize: number,
  symbol: string
): HTMLCanvasElement
```

### Required changes summary:
1. Add `svgImagesRef = useRef<Map<string, HTMLImageElement>>(new Map())`
2. Add `useEffect(() => { /* load MANA_SVGS into svgImagesRef */ }, [])`
3. Update `getGlowCanvas` to accept `svgImages` param, use `drawImage` instead of `fillText`, return `HTMLCanvasElement | null`
4. In `draw`: replace `ctx.fillText(d.symbol, ...)` with `ctx.drawImage(img, ...)`
5. In `draw`: update glow call to pass `svgImagesRef.current` and `d.colorKey`; handle `null` return
6. Remove `ctx.font`, `ctx.textAlign`, `ctx.textBaseline` setup in `draw` (not needed for image rendering)

### Glow tinting technique (source-atop composite):
```ts
// After drawing the SVG image:
offCtx.globalCompositeOperation = 'source-atop';
offCtx.globalAlpha = 0.5;
offCtx.fillStyle = hex;           // mana color (e.g., #A070B0 for B)
offCtx.fillRect(0, 0, size, size);
offCtx.globalCompositeOperation = 'source-over';
offCtx.globalAlpha = 1;
// Then draw with shadowBlur for the actual glow halo
offCtx.shadowColor = hex;
offCtx.shadowBlur = 10;
offCtx.drawImage(img, padding, padding, fontSize, fontSize);
```

---

## What NOT to Change

- `frontend/src/components/backgrounds/useReducedMotion.ts` — untouched
- `frontend/src/mana-symbols-scryfall.css` — read-only source, do not modify
- Any component under `frontend/src/pages/` except via the landing components listed above
- Dashboard, Settings, Admin, Analytics pages — no changes
- `primary` / `accent` Tailwind tokens
- Light mode styles
- Any backend file

---

## Verification Checklist

After implementation, verify:

- [ ] `npm run build` exits 0 with no TypeScript errors
- [ ] In dark mode, landing page body background is `#282a36` (inspect element)
- [ ] All landing sections show Dracula-tinted dark backgrounds (no pure grey)
- [ ] Landing borders have the slight purple tint of `#44475a`
- [ ] `CardMatrix` canvas shows circular mana symbol icons (not `{B}`, `{W}` text)
- [ ] Mana symbols have colored glow in dark mode
- [ ] Dashboard/Settings pages have no visual changes
- [ ] `npm run lint` passes (ESLint clean)
