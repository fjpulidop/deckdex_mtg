# Context Bundle: Fix Landing Page Dracula Theme Rendering

**Change name:** `fix-landing-dracula-theme-rendering`
**For:** Developer implementing this change

This document is a complete self-contained reference. Read it fully before touching any file.

---

## The One-Sentence Summary

`index.css` uses Tailwind v4's `@import "tailwindcss"` engine, but the Dracula/primary/accent color tokens are defined in `tailwind.config.js` using the v3 format — which v4 ignores — so all custom color classes silently produce no CSS output and the browser falls back to black text and transparent backgrounds.

---

## Architecture You Need to Understand

```
frontend/src/index.css         ← @import "tailwindcss" activates v4 engine
frontend/tailwind.config.js    ← v3-format theme.extend.colors, IGNORED by v4
frontend/src/App.tsx           ← renders <LandingNavbar /> and <CardMatrix /> at route level
frontend/src/pages/Landing.tsx ← renders <Hero />, <BentoGrid />, <FinalCTA />, <Footer />
frontend/src/components/landing/
  LandingNavbar.tsx            ← fixed nav, z-50
  Hero.tsx                     ← first section, min-h-screen
  BentoGrid.tsx                ← features section, id="features"
  BentoCard.tsx                ← individual feature cards
  FinalCTA.tsx                 ← conversion section
  Footer.tsx                   ← site footer
frontend/src/components/backgrounds/
  CardMatrix.tsx               ← canvas animation, position:fixed z-0
```

The stacking context for the landing page:
```
z-0  →  CardMatrix canvas (fixed, full-viewport, behind everything)
z-10 →  Landing div (relative z-10, wraps all sections)
z-50 →  LandingNavbar (fixed, rendered by App.tsx outside Landing component)
```

`LandingNavbar` is rendered by `App.tsx` (line 37), NOT by `Landing.tsx`. This is correct. Do not add it to `Landing.tsx`.

---

## Current File State

### `frontend/src/index.css` (current — broken)

```css
@import "tailwindcss";
@import "./mana-symbols-scryfall.css";

@custom-variant dark (&&:where(.dark, .dark *));

body {
  margin: 0;
  min-height: 100vh;
  background-color: #f3f4f6;
}
.dark body {
  background-color: #282a36;
}
/* ... other rules ... */
```

Problem: No `@theme` block. All custom color utilities are inert.

### `frontend/tailwind.config.js` (current — v3 format, ignored by v4)

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
      },
    },
  },
};
```

---

## Exact Changes Required

### Change 1: `frontend/src/index.css`

Insert the `@theme` block immediately after `@import "tailwindcss";` (line 1), before the `@import "./mana-symbols-scryfall.css"` line.

**Result — full file after change:**

```css
@import "tailwindcss";

@theme {
  /* Primary (purple scale) */
  --color-primary-400: #c084fc;
  --color-primary-500: #a855f7;
  --color-primary-600: #9333ea;
  --color-primary-700: #7e22ce;

  /* Accent (pink scale) */
  --color-accent-400: #f472b6;
  --color-accent-500: #ec4899;
  --color-accent-600: #db2777;

  /* Dracula palette */
  --color-dracula-bg:      #282a36;
  --color-dracula-current: #44475a;
  --color-dracula-fg:      #f8f8f2;
  --color-dracula-comment: #6272a4;
  --color-dracula-purple:  #bd93f9;
  --color-dracula-pink:    #ff79c6;
  --color-dracula-cyan:    #8be9fd;
  --color-dracula-green:   #50fa7b;
  --color-dracula-orange:  #ffb86c;
  --color-dracula-yellow:  #f1fa8c;
}

@import "./mana-symbols-scryfall.css";

/* Dark mode: class on <html> (e.g. class="dark") */
@custom-variant dark (&&:where(.dark, .dark *));

body {
  margin: 0;
  min-height: 100vh;
  background-color: #f3f4f6;
}
.dark body {
  background-color: #282a36;
}

/* MTG mana symbols: estilos Scryfall (SVG) en mana-symbols-scryfall.css; fallback para símbolos sin clase */
.card-symbol {
  background-color: #cac5c0;
}

/* Deck detail modal: curva de maná — etiquetas del eje visibles en modo oscuro */
.dark .deck-detail-mana-curve .recharts-cartesian-axis-tick text {
  fill: #e5e7eb;
}

