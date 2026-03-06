## MODIFIED Requirements

### Requirements (compact)

- **KPIs:** Total card count and total value (optional avg) for current filter/drill-down; from backend with same params as charts (search, rarity, type, set_name, price_min, price_max, color_identity, cmc + drill slice). Update when user clicks chart segment. All filter parameters SHALL be passed using keyword arguments to `filter_collection`.
- **Charts (all clickable → set drill-down context):** Rarity (count per rarity); color identity (count per color); CMC (buckets 0,1,2…7+); sets (top N by count). Backend aggregations; refetch all with new context on click. All four drill-down dimensions (rarity, color_identity, cmc, set_name) SHALL be sent as query parameters to all analytics and stats endpoints.
- **Context:** "View all" / Clear resets drill-down to full collection; active context visible (e.g. chip).
- **States:** Loading (skeletons); empty (no cards in context → message, no misleading zero charts); error + retry.
- **Visual:** Palette and typography aligned with app (light/dark); labels/legends so meaning clear without color alone.

## ADDED Requirements

### Requirement: CMC filter in shared filter module
The `filter_collection` function SHALL accept an optional `cmc` parameter for filtering cards by converted mana cost bucket.

#### Scenario: Filter by exact CMC value
- **WHEN** `cmc` parameter is "3"
- **THEN** only cards whose CMC rounds to 3 SHALL be returned

#### Scenario: Filter by CMC 7+ bucket
- **WHEN** `cmc` parameter is "7+"
- **THEN** only cards whose CMC is >= 7 SHALL be returned

#### Scenario: Filter by CMC Unknown
- **WHEN** `cmc` parameter is "Unknown"
- **THEN** only cards with null or unparseable CMC SHALL be returned

### Requirement: Color identity drill-down query parameter
All analytics endpoints and the stats endpoint SHALL accept an optional `color_identity` query parameter and pass it through to `filter_collection`.

#### Scenario: Drill down by color identity
- **WHEN** user clicks a color identity segment in the pie chart
- **THEN** the frontend SHALL send `color_identity` as a query parameter to all analytics and stats endpoints
- **AND** the backend SHALL filter results to only cards matching that color identity

### Requirement: CMC drill-down query parameter
All analytics endpoints and the stats endpoint SHALL accept an optional `cmc` query parameter and pass it through to `filter_collection`.

#### Scenario: Drill down by CMC bucket
- **WHEN** user clicks a CMC bar in the mana curve chart
- **THEN** the frontend SHALL send `cmc` as a query parameter to all analytics and stats endpoints
- **AND** the backend SHALL filter results to only cards in that CMC bucket

### Requirement: Backend filter calls use keyword arguments
All calls to `filter_collection` from analytics and stats routes SHALL use keyword arguments to prevent positional argument misalignment.

#### Scenario: Parameters arrive in correct slots
- **WHEN** analytics or stats endpoint calls `filter_collection` with `set_name="Bloomburrow"`
- **THEN** the filter SHALL match against the `set_name` field, not `color_identity` or any other field
