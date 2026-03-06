## Why

The analytics dashboard is functional but generic — it could belong to any app. MTG players expect visual language they recognize (WUBRG pentagon, mana symbols, rarity iconography). The current charts are static Recharts defaults with no animations, no MTG personality, and KPIs that show numbers without context. Making the analytics components modular also enables reuse in the future deck stats view.

## What Changes

- **Modular chart components**: Extract all charts and KPIs into reusable components under `frontend/src/components/analytics/` so they can be consumed by both the Analytics page and future deck detail views.
- **WUBRG Radar Chart**: Replace the generic donut for color identity with a radar/pentagon chart mapping to the 5 MTG colors — instantly recognizable to any player.
- **Enhanced Mana Curve**: Replace bar chart with area chart using gradient fill, add average CMC badge, and use mana-symbol-styled X-axis labels.
- **Richer KPIs**: Add mythic count and most valuable card to the KPI row, with count-up number animations on load.
- **Count-up animations**: All numeric KPIs animate from 0 to their value on mount for a fluid, polished feel.

## Non-goals

- No new backend endpoints in this change — reuse existing analytics + stats APIs.
- No new npm dependencies beyond what Recharts already provides (Radar chart is built-in).
- No deck stats page — just make components reusable for it later.
- No historical data/sparklines (would require new backend tracking).

## Capabilities

### New Capabilities

_None — this is a frontend-only enhancement of existing capability._

### Modified Capabilities

- `analytics-dashboard`: New component architecture (modular), radar chart for color identity, area chart for mana curve, enhanced KPIs with count-up animations and richer data display.

## Impact

- **Frontend components**: New `frontend/src/components/analytics/` directory with extracted chart components.
- **Analytics page**: Refactored to consume modular components instead of inline chart code.
- **No backend changes**: All data comes from existing endpoints.
- **No API changes**: Same contracts, same query params.
