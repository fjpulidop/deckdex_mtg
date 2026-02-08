## Context

The card table in `CardTable.tsx` sorts by a single key (`sortKey`) using a generic comparator that does `aVal > bVal` / `aVal < bVal`. Values come from `Card`; `price` is typed as `string` from the API. All columns are therefore compared as strings, which produces wrong order for price (e.g. 9, 81, 7 instead of 81, 9, 7). No backend or API changes are needed; this is a frontend-only fix.

## Goals / Non-Goals

**Goals:**
- Price column sorts by numeric value (asc/desc).
- Other sortable columns (name, type, rarity) keep string sort.
- Deterministic order when price is missing or non-numeric.
- Sort is applied to the full card list in memory before pagination (current behaviour), so all pages share one consistent order.

**Non-Goals:**
- Changing API types or adding server-side sort.
- Adding sort to other columns or new numeric columns (can be done later with same pattern).

## Decisions

1. **Column-aware sort in CardTable**  
   In the same `sort` callback, branch on `sortKey === 'price'`: for price, compare `parseFloat(a.price)` vs `parseFloat(b.price)`; for other keys, keep string comparison.  
   *Alternative:* Centralise comparators in a small helper (e.g. `getCompareFn(sortKey, direction)`) for clarity and reuse if we add more numeric columns later. Either is fine; helper is slightly more scalable.

2. **Non-numeric or empty price**  
   Treat as `NaN` and sort last in both directions (so they don’t jump between top and bottom when toggling asc/desc).  
   *Alternative:* Treat as 0; rejected so "no price" doesn’t mix with real zero.

3. **Locale and decimals**  
   Normalise decimal separator (e.g. replace comma with dot) before `parseFloat` so "1,5" and "1.5" sort correctly. No locale-specific number formatting for sort; display format stays as-is.

## Risks / Trade-offs

- **Risk:** Price strings in unexpected formats (e.g. "€ 9.99") could parse wrong.  
  **Mitigation:** parseFloat ignores leading non-numeric characters; if we ever need stricter parsing, we can add a small normaliser (strip currency symbols) in one place.

- **Trade-off:** Only `price` is numeric for now; future numeric columns (e.g. cmc) would need the same treatment. Documenting the pattern in design (and optionally a shared compare helper) keeps the codebase consistent.
