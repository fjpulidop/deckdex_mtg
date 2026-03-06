# Delta Spec: Type-Line Distribution Chart

Target spec file: `openspec/specs/analytics-dashboard/spec.md`

## Additions

### Requirement: Type-line distribution chart

The analytics dashboard SHALL include a Type Distribution chart showing the
card count per primary MTG type (Creature, Land, Artifact, Enchantment,
Planeswalker, Instant, Sorcery, Battle, Other) derived from the `type_line`
field.

The chart SHALL be implemented as a horizontal bar chart (Recharts `BarChart`
with `layout="vertical"`) using semantic per-type colours defined in
`TYPE_COLORS` in `constants.ts`. Bars SHALL be sorted by descending count.

A backend endpoint `GET /api/analytics/type` SHALL aggregate primary types
using the priority extraction rule: take the first word from the portion of
`type_line` before the em-dash `—` that matches, in priority order:
Creature > Land > Artifact > Enchantment > Planeswalker > Instant > Sorcery >
Battle. Non-matching type lines SHALL be counted as "Other".

The endpoint SHALL accept the same filter query parameters as all other
analytics endpoints: `search`, `rarity`, `type` (alias), `set_name`,
`price_min`, `price_max`, `color_identity`, `cmc`.

#### Scenario: Standard type extraction

- WHEN a card has `type_line = "Legendary Creature — Dragon"`
- THEN it is counted under the "Creature" bucket

#### Scenario: Dual-type card uses priority order

- WHEN a card has `type_line = "Artifact Creature — Golem"`
- THEN it is counted under "Creature" (Creature ranks above Artifact)

#### Scenario: Land extraction

- WHEN a card has `type_line = "Basic Land — Forest"`
- THEN it is counted under "Land"

#### Scenario: Unknown type falls to Other

- WHEN a card has `type_line = ""` or an unrecognised value
- THEN it is counted under "Other"

### Requirement: type_line as a drill-down dimension

The analytics page drill-down state SHALL support a `type_line` dimension
alongside the existing `rarity`, `color_identity`, `cmc`, and `set_name`
dimensions.

When `type_line` drill-down is active, it SHALL be forwarded to all analytics
endpoints and the stats endpoint as the `type` query parameter, consistent
with the existing `type_` filter accepted by `filter_collection`.

An active `type_line` drill-down SHALL be displayed as a removable chip in
the filter bar with label `"Type: {value}"`.

#### Scenario: Type drill-down cross-filters all charts

- WHEN a user clicks the "Creature" bar in the Type Distribution chart
- THEN all other charts (Rarity, Color Identity, Mana Curve, Top Sets) refetch
  with `type=Creature` and show data for creatures only
- AND the KPI cards update to reflect the creature-only totals

#### Scenario: Clicking the same bar twice clears the filter

- WHEN a user clicks the "Creature" bar while `type_line = "Creature"` is
  already active
- THEN the type_line drill-down is cleared and all charts return to unfiltered
  data

### Update: Barrel export includes TypeDistributionChart

The barrel export at `frontend/src/components/analytics/index.ts` SHALL
re-export `TypeDistributionChart` and `TypeEntry`.

### Update: API client includes getAnalyticsType

The `api` object in `frontend/src/api/client.ts` SHALL include a
`getAnalyticsType` method with the same signature pattern as
`getAnalyticsRarity`, `getAnalyticsColorIdentity`, `getAnalyticsCmc`, and
`getAnalyticsSets`.

### Update: Chart grid layout

The Analytics page chart grid SHALL accommodate five charts. The Type
Distribution chart SHALL span the full row width (`lg:col-span-2`) to give
the horizontal bar chart adequate label space.
