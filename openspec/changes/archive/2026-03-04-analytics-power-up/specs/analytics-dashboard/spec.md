## ADDED Requirements

### Requirement: Modular analytics components
All analytics visualizations (KPIs, charts) SHALL be implemented as independent, reusable React components under `frontend/src/components/analytics/`. Each component SHALL receive data and configuration via props and SHALL NOT perform its own API calls. A barrel export (`index.ts`) SHALL re-export all public components.

#### Scenario: Component reuse in different context
- **WHEN** a parent page (Analytics or future DeckStats) renders a chart component with data props
- **THEN** the component renders the visualization using only the provided props, without fetching data itself

#### Scenario: Barrel export availability
- **WHEN** a consuming module imports from `components/analytics`
- **THEN** all public chart components (KpiCards, ColorRadar, ManaCurve, RarityChart, TopSetsChart, ChartCard) are available

### Requirement: WUBRG radar chart for color identity
The color identity chart SHALL use a Recharts `RadarChart` with 5 axes corresponding to W, U, B, R, G. Multi-color cards SHALL distribute their count across each constituent color axis (e.g., a "WU" card adds +1 to both W and U). Colorless cards SHALL be shown as a separate count label, not as a radar axis. Each axis SHALL display a percentage label. The radar shape SHALL have a minimum baseline so the shape remains visible even with heavily skewed distributions.

#### Scenario: Mono-color collection renders spike
- **WHEN** the collection is 90% Red cards
- **THEN** the radar shows a prominent spike toward R with a visible minimum on other axes

#### Scenario: Multi-color card distribution
- **WHEN** a card has color identity "WUB"
- **THEN** its count is added to W, U, and B axes equally

#### Scenario: Colorless cards display
- **WHEN** the collection contains colorless cards
- **THEN** a "Colorless: N" label is shown outside the radar (not as a 6th axis)

#### Scenario: Drill-down on radar click
- **WHEN** user clicks on a radar axis point or label
- **THEN** the parent's onSliceClick handler is called with the corresponding single-color code (e.g., "W")

### Requirement: Area chart mana curve with average CMC
The mana curve chart SHALL use a Recharts `AreaChart` with a vertical gradient fill (primary color to transparent). An "Avg CMC" badge SHALL be displayed in the top-right corner of the chart card showing the weighted average converted mana cost rounded to one decimal. The X-axis SHALL display mana cost values (0–6, 7+).

#### Scenario: Area chart renders with gradient
- **WHEN** CMC data is loaded
- **THEN** the chart renders as a filled area with a top-to-bottom gradient, not as discrete bars

#### Scenario: Average CMC calculation
- **WHEN** CMC data contains buckets {0: 10, 1: 30, 2: 50, 3: 40, 4: 20, 5: 10, 6: 5, "7+": 3}
- **THEN** the average CMC badge shows the weighted mean (treating "7+" as 7, excluding "Unknown")

#### Scenario: Drill-down preserved
- **WHEN** user clicks on a data point in the area chart
- **THEN** the parent's onBarClick handler is called with the CMC bucket string

### Requirement: Count-up animation on KPI values
All numeric KPI values SHALL animate from 0 to their target value on mount using a custom `useCountUp` hook. The animation SHALL use ease-out timing and complete within ~800ms. Currency values SHALL animate the number and format as currency at each frame.

#### Scenario: KPI mount animation
- **WHEN** the KPI cards mount with stats data available
- **THEN** each number animates from 0 to its target value over approximately 800ms

#### Scenario: KPI value update
- **WHEN** a drill-down filter changes and new stats load
- **THEN** the numbers animate from their previous value to the new value

### Requirement: Enhanced KPI card showing mythic count
The KPI row SHALL display 4 cards: Total Cards, Total Value, Mythic Rares count, and Average Price. The Mythic Rares count SHALL be derived from the rarity distribution data (count where rarity is "mythic" or "mythic rare"). Each KPI card SHALL display a contextual icon or color accent matching its meaning.

#### Scenario: Mythic count display
- **WHEN** rarity data includes entries with rarity "mythic" (count: 8) and "mythic rare" (count: 4)
- **THEN** the Mythic Rares KPI shows 12

#### Scenario: Zero mythics
- **WHEN** the collection has no mythic rarity cards
- **THEN** the Mythic Rares KPI shows 0

## MODIFIED Requirements

### Requirement: Charts (all clickable → set drill-down context)
Rarity (count per rarity); color identity via WUBRG radar chart (count per color, multi-color distributed); CMC via area chart with gradient (buckets 0,1,2…7+); sets (top N by count). Backend aggregations; refetch all with new context on click. All four drill-down dimensions (rarity, color_identity, cmc, set_name) SHALL be sent as query parameters to all analytics and stats endpoints.

#### Scenario: Rarity drill-down
- **WHEN** user clicks a rarity bar
- **THEN** all charts and KPIs refetch with the rarity filter applied

#### Scenario: Color drill-down from radar
- **WHEN** user clicks a color axis on the radar chart
- **THEN** all charts and KPIs refetch with the color_identity filter applied

#### Scenario: CMC drill-down from area chart
- **WHEN** user clicks a data point on the mana curve area chart
- **THEN** all charts and KPIs refetch with the cmc filter applied

#### Scenario: Set drill-down
- **WHEN** user clicks a set bar
- **THEN** all charts and KPIs refetch with the set_name filter applied
