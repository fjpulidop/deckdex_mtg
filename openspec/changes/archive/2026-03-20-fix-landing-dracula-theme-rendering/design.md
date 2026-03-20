# Technical Design: Fix Landing Page Dracula Theme Rendering

**Change name:** `fix-landing-dracula-theme-rendering`

---

## Root Cause Analysis

### Tailwind v4 `@theme` requirement

`frontend/src/index.css` line 1:
```css
@import "tailwindcss";
```

This activates the Tailwind v4 CSS engine. In v4, the compiler scans source files for class names and generates utilities **only for tokens declared inside `@theme { }` blocks in CSS files**. The `tailwind.config.js` file's `theme.extend.colors` object is not processed by the v4 engine — it has no effect.

Result: every class that references a custom token (`text-dracula-fg`, `bg-dracula-bg`, `from-primary-500`, `to-accent-500`, etc.) is unknown to the compiler. The browser receives no rule for these classes and falls back to:
- `color` properties: browser default = black
- `background-color` properties: no rule generated = transparent
- Gradient `from-*`/`to-*` properties: no rule generated = gradient has no color stops

### Secondary issue: opacity modifiers on unresolved tokens

Classes like `bg-dracula-bg/80` apply an opacity modifier to the base color token. When the token is not registered, both the base and the modifier are lost. All section backgrounds become fully transparent, eliminating visual separation between sections.

### Navbar composition: already correct

`App.tsx` line 37 renders `<LandingNavbar />` conditionally for the landing route:
```tsx
{isLandingPage && <LandingNavbar />}
```
`Landing.tsx` does not and should not include `LandingNavbar` — the composition is at the router level. No change needed.

---

## Affected Files

| File | Change Type | Reason |
|------|-------------|--------|
| `frontend/src/index.css` | Modify | Add `@theme` block with all color tokens |
| `frontend/src/components/landing/Hero.tsx` | Modify | Fix section background for visual separation |
| `frontend/src/components/landing/BentoGrid.tsx` | Modify | Fix section background for visual separation |
| `frontend/src/components/landing/FinalCTA.tsx` | Modify | Fix section background for visual separation |
| `frontend/tailwind.config.js` | Modify | Mark as inert or clear content (tokens moved to CSS) |
| `frontend/src/pages/Landing.tsx` | Verify only | Confirm no navbar duplication needed |
| `frontend/src/App.tsx` | Verify only | Confirm navbar composition is correct |
| Dashboard-area components | Verify only | Confirm no regressions from `@theme` migration |

---

## Implementation Design

### 1. The `@theme` block

All custom tokens from `tailwind.config.js` must be declared as CSS custom properties under `@theme` in `index.css`. Tailwind v4's naming convention maps `--color-<name>` CSS variables to `bg-<name>`, `text-<name>`, etc. utility classes.

The complete set of tokens to migrate:

```
primary:
  400 → #c084fc
  500 → #a855f7
  600 → #9333ea
  700 → #7e22ce

accent:
  400 → #f472b6
  500 → #ec4899
  600 → #db2777

dracula:
  bg      → #282a36
  current → #44475a
  fg      → #f8f8f2
  comment → #6272a4
  purple  → #bd93f9
  pink    → #ff79c6
  cyan    → #8be9fd
  green   → #50fa7b
  orange  → #ffb86c
  yellow  → #f1fa8c
```

CSS variable name format used by Tailwind v4 for nested color scales:
- `primary.400` → `--color-primary-400`
- `dracula.bg` → `--color-dracula-bg`

The resulting `@theme` block in `index.css` (inserted after `@import "tailwindcss"`):

```css
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
```

Once this block is in place, all existing class names across every component resolve to their correct values with zero component-level changes required for tokens to work.

### 2. Section background strategy for visual separation

After the token fix, the three sections still need distinct backgrounds because the current classes all derive from the same `dracula-bg` base with different opacity levels, which will look similar.

