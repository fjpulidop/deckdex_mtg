# Tasks: hero-cardmatrix-background-fix

## Task 1 [frontend] — Remove opaque background from Hero section

**File:** `frontend/src/components/landing/Hero.tsx`

**Change:** On line 16, replace the `<section>` className string:

From:
```
"min-h-screen pt-20 pb-16 bg-dracula-bg flex items-center"
```

To:
```
"min-h-screen pt-20 pb-16 flex items-center bg-gradient-to-b from-dracula-bg/20 via-transparent to-transparent"
```

**Why:** `bg-dracula-bg` resolves to `background-color: #282a36` at 100% opacity, painting a solid rectangle over `min-h-screen` and permanently occluding the `CardMatrix` canvas below it. The replacement gradient starts at 20% Dracula background opacity at the top (smooth transition from the navbar) and fades to fully transparent, allowing the canvas to show through while maintaining text legibility. The `body { background-color: #282a36 }` rule in `index.css` provides the solid dark fallback.

**Acceptance criteria:**
- The `<section>` element in `Hero.tsx` does NOT contain `bg-dracula-bg` as a class.
- The `<section>` element does contain a gradient class with opacity modifier `from-dracula-bg/20`.
- The Hero headline, subtitle, badge, and CTA buttons remain legible against the dark body background.
- No white or unexpected color flash is visible when loading `/`.

**Dependencies:** None.

---

## Task 2 [frontend] — Update FinalCTA gradient to use opacity-modified stops

**File:** `frontend/src/components/landing/FinalCTA.tsx`

**Change:** On line 14, replace the `<section>` className string:

From:
```
"py-20 md:py-32 bg-gradient-to-r from-dracula-bg via-dracula-purple/20 to-dracula-bg px-4 sm:px-6 lg:px-8"
```

To:
```
"py-20 md:py-32 bg-gradient-to-r from-dracula-bg/80 via-dracula-purple/20 to-dracula-bg/80 px-4 sm:px-6 lg:px-8"
```

**Why:** `from-dracula-bg` and `to-dracula-bg` are fully opaque. The left and right ~25% of this section block the canvas. Changing to `/80` (80% opacity) allows ~20% of the canvas to bleed through at the edges while preserving the visual weight and intentionality of the CTA band. The center (`via-dracula-purple/20`) is already semi-transparent and unchanged.

**Acceptance criteria:**
- The `<section>` in `FinalCTA.tsx` uses `from-dracula-bg/80` and `to-dracula-bg/80` (not the unmodified `from-dracula-bg` / `to-dracula-bg`).
- The FinalCTA section retains its horizontal purple gradient accent in the center.
- The CardMatrix animation is partially visible at the left and right edges of the FinalCTA section.

**Dependencies:** Task 1 (recommended sequential order — both are independent but logical to do together).

---

## Task 3 [test] — Verify no regression in landing component tests

**Files to check:**
- `frontend/src/components/landing/__tests__/` (check all test files)
- `frontend/src/components/backgrounds/__tests__/dracula-theme.test.tsx`

**Action:** Run `npm run lint` and `npm test` (or the project's equivalent test runner for the frontend) from `frontend/`. Confirm:
1. No test assertions reference the removed `bg-dracula-bg` class on Hero's `<section>`.
2. The `dracula-theme.test.tsx` test suite passes without modification.
3. No TypeScript errors introduced by the class changes (these are string literals, so no type impact expected).

**Acceptance criteria:**
- `npm run lint` exits with code 0.
- All existing frontend tests pass.
- If any test asserts the old `bg-dracula-bg` class on the Hero section, update that assertion to match the new gradient class.

**Dependencies:** Tasks 1 and 2 must be complete before running verification.

---

## Summary

| # | Layer | File | Change |
|---|---|---|---|
| 1 | frontend | `Hero.tsx` line 16 | `bg-dracula-bg` → gradient with `/20` opacity |
| 2 | frontend | `FinalCTA.tsx` line 14 | `from-dracula-bg` and `to-dracula-bg` → add `/80` modifier |
| 3 | test | landing `__tests__/`, backgrounds `__tests__/` | Verify no regressions |

**No changes required:** `BentoGrid.tsx` (already uses `bg-dracula-current/20`), `Footer.tsx` (already uses `bg-dracula-bg/80`), `Landing.tsx` (no background class at all), `CardMatrix.tsx`, `App.tsx`, any backend file.
