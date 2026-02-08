# Analytics Dashboard (beta)

Metrics, charts, and drill-down over the collection. Beta; no chart library mandated; consistent with rest of dashboard.

### Requirements (compact)

- **KPIs:** Total card count and total value (optional avg) for current filter/drill-down; from backend with same params as charts (search, rarity, type, set_name, price_min, price_max + drill slice). Update when user clicks chart segment.
- **Charts (all clickable → set drill-down context):** Rarity (count per rarity); color identity (count per color); CMC (buckets 0,1,2…7+); sets (top N by count). Backend aggregations; refetch all with new context on click.
- **Context:** "View all" / Clear resets drill-down to full collection; active context visible (e.g. chip).
- **States:** Loading (skeletons); empty (no cards in context → message, no misleading zero charts); error + retry.
- **Visual:** Palette and typography aligned with app (light/dark); labels/legends so meaning clear without color alone.
