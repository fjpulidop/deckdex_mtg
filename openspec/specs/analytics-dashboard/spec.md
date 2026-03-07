# Analytics Dashboard (beta)

Metrics, charts, and drill-down over the collection. Beta; no chart library mandated; consistent with rest of dashboard.

### Requirements (compact)

- **KPIs:** Total card count and total value (optional avg) for current filter/drill-down; from backend with same params as charts (search, rarity, type, set_name, price_min, price_max, color_identity, cmc + drill slice). Update when user clicks chart segment. All filter parameters SHALL be passed using keyword arguments to `filter_collection`.
- **Charts (all clickable → set drill-down context):** Rarity (count per rarity); color identity via WUBRG radar chart (count per color, multi-color distributed); CMC via area chart with gradient (buckets 0,1,2…7+); sets (top N by count). Backend aggregations; refetch all with new context on click. All four drill-down dimensions (rarity, color_identity, cmc, set_name) SHALL be sent as query parameters to all analytics and stats endpoints.
- **Context:** "View all" / Clear resets drill-down to full collection; active context visible (e.g. chip).
- **States:** Loading (skeletons); empty (no cards in context → message, no misleading zero charts); error + retry.
- **Visual:** Palette and typography aligned with app (light/dark); labels/legends so meaning clear without color alone.

### Requirement: CMC filter in shared filter module
The `filter_collection` function SHALL accept an optional `cmc` parameter for filtering cards by converted mana cost bucket (0-6 exact, "7+" for >=7, "Unknown" for null/unparseable).

### Requirement: Color identity drill-down query parameter
All analytics endpoints and the stats endpoint SHALL accept an optional `color_identity` query parameter and pass it through to `filter_collection`.

### Requirement: CMC drill-down query parameter
All analytics endpoints and the stats endpoint SHALL accept an optional `cmc` query parameter and pass it through to `filter_collection`.

### Requirement: Backend filter calls use keyword arguments
All calls to `filter_collection` from analytics and stats routes SHALL use keyword arguments to prevent positional argument misalignment.

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

### Requirement: Type-line distribution chart

The analytics dashboard SHALL include a Type Distribution chart showing the card count per primary MTG type (Creature, Land, Artifact, Enchantment, Planeswalker, Instant, Sorcery, Battle, Other) derived from the `type_line` field.

The chart SHALL be implemented as a horizontal bar chart (Recharts `BarChart` with `layout="vertical"`) using semantic per-type colours defined in `TYPE_COLORS` in `constants.ts`. Bars SHALL be sorted by descending count.

A backend endpoint `GET /api/analytics/type` SHALL aggregate primary types using the priority extraction rule: take the first word from the portion of `type_line` before the em-dash `—` that matches, in priority order: Creature > Land > Artifact > Enchantment > Planeswalker > Instant > Sorcery > Battle. Non-matching type lines SHALL be counted as "Other".

The endpoint SHALL accept the same filter query parameters as all other analytics endpoints: `search`, `rarity`, `type` (alias), `set_name`, `price_min`, `price_max`, `color_identity`, `cmc`.

**Implementation constraint**: The `GET /api/analytics/type` route SHALL delegate all database access to a public repository method (`CollectionRepository.get_type_line_data`). The route SHALL NOT access private repository methods (`_build_filter_clauses`, `_get_engine`) or import SQLAlchemy directly. Python-level primary-type extraction (`_extract_primary_type`) SHALL remain in the route layer and be applied to the rows returned by the repository.

#### Scenario: Standard type extraction
- **WHEN** a card has `type_line = "Legendary Creature — Dragon"`
- **THEN** it is counted under the "Creature" bucket

#### Scenario: Dual-type card uses priority order
- **WHEN** a card has `type_line = "Artifact Creature — Golem"`
- **THEN** it is counted under "Creature" (Creature ranks above Artifact)

#### Scenario: Land extraction
- **WHEN** a card has `type_line = "Basic Land — Forest"`
- **THEN** it is counted under "Land"

#### Scenario: Unknown type falls to Other
- **WHEN** a card has `type_line = ""` or an unrecognised value
- **THEN** it is counted under "Other"

