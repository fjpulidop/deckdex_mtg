## 1. Filter state and data flow

- [x] 1.1 Add filter state in Dashboard: type (string, default "all"), set (string, default "all"), priceMin (string), priceMax (string) alongside existing search and rarity
- [x] 1.2 Compute filtered list in Dashboard: apply type, set, and price range (in addition to rarity) to the cards list; parse price as decimal, treat invalid/empty as no bound
- [x] 1.3 Derive distinct type and set_name options from the current (search-filtered) cards list; sort alphabetically for dropdowns

## 2. Filters component: new controls and props

- [x] 2.1 Extend Filters component props to accept type, set, priceMin, priceMax and callbacks (onTypeChange, onSetChange, onPriceRangeChange) plus optional list of active filter descriptors for chips
- [x] 2.2 Add Type dropdown: options "All" + distinct types from props; controlled by type value; call onTypeChange on change
- [x] 2.3 Add Set dropdown: options "All" + distinct set names from props; controlled by set value; call onSetChange on change
- [x] 2.4 Add Price range: two optional number inputs (min, max) with placeholders; controlled by priceMin/priceMax; call onPriceRangeChange on change; use dot for decimals
- [x] 2.5 Style new controls with existing Tailwind patterns (rounded-lg, border, focus:ring-2 focus:ring-blue-500) to match current filter bar

## 3. Active filter chips and result count

- [x] 3.1 Pass active filter list to Filters (or render in same bar): e.g. rarity !== "all", type !== "all", set !== "all", or price range set; label each chip (e.g. "Rare", "Set: Dominaria", "€5 – €20")
- [x] 3.2 Render each active filter as a removable chip (click or × to clear); clearing a chip calls the appropriate single-filter reset (e.g. setRarity("all") or setType("all"))
- [x] 3.3 Display result count (e.g. "Showing X cards") derived from filtered list length; update when any filter changes; place near filter bar (e.g. right side or row below)

## 4. Clear Filters and wiring

- [x] 4.1 Ensure "Clear Filters" resets search, rarity, type, set, priceMin, and priceMax in Dashboard and in Filters local state (if any)
- [x] 4.2 Wire Dashboard filter state and derived options (types, sets) into Filters; ensure Filters is fully controlled or receives options from parent so type/set dropdowns reflect loaded data

## 5. Polish and verification

- [x] 5.1 Verify all filter combinations work together (name + rarity + type + set + price) and result count matches table length
- [x] 5.2 Verify chips remove only the intended filter and that Clear Filters resets everything; optional: add subtle transition when filters change for a polished feel
