## Why

The `CardMatrix` canvas animation (`fixed inset-0 z-0`) is rendered on the landing page but is permanently occluded by the Hero section's solid `bg-dracula-bg` Tailwind class on its `<section>` element. The canvas animates correctly but is never visible to users. This fix is a small, self-contained frontend correction that restores visual fidelity to the already-specified requirement in `openspec/specs/landing-page/spec.md` (the "CardMatrix animated background visible through landing sections" requirement, lines 71–87).

## What Changes

- **Remove** the `bg-dracula-bg` class from the `<section>` element in `frontend/src/components/landing/Hero.tsx` (line 16). Replace with a translucent tint (`bg-dracula-bg/10 bg-gradient-to-b from-dracula-bg/20 via-transparent to-transparent`) that maintains text legibility while making the canvas visible.
- **Audit** `BentoGrid`, `FinalCTA`, and `Footer` for any opaque background classes that may also block the canvas. Update where appropriate.
- No backend changes, no API changes, no new components.

## Capabilities

### New Capabilities

_(none — this fix implements an already-specified requirement)_

### Modified Capabilities

- `landing-page`: The "CardMatrix animated background visible through landing sections" requirement (already in spec) is currently violated by the implementation. The spec wording is correct; the code is wrong. A delta spec tightens the wording to clarify the exact opacity constraint that was missing precision.
- `animated-backgrounds`: No requirement changes needed — the spec already says the canvas SHALL be visible behind page content.

## Impact

- **Files changed**: `frontend/src/components/landing/Hero.tsx` (1 line), possibly `BentoGrid.tsx`, `FinalCTA.tsx`, `Footer.tsx` (audit-dependent).
- **No API surface changes**.
- **No backend changes**.
- **No new dependencies**.
- **Test impact**: Existing `dracula-theme.test.tsx` in `frontend/src/components/backgrounds/__tests__/` may assert Hero class names — verify no regression.

## Non-goals

- This change does NOT redesign the Hero layout or typography.
- This change does NOT alter `CardMatrix` animation logic, frame rate, or z-index stacking.
- This change does NOT affect the `AetherParticles` background used on authenticated pages.
- This change does NOT modify any backend, database, or API code.
