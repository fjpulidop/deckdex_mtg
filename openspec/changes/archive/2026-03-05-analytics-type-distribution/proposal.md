# Proposal: Type-Line Distribution Chart for Analytics Dashboard

## Date
2026-03-05

## Status
Proposed

## Problem

The Analytics dashboard currently visualises four dimensions of a collection:
Rarity, Color Identity, Mana Curve (CMC), and Top Sets. A critical dimension is
absent: **card type composition**.

Knowing the split between Creatures, Instants, Sorceries, Enchantments,
Artifacts, Planeswalkers, Lands, and Other gives players actionable information
about their collection's playability profile. A collection heavy on Lands but
light on Creatures reads very differently from the reverse. This dimension is
also the most obvious anchor for deck-building decisions.

The data is already present: every card stored in the collection has a
`type_line` field (e.g. `"Legendary Creature — Dragon"`, `"Instant"`,
`"Artifact — Equipment"`). No new data ingestion or Scryfall calls are required.

## Proposed Solution

Add a fifth analytics chart — **Type Distribution** — with full parity with the
four existing charts:

1. **Backend endpoint** `GET /api/analytics/type` that aggregates cards by
   primary type extracted from `type_line`, using the same filter parameter
   signature as all existing analytics endpoints.

2. **Frontend component** `TypeDistributionChart` — a horizontal bar chart
   (matching `TopSetsChart` layout) with semantic per-type colour coding. Types
   sorted by descending card count.

3. **Drill-down integration** in `Analytics.tsx`: clicking a type bar sets a
   `type_line` drill-down dimension that is forwarded to every analytics and
   stats query, consistent with how `rarity`, `color_identity`, `cmc`, and
   `set_name` already work.

4. **i18n keys** added to `en.json` and `es.json`.

5. **API client** method `getAnalyticsType` added to `api/client.ts`.

## Out of Scope

- Subtypes (e.g. `Dragon`, `Equipment`) — aggregating at the supertype level is
  sufficient for the initial version.
- Dual-faced cards with two types — the primary face's type line is used.
- Changing the existing `type_` / `type` filter parameter in `filter_collection`
  — this proposal adds a new drill-down dimension (`type_line`) that routes
  through the existing `type_` parameter.

## Expected Outcome

Users can look at the Analytics page, see a chart showing e.g. "Creatures 42%,
Lands 18%, Instants 12% …", click on "Creature" to cross-filter all other
charts, and see rarity/color/CMC breakdowns for their creatures only.
