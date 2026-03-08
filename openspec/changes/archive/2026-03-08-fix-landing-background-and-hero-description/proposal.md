## Why

The landing page has two visual defects that undermine its first impression. First, the CardMatrix animated mana-symbol background is completely invisible because the `Landing` wrapper (`bg-gradient-to-b from-slate-900/90 via-purple-900/20 to-slate-900/90`) and the `Hero` section (`bg-gradient-to-br from-slate-900/80 via-purple-900/60 to-slate-900/80`) stack opaque gradients on top of the canvas, which sits at `z-0`. Second, the Hero right column renders a static `dashboard-preview.png` image that does not exist in production, causing a silent 404 and showing nothing — a bad first impression for any visitor.

## What Changes

- **Landing.tsx**: Remove the solid `bg-gradient-to-b` from the content wrapper. Replace with a translucent or zero-opacity background so the CardMatrix canvas at `z-0` shows through. Content stays at `z-10` (already set via `relative z-10`).
- **Hero.tsx**: Remove the `bg-gradient-to-br` from the `<section>` element (or make it transparent) so the canvas is visible through the Hero as well. Replace the static `<img src="/dashboard-preview.png">` right column with an inline styled description card that presents what DeckDex does in both English and Spanish, side by side, using the existing `useTranslation` hook.
- **en.json / es.json**: Add new i18n keys under `hero.descCard` for the bilingual description card content (title, feature bullets, tagline).

## Capabilities

### New Capabilities

- None

### Modified Capabilities

- `landing-page`: The requirement "Hero section shows real dashboard screenshot" is being replaced. The Hero SHALL display an inline bilingual description card instead of a static image. The requirement about CardMatrix visibility ("the CardMatrix animated background SHALL be visible behind all landing page sections") is already in the spec but was never correctly implemented — this change corrects the implementation.
- `animated-backgrounds`: No requirement changes; the spec already mandates CardMatrix visibility. Implementation correction only (no delta spec needed).
- `i18n`: New translation keys are added under `hero.descCard` in both locale files. This is an additive change to locale coverage, not a requirement change.

## Non-goals

- No changes to CardMatrix animation logic, speed, opacity math, or any canvas rendering code.
- No changes to any other landing section (BentoGrid, FinalCTA, Footer, LandingNavbar).
- No backend changes.
- No new routes or API endpoints.
- No changes to AetherParticles or app-page backgrounds.
- No server-side rendering or static-site generation concern.

## Impact

- **frontend/src/pages/Landing.tsx** — remove opaque background classes from the wrapper div
- **frontend/src/components/landing/Hero.tsx** — remove opaque background class from `<section>`, replace `<img>` right column with `AppDescriptionCard` inline component
- **frontend/src/locales/en.json** — add `hero.descCard` keys
- **frontend/src/locales/es.json** — add `hero.descCard` keys (Spanish translations)
- No other files affected
