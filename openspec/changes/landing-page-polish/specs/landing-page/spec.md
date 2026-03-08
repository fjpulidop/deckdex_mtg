# Delta Spec: Landing Page Polish

Base spec: `openspec/specs/landing-page/spec.md`

This delta refines existing requirements with implementation-level detail. No new top-level requirements are added. All scenarios below are additive clarifications to the base spec.

---

## Requirement: BentoGrid cards display styled visual content (refined)

Extends the base requirement of the same name.

### Scenario: Illustration icon is visually distinct per card

- **GIVEN** the BentoGrid section is rendered
- **WHEN** a visitor views a feature card at rest (no hover)
- **THEN** the illustration icon SHALL be rendered at a minimum opacity of 40% (`text-white/40` equivalent)
- **AND** the icon SHALL carry a color tint matching the card's gradient color family (e.g., blue card uses a blue icon tint)
- **AND** on hover the icon SHALL increase in opacity to at least 60%

### Scenario: No raw dimension text in any card

- **GIVEN** the BentoGrid section is rendered
- **THEN** no text matching the pattern `\d+x\d+px` (e.g., "600x500px") SHALL appear in the DOM
- **AND** size information SHALL be expressed only via CSS layout classes, never as visible text content

---

## Requirement: Hero image fallback (test coverage)

Extends the base scenario "Hero image fallback" from the base spec.

### Scenario: Hero image fallback activates on error (verified by test)

- **GIVEN** the Hero section is rendered
- **AND** the browser cannot load `/dashboard-preview.png`
- **WHEN** the `<img>` element fires an `error` event
- **THEN** the `<img>` element SHALL have `display: none` applied
- **AND** the gradient fallback `<div>` sibling SHALL have `display: flex` applied
- **AND** no JavaScript error SHALL be thrown

---

## Requirement: Footer rendered on landing page (test coverage)

Extends the base scenario "Footer visible at bottom of landing" from the base spec.

### Scenario: Footer renders when visitor is unauthenticated (verified by test)

- **GIVEN** the auth context reports `isAuthenticated: false`
- **WHEN** the Footer component is rendered
- **THEN** the `<footer>` element SHALL be present in the DOM
- **AND** the copyright text SHALL be visible (contains current year)
- **AND** GitHub, Twitter, and Discord social links SHALL be present with correct `aria-label` attributes

### Scenario: Footer renders when visitor is authenticated (verified by test)

- **GIVEN** the auth context reports `isAuthenticated: true`
- **WHEN** the Footer component is rendered
- **THEN** the `<footer>` element SHALL be present in the DOM
- **AND** the copyright text SHALL be visible (contains current year)
- **AND** GitHub, Twitter, and Discord social links SHALL be present with correct `aria-label` attributes

### Note on auth-independence

The Footer component does not conditionally render based on auth state — it is identical in both scenarios. These tests exist to guard against future regressions if auth-dependent logic is added and to formally verify the Footer renders without error in both page load contexts.
