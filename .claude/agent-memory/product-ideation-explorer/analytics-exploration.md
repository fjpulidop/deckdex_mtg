# Analytics Exploration (2026-03-05)

## Current State
- **4 chart endpoints**: rarity, color-identity, cmc, sets (all in backend/api/routes/analytics.py)
- **4 chart components**: RarityChart (bar), ColorRadar (WUBRG radar), ManaCurve (area), TopSetsChart (horizontal bar)
- **KPI cards**: Total Cards, Total Value, Mythic Rares, Avg Price
- **Drill-down**: click any chart segment to cross-filter all charts + KPIs
- **Collection Insights**: 17 predefined questions via InsightsService, shown on Dashboard (not Analytics page)
- **No price history table** exists yet - data model mentions PriceHistory but no migration
- **No deck analytics** - decks exist (id, name, deck_cards) but no analytics endpoints for them
- **catalog_cards has legalities JSONB** - enables format-aware analytics without API calls
- **cards table has created_at/updated_at** - enables time-based analytics

## Architecture Notes
- All analytics computed in-memory from get_cached_collection() - no SQL aggregations
- 30-second TTL cache per endpoint + filter combination (in-memory dict)
- Duplicated _normalize_color_identity in analytics.py and insights_service.py
- Charts use Recharts library, all modular under components/analytics/
- Insights live on Dashboard page, not on Analytics page

## Gaps Identified
- No type-line distribution (Creature, Instant, Sorcery, etc.)
- No price-based charts (value distribution, price histogram)
- No deck-level analytics
- No cross-deck card overlap analysis
- No format legality breakdown
- No time-series (collection growth over time)
- No set completion tracking
- Insights and Analytics are separate pages with no cross-linking
- Backend does all computation in Python loops, not SQL - won't scale
