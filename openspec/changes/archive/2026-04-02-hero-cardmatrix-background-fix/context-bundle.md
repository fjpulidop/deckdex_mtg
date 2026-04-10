# Context Bundle: hero-cardmatrix-background-fix

This file captures the exact current state of all relevant code, class strings, and stacking context for the developer implementing this change.

---

## Z-Index Hierarchy (current)

```
<canvas class="pointer-events-none fixed inset-0 z-0" aria-hidden="true">  ← CardMatrix
  (rendered in App.tsx at the fragment root, sibling to Landing)

<div class="relative z-10 min-h-screen">                                    ← Landing.tsx wrapper
  <section class="min-h-screen pt-20 pb-16 bg-dracula-bg flex items-center">  ← Hero.tsx (BUG HERE)
  <section class="py-20 md:py-32 bg-dracula-current/20 ...">                  ← BentoGrid.tsx (OK)
  <section class="py-20 md:py-32 bg-gradient-to-r from-dracula-bg via-dracula-purple/20 to-dracula-bg ...">  ← FinalCTA.tsx (partially opaque)
  <footer class="bg-dracula-bg/80 border-t border-dracula-current ...">       ← Footer.tsx (OK)
```

---

## Exact Current Class Strings Per File

### `frontend/src/components/landing/Hero.tsx` — Line 16

```tsx
<section className="min-h-screen pt-20 pb-16 bg-dracula-bg flex items-center">
```

**Problem:** `bg-dracula-bg` = `background-color: #282a36` at 100% opacity. Full occluding rectangle.

**Fix:** Replace with:
```tsx
<section className="min-h-screen pt-20 pb-16 flex items-center bg-gradient-to-b from-dracula-bg/20 via-transparent to-transparent">
```

---

### `frontend/src/components/landing/BentoGrid.tsx` — Line 31

```tsx
<section id="features" className="py-20 md:py-32 bg-dracula-current/20 px-4 sm:px-6 lg:px-8">
```

`bg-dracula-current/20` = `#44475a` at 20% opacity. **Semi-transparent. No change required.**

---

### `frontend/src/components/landing/FinalCTA.tsx` — Line 14

```tsx
<section className="py-20 md:py-32 bg-gradient-to-r from-dracula-bg via-dracula-purple/20 to-dracula-bg px-4 sm:px-6 lg:px-8">
```

`from-dracula-bg` and `to-dracula-bg` = `#282a36` at 100% opacity on the left/right edges.

**Fix:** Replace with:
```tsx
<section className="py-20 md:py-32 bg-gradient-to-r from-dracula-bg/80 via-dracula-purple/20 to-dracula-bg/80 px-4 sm:px-6 lg:px-8">
```

---

### `frontend/src/components/landing/Footer.tsx` — Line 7

```tsx
<footer className="bg-dracula-bg/80 border-t border-dracula-current px-4 sm:px-6 lg:px-8">
```

`bg-dracula-bg/80` = `#282a36` at 80% opacity. **Semi-transparent. No change required.**

---

### `frontend/src/pages/Landing.tsx` — Line 8

```tsx
<div className="relative z-10 min-h-screen">
```

No background class. **No change required.**

---

## Body Background (Solid Fallback)

From `frontend/src/index.css` lines 32–36:

```css
body {
  margin: 0;
  min-height: 100vh;
  background-color: #282a36;
}
```

This is the Dracula background color — identical to what `bg-dracula-bg` would paint. Removing `bg-dracula-bg` from the Hero section causes no visual change in background color because the body already provides it. The canvas (which paints above the body but below the section) becomes visible through the transparent section.

---

## Dracula Theme Token Reference

From `frontend/src/index.css` `@theme` block:

| Token | Hex Value |
|---|---|
| `--color-dracula-bg` | `#282a36` |
| `--color-dracula-current` | `#44475a` |
| `--color-dracula-fg` | `#f8f8f2` |
| `--color-dracula-comment` | `#6272a4` |
| `--color-dracula-purple` | `#bd93f9` |
| `--color-dracula-pink` | `#ff79c6` |

---

## CardMatrix Component Location

- **File:** `frontend/src/components/backgrounds/CardMatrix.tsx`
- **Mount point:** `App.tsx` line 37: `{isLandingPage && <CardMatrix />}`
- **Canvas class:** `"pointer-events-none fixed inset-0 z-0"`
- **Reduced motion:** handled by `useReducedMotion()` from `frontend/src/components/backgrounds/useReducedMotion.ts`
  - When `prefers-reduced-motion: reduce` → renders one static frame, no animation loop
  - When not set → 30 FPS animation loop via `requestAnimationFrame`
- **Visibility pause:** Canvas animation pauses via `visibilitychange` event when tab is hidden

---

## Existing Tests

- `frontend/src/components/backgrounds/__tests__/dracula-theme.test.tsx` — tests CardMatrix/AetherParticles visual appearance; does NOT assert Hero class names
- `frontend/src/components/backgrounds/__tests__/constants.test.ts` — tests mana symbol constants; unrelated to backgrounds
- `frontend/src/components/landing/__tests__/` — exists but is empty (no test files found at audit time)

No existing test asserts the `bg-dracula-bg` class on `Hero.tsx`'s `<section>` element. No test changes are expected.
