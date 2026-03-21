# Tasks: Fix Landing Page Dracula Theme Rendering

**Change name:** `fix-landing-dracula-theme-rendering`
**Layer:** [frontend] only
**Estimated total effort:** < 4 hours

Tasks must be executed in order — Task 1 is the load-bearing prerequisite for all others.

---

## Task 1 — Migrate Dracula + primary + accent tokens to `@theme` in `index.css` [frontend]

**Description:**
Add a `@theme { }` block to `frontend/src/index.css` immediately after the `@import "tailwindcss"` line. This block must declare CSS custom properties for every color token currently in `tailwind.config.js`. This is the single most impactful change: once it is in place, all `text-dracula-*`, `bg-dracula-*`, `from-primary-*`, `to-accent-*`, and related utility classes across all landing components will resolve to their correct hex values without any further edits.

Additionally, add a comment to `tailwind.config.js` indicating that it is now inert under Tailwind v4.

**Modify:**
- `frontend/src/index.css` — insert `@theme` block after line 1

**Modify:**
- `frontend/tailwind.config.js` — add top comment: `// Tailwind v4: color tokens are declared in src/index.css @theme block. This file has no effect.`

**Exact `@theme` block to add (after `@import "tailwindcss";`):**
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

**Acceptance test:**
- `npm run build` completes with exit code 0
- `npm run lint` reports zero new violations
- In the browser (or `npm run preview`), DevTools computed styles for any element with `text-dracula-fg` show `color: rgb(248, 248, 242)` (#f8f8f2), not black
- Any element with `bg-dracula-bg` shows `background-color: rgb(40, 42, 54)` (#282a36)

**Depends on:** nothing

---

## Task 2 — Fix Hero section background for visual separation [frontend]

**Description:**
After Task 1, `Hero.tsx`'s section element uses `bg-gradient-to-br from-dracula-bg/20 via-dracula-purple/10 to-dracula-bg/20`. The opacity modifiers (`/20`, `/10`) make the section nearly transparent, which means Hero blends into the CardMatrix canvas background instead of presenting as a distinct section. Replace this with a solid `bg-dracula-bg` background so Hero reads as the page's primary dark canvas.

The full list of text and interactive element classes in Hero are correct by name and will render correctly once Task 1 is complete — no changes are needed for those classes.

**Modify:**
- `frontend/src/components/landing/Hero.tsx`

**Change:**
Line 16: `className="min-h-screen pt-20 pb-16 bg-gradient-to-br from-dracula-bg/20 via-dracula-purple/10 to-dracula-bg/20 flex items-center"`

Replace the background portion with:
`className="min-h-screen pt-20 pb-16 bg-dracula-bg flex items-center"`

**Acceptance test:**
- Hero section has a solid dark background (`#282a36`) — no white or light-grey bleed
- Headline text gradient (purple → pink) is visible on the dark background
- Badge, subtitle paragraph, and CTA buttons all display with correct Dracula colors
- CardMatrix canvas symbols are visible only around the hero section edges (if page background allows) — not bleeding through the hero itself

**Depends on:** Task 1 (tokens must resolve for `bg-dracula-bg` to have a value)

---

## Task 3 — Fix BentoGrid section background for visual separation [frontend]

**Description:**
`BentoGrid.tsx`'s section uses `bg-gradient-to-b from-dracula-bg/80 to-dracula-bg/80`. With both gradient stops at the same color and 80% opacity, the section looks identical to Hero when tokens resolve. Replace with a slightly lighter solid background using `bg-dracula-current/20` (a 20% opacity overlay of `#44475a` over the page base) to create a subtle but legible section break.

The section header text (`text-dracula-comment`, `text-accent-400`) and BentoCard internals do not need changes — they will render correctly after Task 1.

**Modify:**
- `frontend/src/components/landing/BentoGrid.tsx`

**Change:**
Line 31: `className="py-20 md:py-32 bg-gradient-to-b from-dracula-bg/80 to-dracula-bg/80 px-4 sm:px-6 lg:px-8"`

Replace the background portion with:
`className="py-20 md:py-32 bg-dracula-current/20 px-4 sm:px-6 lg:px-8"`

**Acceptance test:**
- BentoGrid section is visually distinct from the Hero section above it when scrolling — a clear section break is perceptible
- BentoCard borders (`border-dracula-current/50`) are visible as subtle separators
- Each BentoCard's colored illustration area shows its distinct tint (cyan, purple, pink, orange, green) — the `/20` opacity illustrations are faint but visible
- Section title gradient (purple → pink) is visible

**Depends on:** Task 1

---

## Task 4 — Fix FinalCTA section background for visual separation [frontend]

**Description:**
`FinalCTA.tsx`'s section uses `bg-gradient-to-r from-dracula-bg/80 via-dracula-purple/40 to-dracula-bg/80`. Once tokens resolve (Task 1), this will show a purple-tinted gradient — which is the intended design. However, the `from-dracula-bg/80` end-stops remain nearly identical to the BentoGrid above it. Strengthen the gradient by removing the opacity modifier from the end-stops so the section reads as `from-dracula-bg via-dracula-purple/20 to-dracula-bg`. This gives FinalCTA a solid dark base with a subtle centered purple halo that is visually distinct from the neutral BentoGrid above.

Note: `text-dracula-fg`, `text-dracula-comment`, `text-accent-400`, `border-dracula-current`, and button classes will render correctly after Task 1 — no changes needed for those.

**Modify:**
- `frontend/src/components/landing/FinalCTA.tsx`

**Change:**
Line 14: `className="py-20 md:py-32 bg-gradient-to-r from-dracula-bg/80 via-dracula-purple/40 to-dracula-bg/80 px-4 sm:px-6 lg:px-8"`

Replace the background portion with:
`className="py-20 md:py-32 bg-gradient-to-r from-dracula-bg via-dracula-purple/20 to-dracula-bg px-4 sm:px-6 lg:px-8"`

**Acceptance test:**
- FinalCTA section is visually distinct from the BentoGrid above it — the subtle purple halo on the gradient is perceptible in the center of the section
- Body paragraph text is `#f8f8f2` (not black)
- The "Try Live Demo" outline button shows its `border-dracula-current` border in `#44475a`
- The Google sign-in CTA button renders with the purple-to-pink gradient background

**Depends on:** Task 1

---

## Task 5 — Verify Landing.tsx and App.tsx navbar composition [frontend]

**Description:**
Confirm that `LandingNavbar` is rendered exactly once when the landing route is active and that `Landing.tsx` does not (and should not) include it.

**Current state (verified):**
- `App.tsx` line 37: `{isLandingPage && <LandingNavbar />}` — renders the navbar conditionally
- `Landing.tsx`: does not import or render `LandingNavbar` — correct by design
- `LandingNavbar.tsx`: uses `text-dracula-fg`, `bg-dracula-bg/80`, `from-primary-400 to-accent-500`, and `bg-dracula-current` classes — all will resolve after Task 1

**Action:** Read both files and confirm the above. If the composition is already correct (which the current code confirms), no edit is required. If for any reason `LandingNavbar` is duplicated or missing, fix the composition.

**Modify:** None expected. If a discrepancy is found, modify `Landing.tsx` or `App.tsx` as appropriate.

**Acceptance test:**
- The DeckDex logo text in the navbar renders with the purple-to-pink gradient (not invisible/transparent)
- The navbar shows correctly above Hero content (z-50 positions it above the z-10 content wrapper)
- On scroll, the navbar gains `bg-dracula-bg/80 backdrop-blur-md border-b border-dracula-current/50` — the background tint and border become visible
- The mobile hamburger menu opens with `bg-dracula-bg/95` background — not transparent

**Depends on:** Task 1 (tokens must resolve for navbar Dracula classes to show)

---

## Task 6 — Audit Dashboard components for dracula/primary/accent class regressions [frontend]

**Description:**
The `@theme` migration in Task 1 rebuilds the entire CSS output. Although the Grep confirms that Dashboard-area components do not use any `dracula-*`, `primary-*`, or `accent-*` classes today, a final visual smoke test should confirm that no Dashboard functionality was broken by the CSS rebuild.

Specifically check:
1. The `body` dark-mode background in `index.css` is hardcoded as `background-color: #282a36` (not a class) — confirm it is unchanged after the `@theme` edit
2. The `.dark body` rule and `.card-symbol` rule in `index.css` are below the `@theme` block and remain intact
3. Run `npm run build` to confirm zero compiler errors
4. Run `npm run lint` to confirm zero new ESLint violations

If any dashboard component unexpectedly uses a now-resolved token in a way that creates a visual regression, document the class name and fix it. Based on the current codebase state, no fixes are expected.

**Modify:** None expected. If a regression is found, fix the affected component.

**Files to check:**
- `frontend/src/index.css` (verify existing rules below `@theme` are untouched)
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/components/CardTable.tsx` (if it exists)
- `frontend/src/components/Filters.tsx` (if it exists)

**Acceptance test:**
- `npm run build` exits 0
- `npm run lint` reports zero new violations
- Dashboard page renders without visual regressions in the browser (dark mode and light mode)
- No component in `src/components/` (non-landing) renders with unexpected purple, pink, or teal colors

**Depends on:** Task 1