/* Add cards picker: iconos de color como botones, cursor pointer (no help) */
.picker-color-symbols .card-symbol {
  cursor: pointer !important;
}
```

### Change 2: `frontend/tailwind.config.js`

Add a comment at the top:

```js
// Tailwind v4: color tokens are declared in src/index.css @theme block. This file has no effect.
export default {
  theme: {
    extend: {
      colors: { ... }
    },
  },
};
```

### Change 3: `frontend/src/components/landing/Hero.tsx`

Line 16 — change section `className`:

Before:
```
className="min-h-screen pt-20 pb-16 bg-gradient-to-br from-dracula-bg/20 via-dracula-purple/10 to-dracula-bg/20 flex items-center"
```

After:
```
className="min-h-screen pt-20 pb-16 bg-dracula-bg flex items-center"
```

### Change 4: `frontend/src/components/landing/BentoGrid.tsx`

Line 31 — change section `className`:

Before:
```
className="py-20 md:py-32 bg-gradient-to-b from-dracula-bg/80 to-dracula-bg/80 px-4 sm:px-6 lg:px-8"
```

After:
```
className="py-20 md:py-32 bg-dracula-current/20 px-4 sm:px-6 lg:px-8"
```

### Change 5: `frontend/src/components/landing/FinalCTA.tsx`

Line 14 — change section `className`:

Before:
```
className="py-20 md:py-32 bg-gradient-to-r from-dracula-bg/80 via-dracula-purple/40 to-dracula-bg/80 px-4 sm:px-6 lg:px-8"
```

After:
```
className="py-20 md:py-32 bg-gradient-to-r from-dracula-bg via-dracula-purple/20 to-dracula-bg px-4 sm:px-6 lg:px-8"
```

---

## What NOT to Change

- `Landing.tsx` — do not add `LandingNavbar` here; it is already in `App.tsx`
- `App.tsx` — navbar composition is already correct
- `BentoCard.tsx` — all class names are correct by name; they render fine after the token fix
- `LandingNavbar.tsx` — all class names are correct by name; they render fine after the token fix
- `Footer.tsx` — already uses `bg-dracula-bg/80` and border classes; these will resolve correctly after the token fix and the footer's `border-t` provides sufficient visual separation
- Any Dashboard component — none use custom dracula/primary/accent classes

---

## Token Reference

After the fix, here is what each utility class resolves to:

| Token | Hex | Key class uses |
|-------|-----|---------------|
| `dracula-bg` | `#282a36` | Section backgrounds, card bases, navbar on scroll |
| `dracula-current` | `#44475a` | Borders, hover backgrounds, mobile menu |
| `dracula-fg` | `#f8f8f2` | Body text, subtitle text |
| `dracula-comment` | `#6272a4` | Secondary text, footer links |
| `dracula-purple` | `#bd93f9` | Headline gradients, accent borders, section tints |
| `dracula-pink` | `#ff79c6` | Headline gradient end-stop, hover colors |
| `dracula-cyan` | `#8be9fd` | Collection card illustration |
| `dracula-green` | `#50fa7b` | Price tracking card illustration |
| `dracula-orange` | `#ffb86c` | Real-time progress card illustration |
| `primary-400` | `#c084fc` | Logo gradient |
| `primary-500` | `#a855f7` | CTA button gradient, logo gradient |
| `primary-600` | `#9333ea` | (available, not currently used in landing) |
| `accent-400` | `#f472b6` | Contribute links, badge text |
| `accent-500` | `#ec4899` | CTA button gradient |

---

## Gotchas

### Gotcha 1: `@theme` placement matters
The `@theme` block must appear **after** `@import "tailwindcss"` but it should be placed before other CSS rules. Import statements must remain at the top of the file before any non-import CSS. In practice: `@import "tailwindcss"` → `@theme { }` → `@import "./mana-symbols-scryfall.css"` → all other CSS rules.

Actually: CSS `@import` rules must come before any other rules _except_ `@layer`, `@charset`, and `@import`. In Tailwind v4, `@theme` is a special at-rule processed by the compiler, not a standard CSS rule — it is safe to place after `@import "tailwindcss"` and before `@import "./mana-symbols-scryfall.css"`. If the linter complains about import order, move the mana symbols import to be first (right after `@import "tailwindcss"`).

### Gotcha 2: Opacity modifiers require the base token to be a color, not a variable
Tailwind v4 generates opacity utilities by wrapping the color in `color-mix()` or by using `oklch()` alpha channel. This works automatically when the token is declared in `@theme` — no special syntax needed. `bg-dracula-bg/80` will work once `--color-dracula-bg` is in `@theme`.

### Gotcha 3: BentoCard gradient rendering
BentoCard's illustration container uses the same `gradientFrom` and `gradientTo` for both the start and end, e.g. `from-dracula-cyan/20 to-dracula-cyan/20`. This renders as a flat tinted box (same color, no gradient transition), which is the intended design. It is not a bug — the gradient classes are used for the opacity modifier capability, not for a color transition.

### Gotcha 4: `tailwind.config.js` is not deleted
Keep the file. It documents what the tokens are. Adding a comment makes it clear to the next developer that the file is intentionally inert in v4. Do not delete it — it may be needed if the project ever migrates to a config-file-first setup or uses plugins that still read `tailwind.config.js`.

### Gotcha 5: `bg-dracula-current/20` in BentoGrid
`dracula-current` is `#44475a`. At 20% opacity over the `#282a36` page background, the visual difference is subtle — approximately `#303241`. This is intentional: the section break should be noticeable but not jarring. If the product owner wants a stronger break, increase to `/30` or `/40`.

---

## Verification Checklist

After completing all tasks, run this checklist:

- [ ] `npm run build` exits 0
- [ ] `npm run lint` exits 0
- [ ] In browser DevTools, inspect `.text-dracula-fg` element → computed `color` is `rgb(248, 248, 242)`
- [ ] Hero section: solid dark background, gradient headline text visible (purple → pink), subtitle text white/near-white
- [ ] BentoGrid section: slightly different background shade from Hero, section header visible, cards have colored tinted illustration areas
- [ ] FinalCTA section: subtle purple halo gradient visible against dark background, body text white/near-white
- [ ] LandingNavbar: on scroll, navbar gains a tinted background; DeckDex logo text renders in gradient (not invisible)
- [ ] Footer: dark background, comment-colored links, border-top separator visible
- [ ] No black text anywhere on the landing page
- [ ] Dashboard page renders without visual regressions

---

## Commands

```bash
cd frontend
npm run dev       # start dev server at :5173
npm run build     # production build
npm run lint      # ESLint check
npm run preview   # preview production build locally
```