**Principle:** use the Dracula palette's natural depth hierarchy:
- `dracula-bg` (`#282a36`) — darkest, used as the page base
- `dracula-current` (`#44475a`) — mid-dark, used for surface elevation
- Low-opacity accent colors for tinted sections

**Section assignments:**

| Section | Current class | Proposed class | Visual effect |
|---------|--------------|----------------|---------------|
| Hero | `bg-gradient-to-br from-dracula-bg/20 via-dracula-purple/10 to-dracula-bg/20` | `bg-dracula-bg` | Solid dark base; CardMatrix canvas visible behind via page background |
| BentoGrid | `bg-gradient-to-b from-dracula-bg/80 to-dracula-bg/80` | `bg-dracula-current/20` | Slightly lighter tinted surface, creates visible break from Hero |
| FinalCTA | `bg-gradient-to-r from-dracula-bg/80 via-dracula-purple/40 to-dracula-bg/80` | `bg-gradient-to-r from-dracula-bg via-dracula-purple/20 to-dracula-bg` | Subtle purple tint gradient; distinct from the neutral BentoGrid above |
| Footer | `bg-dracula-bg/80` | No change needed (border-t creates visual break) | Solid base |

Note: Hero's section uses `min-h-screen` so its background fills the viewport. The CardMatrix canvas is `position: fixed z-0` and the Hero section has `relative z-10`, so the Hero section background will sit on top of the canvas. Using `bg-dracula-bg` (fully opaque) for Hero is intentional — the canvas shows only where no section background covers it (i.e., through opacity modifiers elsewhere or behind transparent areas).

### 3. `tailwind.config.js` fate in v4

With tokens moved to `@theme` in the CSS, `tailwind.config.js` is inert. Options:
1. Keep the file with a comment marking it as a v3 artifact (no functional effect)
2. Replace content with an empty default export

Option 1 is preferred for clarity — a developer reading the file should understand why it exists even though it has no effect. The file should gain a top comment: `// Tailwind v4: color tokens are declared in src/index.css @theme block. This file has no effect.`

### 4. Dashboard regression audit

The Grep confirms that `dracula`, `primary-`, and `accent-` classes appear **only** in `src/components/landing/` files. Dashboard components (`CardTable`, `CardFormModal`, `Filters`, etc.) use standard Tailwind colors and `dark:` variants. The `@theme` migration adds new CSS custom properties but does not remove or rename any existing ones — Dashboard components are unaffected.

The `body` rule in `index.css` uses hardcoded hex `#282a36` (not a class) for dark mode background, so it is unaffected by the `@theme` changes.

### 5. BentoCard gradient visibility

BentoCard's illustration area:
```tsx
<div className={`... bg-gradient-to-br ${gradientFrom} ${gradientTo} ...`}>
```

Where `gradientFrom`/`gradientTo` are e.g. `"from-dracula-cyan/20"` / `"to-dracula-cyan/20"`. After the token fix, these will resolve correctly. The `/20` opacity means the illustration background will be a subtle tint — this is intentional and visually correct once the underlying color is not transparent.

The outer card background `bg-dracula-bg/50` (50% opacity `#282a36`) will also resolve. Cards will have the correct semi-transparent dark background with `backdrop-blur-sm`.

---

## Class Audit: All Landing Components

### Hero.tsx — problematic classes
| Class | Issue | Status after fix |
|-------|-------|-----------------|
| `bg-gradient-to-br from-dracula-bg/20 via-dracula-purple/10 to-dracula-bg/20` | All tokens unresolved → transparent gradient | Fixed by token migration + background swap |
| `text-dracula-fg` | Token unresolved → black text | Fixed by token migration |
| `bg-gradient-to-r from-accent-500/10 to-primary-500/10` | Tokens unresolved → transparent | Fixed by token migration |
| `bg-gradient-to-r from-dracula-purple to-dracula-pink bg-clip-text text-transparent` | Tokens unresolved → transparent gradient text (invisible) | Fixed by token migration |
| `border-dracula-current/50` | Token unresolved → no border color | Fixed by token migration |
| `bg-dracula-bg/60` | Token unresolved → transparent card background | Fixed by token migration |
| `from-primary-500 to-accent-500` | Tokens unresolved → transparent buttons | Fixed by token migration |