#### Scenario: Null type_line falls to Other
- **WHEN** a card has `type_line = None`
- **THEN** it is counted under "Other"

#### Scenario: Repository delegation in Postgres mode
- **WHEN** a PostgreSQL repository is active and `GET /api/analytics/type` is called
- **THEN** the route calls `repo.get_type_line_data(user_id, filters)` to retrieve filtered (type_line, quantity) rows
- **AND** the route does not call any private repository method or import SQLAlchemy

#### Scenario: Sheets path uses in-memory collection
- **WHEN** no PostgreSQL repository is available (Sheets mode)
- **THEN** the route reads from the in-memory cached collection and applies `_extract_primary_type` over each card's `type_line` or `type` field

### Requirement: type_line as a drill-down dimension

The analytics page drill-down state SHALL support a `type_line` dimension alongside the existing `rarity`, `color_identity`, `cmc`, and `set_name` dimensions.

When `type_line` drill-down is active, it SHALL be forwarded to all analytics endpoints and the stats endpoint as the `type` query parameter, consistent with the existing `type_` filter accepted by `filter_collection`.

An active `type_line` drill-down SHALL be displayed as a removable chip in the filter bar with label `"Type: {value}"`.

#### Scenario: Type drill-down cross-filters all charts
- WHEN a user clicks the "Creature" bar in the Type Distribution chart
- THEN all other charts (Rarity, Color Identity, Mana Curve, Top Sets) refetch with `type=Creature` and show data for creatures only
- AND the KPI cards update to reflect the creature-only totals

#### Scenario: Clicking the same bar twice clears the filter
- WHEN a user clicks the "Creature" bar while `type_line = "Creature"` is already active
- THEN the type_line drill-down is cleared and all charts return to unfiltered data

### Requirement: Barrel export includes TypeDistributionChart

The barrel export at `frontend/src/components/analytics/index.ts` SHALL re-export `TypeDistributionChart` and `TypeEntry`.

### Requirement: API client includes getAnalyticsType

The `api` object in `frontend/src/api/client.ts` SHALL include a `getAnalyticsType` method with the same signature pattern as `getAnalyticsRarity`, `getAnalyticsColorIdentity`, `getAnalyticsCmc`, and `getAnalyticsSets`.

### Requirement: Chart grid layout for five charts

The Analytics page chart grid SHALL accommodate five charts. The Type Distribution chart SHALL span the full row width (`lg:col-span-2`) to give the horizontal bar chart adequate label space.

### Requirement: Repository method for type-line data retrieval

`CollectionRepository` SHALL expose a public method `get_type_line_data(user_id, filters)` that returns a list of dicts with keys `type_line` (str or None) and `quantity` (int) for all cards matching the given filters.

The default implementation in the ABC SHALL return an empty list. `PostgresCollectionRepository` SHALL override this method with a SQL query: `SELECT type_line, quantity FROM cards {where_clause}`, where the WHERE clause is built by the existing `_build_filter_clauses` internal helper (acceptable as same-class access).

#### Scenario: Default ABC returns empty list
- **WHEN** `CollectionRepository.get_type_line_data` is called on the base class
- **THEN** it returns `[]`

#### Scenario: Postgres returns filtered type_line rows
- **WHEN** `PostgresCollectionRepository.get_type_line_data` is called with a user_id and rarity filter
- **THEN** it returns only rows for cards belonging to that user with the matching rarity, each with `type_line` and `quantity` keys

#### Scenario: Postgres handles null type_line
- **WHEN** a card has a NULL `type_line` in the database
- **THEN** the returned dict for that card has `type_line: None` and `quantity` set to the card's quantity value

### Requirement: Test coverage for analytics color-identity endpoint

The test suite SHALL include tests for `GET /api/analytics/color-identity` covering: HTTP 200 response, response body is a JSON array, each element contains `color_identity` and `count` keys, and aggregation counts are correct for a known fixture collection.

#### Scenario: Color identity returns 200
- **WHEN** `GET /api/analytics/color-identity` is called with a mocked empty collection (Sheets path)
- **THEN** the response status is 200

