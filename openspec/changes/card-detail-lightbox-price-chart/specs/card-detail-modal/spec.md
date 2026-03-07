# Card Detail Modal

Read-only modal: card image (GET /api/cards/{id}/image) + structured data (name, type, mana cost, oracle, P/T, set, rarity, price) in Scryfall-style layout. Opened on table row click (not on Edit/Delete).

### Requirements (compact)

- **Image + data:** Image from backend; loading placeholder; 404/error → fallback message, text still shown. Text layout: name, type line, mana cost, description, P/T, set, number, rarity, price.
- **Mana symbols:** {W}, {U}, etc. rendered as Scryfall-style SVGs (cost + oracle); hybrid/generic/special supported; aria-label/title for a11y. Close → dismiss, no persist.
- **Update price:** Button when card has id; POST /api/prices/update/{card_id} → job in global bar; no button when no id.
- **Refresh on job complete:** When single-card Update price job completes: refresh dashboard stats, modal price (if same card open), and table row.
- **Lightbox:** Click image → larger overlay (max 488×680 px); click overlay or Escape → close, modal stays open. Cursor: zoom-in on modal image, zoom-out on lightbox. Implemented as a nested `AccessibleModal` at `z-[60]` (above parent modal's `z-50`). Image click is disabled while the image is still loading. Lightbox includes a visually hidden title (`sr-only`) linked via `aria-labelledby` for screen readers. i18n keys: `cardDetail.viewLarger` (trigger aria-label), `cardDetail.lightboxTitle` (lightbox dialog title with card name).
- **Price history chart:** Below card metadata in the right panel (view mode only, not shown in edit mode), a Recharts `LineChart` renders up to 90 days of price history fetched from `GET /api/cards/{id}/price-history?days=90`. Loading state: animated skeleton (`h-40 animate-pulse`). Empty state (no history yet): dashed border box with `priceChart.noHistory` message. Chart config: X-axis = short date labels, Y-axis = EUR price with `€` prefix, blue line (`stroke="#3b82f6"`), tooltip shows formatted price. No chart rendered when `cardId` is null (e.g., card has no database id). Component: `frontend/src/components/PriceChart.tsx`. Hook: `usePriceHistory(cardId, 90)` from `frontend/src/hooks/useApi.ts`. i18n keys: `priceChart.title`, `priceChart.noHistory`, `priceChart.tooltipLabel`.
- **Accessibility:** Image trigger uses `role="button"`, `tabIndex={0}`, `aria-label`. Lightbox uses `AccessibleModal` for focus trap and ESC dismiss. Price chart skeleton does not require ARIA (decorative loading state).
