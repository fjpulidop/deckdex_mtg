## 1. Card table sort logic

- [x] 1.1 In `CardTable.tsx`, add numeric comparison for Price: when `sortKey === 'price'`, parse values (e.g. parseFloat, normalising comma to dot), compare numerically; treat NaN/empty as sort last in both directions
- [x] 1.2 Keep string comparison for name, type, and rarity columns (unchanged behaviour)
- [x] 1.3 Ensure sort continues to run on the full `cards` array before slicing for pagination (so all pages use one consistent order)
- [ ] 1.4 Manually verify: sort Price asc/desc shows correct numeric order (e.g. 81, 9, 7 when desc); empty/non-numeric prices appear last; name/type/rarity sort still work; changing page keeps the same global order
