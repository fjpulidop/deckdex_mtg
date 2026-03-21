# Proposal: Multi-Deck Comparison Tool

**Change name:** `multi-deck-comparison-tool`
**GitHub Issue:** #131
**Status:** Proposed
**Priority:** Medium
**Effort:** Medium

---

## Feature Rationale

MTG players who maintain multiple decks face a recurring pain: they cannot easily tell at a glance which decks share valuable staples, how their mana curves differ, or which deck packs the most total value. Without a comparison tool, the only option is to open each deck detail modal one at a time, memorise the numbers, and manually compare — a slow, error-prone process.

This feature adds a modal that accepts 2–4 deck selections and renders side-by-side stat panels, letting the player answer "do I have enough Lightning Bolts to put them in both decks?" in seconds rather than minutes.

**Inspiration:** EDHREC deck comparison, Archidekt multi-deck tools.

---

## User Story

> As an **MTG Player (Alex)**, I want to **compare power levels, mana curves, and card overlap across multiple decks at once** so that **I can balance my collection and identify staples I could share**.

### Persona score
Alex (MTG Player): **4/5**

---

## Acceptance Criteria

1. A "Compare Decks" button is visible on the Deck Builder page whenever two or more decks exist.
2. Clicking the button opens the `DeckComparisonModal`.
3. The modal contains a `DeckMultiSelect` component that lets the user pick between 2 and 4 decks (checkboxes or toggle buttons; cannot select fewer than 2 or more than 4).
4. After selection the modal displays a results section with one column per selected deck showing:
   - Deck name and total card value (EUR)
   - Mana curve bar chart (CMC 0–7+ buckets)
   - Color distribution (W/U/B/R/G/Colorless counts)
   - Creature-to-instant ratio (creature count : instant count, e.g. "24:6")
5. Below the per-deck columns, an "Overlapping Cards" section lists every card name that appears in two or more of the selected decks, with a badge showing which decks contain it (e.g. "Deck A, Deck C").
6. Cards that appear in multiple selected decks are highlighted with a coloured background in the Overlapping Cards list.
7. The compare endpoint is `GET /api/decks/compare?ids=1,2,3` — it returns per-deck aggregated stats and the overlap card list.
8. The endpoint returns 400 if fewer than 2 or more than 4 IDs are provided.
9. The endpoint returns 404 if any of the requested deck IDs do not exist or do not belong to the authenticated user.
10. The endpoint returns 501 when Postgres is not configured.
11. All user-facing strings are declared in `en.json` and `es.json`.
12. The modal is accessible: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus-trap, Escape-to-close.
13. The feature is only active when decks are available (Postgres configured); it is hidden or gracefully disabled otherwise.

---

## Out of Scope

- Commander-specific power-level scoring (reserved for a future spec).
- Exporting the comparison as an image or PDF.
- Sharing comparison links between users.
