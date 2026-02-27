## 1. Create `TopValueCards` component

- [ ] 1.1 Create `frontend/src/components/TopValueCards.tsx` with the following interface:
  ```ts
  interface TopValueCardsProps {
    cards: Card[];
    onCardClick: (card: Card) => void;
  }
  ```
- [ ] 1.2 Derive top 5: filter `cards` to those where `parseFloat(card.price ?? '')` is a finite positive number, sort descending by that value, take the first 5. If the result is empty, render nothing (`return null`).
- [ ] 1.3 Render a section with heading "Top 5 más valiosas" and a horizontal flex row (wrap on small screens) with one card per slot. Each slot shows:
  - Card image via `<img src={api.getCardImageUrl(card.id!)} />` — `object-contain`, max height ~120px, rounded corners, lazy loading
  - On image error: show a neutral placeholder (gray rounded box, same dimensions)
  - Card name (truncated with ellipsis if long)
  - Set name in small muted text
  - Rarity badge: color-coded chip (common=gray, uncommon=green, rare=amber, mythic=orange)
  - Price in bold green
- [ ] 1.4 Each card slot is clickable (cursor-pointer, hover ring) and calls `onCardClick(card)` to open `CardDetailModal`
- [ ] 1.5 Wrap the section in a `bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6` container consistent with the rest of the dashboard

## 2. Integrate `TopValueCards` into `Dashboard.tsx`

- [ ] 2.1 Import `TopValueCards` in `Dashboard.tsx`
- [ ] 2.2 Fetch the unfiltered card list separately for the widget. The existing `useCards` call uses active filters, so add a second `useCards` call with **no filters** and `limit: 10000` to always supply the full collection to `TopValueCards`. Assign it to `allCardsData`.
- [ ] 2.3 Render `<TopValueCards cards={allCardsData ?? []} onCardClick={handleRowClick} />` between `<StatsCards>` and `<Filters>` in the JSX

## 3. Migrate filter state to URL params in `Dashboard.tsx`

- [ ] 3.1 Import `useSearchParams` from `react-router-dom`
- [ ] 3.2 Replace the 6 `useState` filter declarations with reads from `useSearchParams`:
  ```ts
  const [searchParams, setSearchParams] = useSearchParams();
  const search    = searchParams.get('q')        ?? '';
  const rarity    = searchParams.get('rarity')   ?? 'all';
  const type      = searchParams.get('type')     ?? 'all';
  const setFilter = searchParams.get('set')      ?? 'all';
  const priceMin  = searchParams.get('priceMin') ?? '';
  const priceMax  = searchParams.get('priceMax') ?? '';
  ```
- [ ] 3.3 Update each handler to write to `searchParams` instead of calling `setState`. Use a functional updater and `{ replace: true }` to avoid polluting browser history:
  ```ts
  const handleSearchChange = useCallback((value: string) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (value) next.set('q', value); else next.delete('q');
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  const handleRarityChange = useCallback((value: string) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (value !== 'all') next.set('rarity', value); else next.delete('rarity');
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  // same pattern for handleTypeChange (key: 'type') and handleSetChange (key: 'set')

  const handlePriceRangeChange = useCallback((min: string, max: string) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (min.trim()) next.set('priceMin', min); else next.delete('priceMin');
      if (max.trim()) next.set('priceMax', max); else next.delete('priceMax');
      return next;
    }, { replace: true });
  }, [setSearchParams]);
  ```
- [ ] 3.4 Update `handleClearFilters` to reset the URL:
  ```ts
  const handleClearFilters = useCallback(() => {
    setSearchParams({}, { replace: true });
  }, [setSearchParams]);
  ```
- [ ] 3.5 Remove all `setState` calls for `search`, `rarity`, `type`, `setFilter`, `priceMin`, `priceMax` — they are no longer needed (state is owned by the URL)
- [ ] 3.6 Verify that the active chips' `onRemove` callbacks also call `setSearchParams` (they reference the handler functions updated in 3.3 — if they called `setRarity('all')` etc., update them to call the handler directly or use the same `setSearchParams` pattern)
