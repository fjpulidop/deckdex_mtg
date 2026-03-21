# Proposal: Dracula Theme and Mana Symbol Rendering on Landing

## Change Name
`dracula-theme-and-mana-symbols`

## Problem

The landing page has two independent visual regressions relative to the intended Dracula aesthetic:

**1. Generic slate palette instead of Dracula colors**

All landing sections (`Hero`, `BentoGrid`, `BentoCard`, `FinalCTA`, `Footer`, `LandingNavbar`) use Tailwind's built-in `slate-*` color scale (`slate-900`, `slate-950`, `slate-700`, etc.) as their dark background, border, and text colors. The Dracula color scheme (`#282a36` background, `#44475a` current-line, `#f8f8f2` foreground, etc.) has different hue and saturation values that give the landing page its signature purple-tinted dark aesthetic. The current slate palette lacks this tint, producing a neutral grey appearance that clashes with the purple gradient accents already present in the headlines and CTAs.

The `index.css` `.dark body` rule also sets the body background to `#111827` (Tailwind's `gray-900`), which does not match the Dracula background color (`#282a36`).

**2. Literal text strings rendered in place of mana symbol icons**

`CardMatrix.tsx` uses `ctx.fillText(d.symbol, ...)` to paint each mana symbol as raw text on the canvas (e.g., `{B}`, `{W}`, `{R}`). The project already ships full-resolution SVG data URIs for every MTG mana symbol in `mana-symbols-scryfall.css`. The canvas background animation should render recognizable circular mana symbols instead of monospace bracket text, matching the visual language established by the `ManaText` component used elsewhere in the app.

## Solution

### Part A — Dracula color tokens in Tailwind

Add a `dracula` namespace to `tailwind.config.js` with the full Dracula palette as named color tokens. Replace every `slate-*` occurrence across the six landing components and `index.css` with the corresponding Dracula token. Retain all opacity modifiers (`/80`, `/40`, etc.) and gradient directives unchanged.

Token mapping:

| Dracula token       | Hex value | Replaces         |
|---------------------|-----------|------------------|
| `dracula-bg`        | `#282a36` | `slate-900/950`  |
| `dracula-current`   | `#44475a` | `slate-700/800`  |
| `dracula-fg`        | `#f8f8f2` | `slate-100/200`  |
| `dracula-comment`   | `#6272a4` | `slate-400/500`  |
| `dracula-purple`    | `#bd93f9` | gradient accents |
| `dracula-pink`      | `#ff79c6` | gradient accents |
| `dracula-cyan`      | `#8be9fd` | blue accents     |
| `dracula-green`     | `#50fa7b` | green accents    |
| `dracula-orange`    | `#ffb86c` | amber/orange     |
| `dracula-yellow`    | `#f1fa8c` | yellow           |

### Part B — SVG mana icons on canvas

Export SVG data URI strings for W, U, B, R, G from a new `MANA_SVGS` record in `constants.ts`. These strings are already embedded in `mana-symbols-scryfall.css` as `background-image` CSS rules — extract the base64 payloads from the five single-letter rules (`.card-symbol-W`, `.card-symbol-U`, `.card-symbol-B`, `.card-symbol-R`, `.card-symbol-G`).

In `CardMatrix.tsx`, pre-load each SVG as an `HTMLImageElement` at component mount. Cache these images in a `svgImagesRef` alongside the existing `glowCacheRef`. Modify `MANA_SYMBOLS` in `constants.ts` to export only the five WUBRG keys (drop the colorless symbols `{T}`, `{X}`, `{1}`, `{2}`, `{3}` since they have no WUBRG color mapping and no SVG). Update `getGlowCanvas` and the `draw` function to call `ctx.drawImage(img, ...)` instead of `ctx.fillText(symbol, ...)`. Maintain the existing colored glow layer via `ctx.globalCompositeOperation` tinting.

## Acceptance Criteria

1. Landing page dark body background is `#282a36`
2. All landing section backgrounds use Dracula palette (`#282a36`, `#44475a`) instead of `slate-900`/`slate-950`
3. Landing border colors use `#44475a` instead of `slate-700`/`slate-800`
4. Landing text colors map to `#f8f8f2` and `#6272a4` instead of `slate-300`/`slate-400`
5. Gradient accents use Dracula Purple (`#bd93f9`) and Pink (`#ff79c6`)
6. `CardMatrix` canvas renders actual MTG mana symbol icons instead of `{B}`, `{W}` text
7. Mana symbols retain their colored glow effect
8. No visual changes on authenticated pages (Dashboard, Settings, Admin, etc.)
9. `npm run build` passes without TypeScript errors

## Out of Scope

- Dashboard or authenticated page theme changes
- Adding Dracula as a toggleable user theme option
- Modifying the light mode palette
- Changing existing `primary`/`accent` Tailwind token values
- Rendering all Scryfall symbols beyond the five WUBRG basics
