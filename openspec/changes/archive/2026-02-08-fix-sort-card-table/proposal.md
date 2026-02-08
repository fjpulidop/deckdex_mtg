## Why

The card table sorts all columns using string comparison. The Price column stores values as strings (e.g. "9", "81", "7"), so sorting is lexicographic: users see order like 9 €, 81 €, 7 € instead of 81 €, 9 €, 7 €. This is confusing and wrong for a numeric column. Fixing it ensures table sort matches user expectations for price (and any future numeric columns).

## What Changes

- Card table sort SHALL treat the **Price** column as numeric: compare by numeric value (e.g. parseFloat), not by string.
- Text columns (name, type, rarity) SHALL continue to sort as strings (current behaviour).
- Non-numeric or empty price values SHALL have defined behaviour (e.g. sort last or treat as zero) so order is deterministic.
- Sort SHALL be applied to the **full** card list (all rows received by the table) before pagination, so that the same order is consistent across all pages, not only the visible page.

## Capabilities

### New Capabilities

- (None)

### Modified Capabilities

- **web-dashboard-ui**: Add requirement that the card table SHALL sort the Price column by numeric value; string columns SHALL sort lexicographically. Delta spec will define the new sort behaviour and scenarios.

## Impact

- **Frontend:** `frontend/src/components/CardTable.tsx` — sort logic only; no API or prop changes.
- No backend, API, or dependency changes.