#### Scenario: Color identity response shape
- **WHEN** `GET /api/analytics/color-identity` is called with a mocked collection containing cards with color identities "R", "U", ""
- **THEN** the response is a list where each element has `color_identity` (str) and `count` (int) keys

#### Scenario: Color identity aggregation correctness
- **WHEN** the collection contains 2 Red cards and 1 Blue card
- **THEN** the response includes an entry for the normalized Red identity with count 2 and an entry for normalized Blue with count 1

### Requirement: Test coverage for analytics CMC endpoint

The test suite SHALL include tests for `GET /api/analytics/cmc` covering: HTTP 200 response, response body is a JSON array, each element contains `cmc` and `count` keys, CMC bucket ordering (numeric values ascending, "7+" after "6", "Unknown" last), and edge cases (null CMC maps to "Unknown", float CMC >= 7.0 maps to "7+").

#### Scenario: CMC returns 200
- **WHEN** `GET /api/analytics/cmc` is called with a mocked empty collection (Sheets path)
- **THEN** the response status is 200

#### Scenario: CMC response shape
- **WHEN** `GET /api/analytics/cmc` is called with a mocked collection
- **THEN** the response is a list where each element has `cmc` (str) and `count` (int) keys

#### Scenario: Null CMC maps to Unknown
- **WHEN** a card has `cmc = None`
- **THEN** it is counted in the "Unknown" bucket

#### Scenario: CMC >= 7 maps to 7+
- **WHEN** a card has `cmc = 8`
- **THEN** it is counted in the "7+" bucket

#### Scenario: CMC bucket ordering
- **WHEN** the collection contains cards with cmc 0, 3, 8, and None
- **THEN** the result list is ordered: "0", "3", "7+", "Unknown"

### Requirement: Test coverage for analytics type endpoint

The test suite SHALL include tests for `GET /api/analytics/type` covering: HTTP 200 response, response body is a JSON array, each element contains `type_line` and `count` keys, and primary-type extraction is correct for known type_line values (Creature priority over Artifact, Land extraction, Other fallback).

#### Scenario: Type endpoint returns 200
- **WHEN** `GET /api/analytics/type` is called with a mocked empty collection (Sheets path)
- **THEN** the response status is 200

#### Scenario: Type response shape
- **WHEN** `GET /api/analytics/type` is called with a mocked collection
- **THEN** the response is a list where each element has `type_line` (str) and `count` (int) keys

#### Scenario: Creature extracted from legendary creature type_line
- **WHEN** the collection contains a card with `type` = "Legendary Creature — Dragon"
- **THEN** the "Creature" bucket count is 1

#### Scenario: Other for unrecognized type
- **WHEN** the collection contains a card with `type` = "" or None
- **THEN** the "Other" bucket count is incremented

#### Scenario: Priority order — Creature wins over Artifact
- **WHEN** the collection contains a card with `type` = "Artifact Creature — Golem"
- **THEN** the card is counted under "Creature", not "Artifact"

### Requirement: Test coverage for price history endpoint

The test suite SHALL include tests for `GET /api/cards/{id}/price-history` covering: 501 response when no Postgres repo is available (Sheets mode), 404 response when the card does not exist, and 200 response with correct `PriceHistoryResponse` shape when the card exists and has history.

#### Scenario: Price history returns 501 in Sheets mode
- **WHEN** `get_collection_repo` returns None and `GET /api/cards/1/price-history` is called
- **THEN** the response status is 501

#### Scenario: Price history returns 404 for missing card
- **WHEN** `get_collection_repo` returns a mock repo whose `get_card_by_id` returns None
- **THEN** `GET /api/cards/99/price-history` returns 404

#### Scenario: Price history returns 200 with correct shape
- **WHEN** `get_collection_repo` returns a mock repo whose `get_card_by_id` returns a card and `get_price_history` returns a list of price points
- **THEN** `GET /api/cards/1/price-history` returns 200 with a body containing `card_id`, `currency`, and `points` (list of objects with `recorded_at`, `price`, `source`, `currency`)
