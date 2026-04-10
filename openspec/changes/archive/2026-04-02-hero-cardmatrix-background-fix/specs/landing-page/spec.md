# Delta Spec: landing-page — hero-cardmatrix-background-fix

This delta refines the existing "CardMatrix animated background visible through landing sections" requirement to add precise, implementable constraints that were missing from the original wording. No requirements are removed or weakened.

---

## Refined Requirement: CardMatrix animated background visible through landing sections

The CardMatrix animated canvas background SHALL be visually perceptible behind the Hero, BentoGrid, FinalCTA, and Footer sections of the landing page. No landing section element SHALL carry a fully-opaque background color that occludes the canvas.

### Scenario: Hero section uses a transparent or semi-transparent background

**Previously (vague):** "Hero `<section>` element's background gradient opacity SHALL be at most 20% on slate and 10% on purple."

**Refined:**
- **WHEN** a visitor loads the landing page `/`
- **THEN** the Hero `<section>` element SHALL NOT carry any Tailwind background class that resolves to a solid color at 100% opacity (e.g., `bg-dracula-bg` without an opacity modifier)
- **AND** if a background tint is applied, it SHALL use an opacity modifier of `/20` or lower (e.g., `bg-dracula-bg/20` or a gradient from `dracula-bg/20` to `transparent`)
- **AND** the falling mana symbols from the CardMatrix canvas SHALL be visually perceptible through the Hero section background

### Scenario: FinalCTA gradient uses opacity-modified stops

- **WHEN** a visitor views the FinalCTA section
- **THEN** the gradient background on the FinalCTA `<section>` SHALL use opacity-modified Tailwind color stops on all solid-color gradient steps (e.g., `from-dracula-bg/80`, `to-dracula-bg/80`)
- **AND** no gradient stop SHALL resolve to a fully-opaque solid color

### Scenario: BentoGrid and Footer already comply

- **WHEN** a visitor views the BentoGrid or Footer sections
- **THEN** the BentoGrid `<section>` background SHALL use `bg-dracula-current/20` (20% opacity) or equivalent semi-transparent value — no change required
- **AND** the Footer `<footer>` background SHALL use `bg-dracula-bg/80` (80% opacity) or equivalent — no change required

### Scenario: Body background provides solid fallback

- **WHEN** all landing section backgrounds are semi-transparent or transparent
- **THEN** the `body` element's `background-color: #282a36` (set in `index.css`) SHALL serve as the solid dark fallback
- **AND** no white flash or unexpected color SHALL appear in the absence of a section-level solid background

### Scenario: Canvas visible under reduced motion

- **WHEN** `prefers-reduced-motion: reduce` is active
- **THEN** the CardMatrix SHALL render a single static frame (unchanged from existing behavior)
- **AND** the static frame SHALL still be visible through the transparent Hero section background

---

## No changes to other landing-page requirements

All other requirements in `openspec/specs/landing-page/spec.md` remain unchanged:
- Bilingual Hero description card
- Live demo CTA in Hero and FinalCTA
- Footer rendered on landing page
- BentoGrid cards display styled visual content
- GitHub links use correct repository URL
- Locale keys for Hero description card
- No dead code in landing components
- No debug artifacts in public directory