### BentoGrid.tsx — problematic classes
| Class | Issue | Status after fix |
|-------|-------|-----------------|
| `bg-gradient-to-b from-dracula-bg/80 to-dracula-bg/80` | Resolves to transparent → no section background | Fixed by token migration + background swap |
| `text-dracula-comment` | Token unresolved → black text | Fixed by token migration |
| `text-accent-400` | Token unresolved → default color | Fixed by token migration |

### BentoCard.tsx — problematic classes
| Class | Issue | Status after fix |
|-------|-------|-----------------|
| `border-dracula-current/50` | Token unresolved → no border | Fixed by token migration |
| `bg-dracula-bg/50` | Token unresolved → transparent | Fixed by token migration |
| `from-primary-500/20 to-accent-500/20` | Tokens unresolved → transparent | Fixed by token migration |
| `bg-accent-500/20 text-accent-300 border-accent-500/50` | Tokens unresolved | Fixed by token migration |
| `text-dracula-fg` | Token unresolved → black | Fixed by token migration |
| `from-dracula-cyan/20` (and other per-card gradients) | Tokens unresolved → transparent illustrations | Fixed by token migration |

### FinalCTA.tsx — problematic classes
| Class | Issue | Status after fix |
|-------|-------|-----------------|
| `bg-gradient-to-r from-dracula-bg/80 via-dracula-purple/40 to-dracula-bg/80` | All tokens unresolved → transparent | Fixed by token migration + background swap |
| `text-dracula-fg` | Token unresolved → black text | Fixed by token migration |
| `text-dracula-comment` | Token unresolved → black | Fixed by token migration |
| `text-accent-400` | Token unresolved | Fixed by token migration |
| `border-dracula-current` | Token unresolved → no border on demo button | Fixed by token migration |
| `from-primary-500 to-accent-500` | Tokens unresolved → transparent buttons | Fixed by token migration |

### LandingNavbar.tsx — problematic classes
| Class | Issue | Status after fix |
|-------|-------|-----------------|
| `bg-dracula-bg/80` | Token unresolved → transparent scrolled nav | Fixed by token migration |
| `border-dracula-current/50` | Token unresolved → no border | Fixed by token migration |
| `text-dracula-fg` | Token unresolved → black | Fixed by token migration |
| `from-primary-400 to-accent-500 bg-clip-text text-transparent` | Tokens unresolved → invisible logo text | Fixed by token migration |
| `focus-visible:ring-offset-dracula-bg` | Token unresolved → fallback | Fixed by token migration |
| `bg-dracula-bg` | Token unresolved → GitHub modal transparent | Fixed by token migration |

### Footer.tsx — problematic classes
| Class | Issue | Status after fix |
|-------|-------|-----------------|
| `bg-dracula-bg/80` | Token unresolved → transparent footer | Fixed by token migration |
| `border-dracula-current` | Token unresolved → no border | Fixed by token migration |
| `text-dracula-comment` | Token unresolved → black | Fixed by token migration |

---

## Risk Assessment

**Low risk:** The `@theme` migration is additive — it declares new CSS custom properties without removing or overriding any existing rules. The only change to existing CSS is to the section background classes on three components, which are purely cosmetic.

**Regression surface:** The entire application's CSS output is rebuilt when `@theme` changes. Dashboard components do not use any of the migrated tokens (confirmed by Grep), so they are unaffected.

**Build correctness:** `npm run build` invokes `vite build`, which runs the Tailwind v4 CSS transformation. Adding `@theme` tokens will cause the compiler to emit more utility classes, not fewer — build cannot regress on a well-formed `@theme` block.
