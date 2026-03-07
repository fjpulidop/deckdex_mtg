# Design: Card Image Lightbox and Price History Chart

## Current State (confirmed by code audit)

Both features are already implemented in the codebase. This design document serves as the authoritative technical specification of what is built and what the final state should look like, for reference by the delta spec and task checklist.

Key files confirmed:
- `frontend/src/components/CardDetailModal.tsx` — lightbox state (`imageLightboxOpen`) and `PriceChart` usage already wired
- `frontend/src/components/PriceChart.tsx` — complete Recharts line chart component
- `frontend/src/hooks/useApi.ts` — `usePriceHistory(cardId, days)` hook already present (line 339)
- `frontend/src/api/client.ts` — `api.getPriceHistory(cardId, days)` already present (line 562), `PriceHistoryResponse` and `PriceHistoryPoint` interfaces exported (lines 139-150)
- `frontend/src/locales/en.json` — `priceChart.*` keys present (lines 604-608); `cardDetail.viewLarger` and `cardDetail.lightboxTitle` present (lines 105-106)
- `frontend/src/locales/es.json` — same keys present in Spanish (lines 604-608)
- `backend/api/routes/cards.py` lines 308-344 — `GET /api/cards/{id}/price-history` endpoint complete

---

## Component Architecture

### CardDetailModal Layout

```
CardDetailModal (AccessibleModal z-50)
  ├── Left panel: card image area
  │     └── <div role="button"> wraps <img>
  │           cursor-zoom-in, onClick → setImageLightboxOpen(true)
  │           disabled (no onClick) while image is still loading
  └── Right panel: metadata + actions
        ├── name, mana cost, type, description, P/T
        ├── set / rarity / price fields
        ├── PriceChart (rendered when cardId != null, view mode only)
        └── action buttons (edit / delete / update price)

ConfirmModal (delete confirmation)

Lightbox (AccessibleModal z-[60])
  └── <div role="button"> wrapping <img max-w-[488px] max-h-[680px]>
        onClick → setImageLightboxOpen(false)
```

### PriceChart Component

Location: `frontend/src/components/PriceChart.tsx`

Props interface:
```typescript
interface PriceChartProps {
  points: PriceHistoryPoint[];  // from api/client.ts
  currency?: string;            // default: 'eur'
  isLoading?: boolean;          // default: false
}
```

Rendering states:
1. **Loading** (`isLoading === true`): heading + `h-40` animated skeleton div (`animate-pulse`)
2. **Empty** (`points.length === 0`): heading + dashed border box with `priceChart.noHistory` message
3. **Data** (`points.length > 0`): heading + `ResponsiveContainer` (width 100%, height 160) containing `LineChart`

Recharts configuration:
```
LineChart
  data: points mapped to { date: formatDate(p.recorded_at), price: p.price }
  margin: { top: 4, right: 8, left: 0, bottom: 0 }

  CartesianGrid
    strokeDasharray="3 3"
    className="stroke-gray-200 dark:stroke-gray-700"

  XAxis
    dataKey="date"
    tick: { fontSize: 10, fill: 'currentColor' }
    tickLine: false, axisLine: false

  YAxis
    tick: { fontSize: 10, fill: 'currentColor' }
    tickFormatter: v => `${currencySymbol}${v}`
    tickLine: false, axisLine: false
    width: 48

  Tooltip
    formatter: value => [`${currencySymbol}${value.toFixed(2)}`, t('priceChart.tooltipLabel')]

  Line
    type="monotone"
    dataKey="price"
    stroke="#3b82f6"
    strokeWidth={2}
    dot={false}
    activeDot={{ r: 4 }}
```

`formatDate(iso: string)` uses `new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })` — locale-aware short date formatting.

Dark mode: `CartesianGrid` uses Tailwind class targeting (`stroke-gray-200 dark:stroke-gray-700`). Axis tick fill is `currentColor`, which inherits from parent Tailwind text color. No additional dark mode logic needed in the component itself.

### Lightbox Design

State: `const [imageLightboxOpen, setImageLightboxOpen] = useState(false)`

Trigger: The card image wrapper in the left panel is a `<div role="button" tabIndex={0}>` with:
- `onClick={() => imageLoaded && setImageLightboxOpen(true)}`
- `onKeyDown={e => e.key === 'Enter' && imageLoaded && setImageLightboxOpen(true)}`
- `className="cursor-zoom-in inline-block"`
- `aria-label={t('cardDetail.viewLarger')}`

The click handler guards `imageLoaded` to prevent opening the lightbox before the image has rendered (avoids showing a lightbox with a blank broken image).

Lightbox rendered as a second `AccessibleModal` nested inside the outer `<>` fragment:
```tsx
{imageLightboxOpen && imageUrl && (
  <AccessibleModal
    isOpen={true}
    onClose={() => setImageLightboxOpen(false)}
    titleId="card-detail-lightbox-title"
    className="z-[60] cursor-zoom-out"
  >
    <div
      tabIndex={0}
      role="button"
      aria-label={t('common.close')}
      onClick={() => setImageLightboxOpen(false)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setImageLightboxOpen(false); }}
      className="outline-none p-4"
    >
      <span id="card-detail-lightbox-title" className="sr-only">
        {t('cardDetail.lightboxTitle', { name: displayName })}
      </span>
      <img
        src={imageUrl}
        alt={displayName}
        className="max-w-[488px] max-h-[680px] w-auto h-auto object-contain rounded-lg shadow-2xl"
      />
    </div>
  </AccessibleModal>
)}
```

`z-[60]` ensures the lightbox stacks above the parent modal (`z-50`). `AccessibleModal` manages focus trap and ESC key handling automatically. The `cursor-zoom-out` on the outer modal communicates that clicking anywhere closes the lightbox.

---

## Data Flow

```
CardDetailModal receives card prop (Card)
  → cardId = card.id ?? null
  → useCardImage(cardId)          → src: imageUrl (blob URL from GET /api/cards/{id}/image)
  → usePriceHistory(cardId, 90)   → data: PriceHistoryResponse | undefined
      ↳ api.getPriceHistory(cardId, 90)
          → GET /api/cards/{cardId}/price-history?days=90
          → returns { card_id, currency, points: PriceHistoryPoint[] }

  PriceChart renders when cardId != null (view mode only, not in edit mode):
    points={priceHistoryData?.points ?? []}
    currency={priceHistoryData?.currency ?? 'eur'}
    isLoading={priceHistoryLoading}
```

The `usePriceHistory` hook has `staleTime: 5 * 60 * 1000` (5 minutes). Data is cached by TanStack Query under `['price-history', cardId, days]`. No manual invalidation is needed — the chart is read-only and reflects the last price update job's output.

---

## Accessibility

### Image Trigger
- `role="button"` on the wrapper div
- `tabIndex={0}` for keyboard focus
- `aria-label={t('cardDetail.viewLarger')}` — translatable
- Enter key activates (same as click)
- Cursor `cursor-zoom-in` provides visual affordance

### Lightbox
- `AccessibleModal` provides: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus trap, ESC dismiss
- `titleId="card-detail-lightbox-title"` links to a visually hidden `<span>` with descriptive text
- The close action is triggered by: ESC (AccessibleModal), clicking the backdrop (AccessibleModal), or clicking anywhere within the content div (role="button" handler)
- `z-[60]` ensures lightbox renders above `z-50` parent — stacking context is correct
- `cursor-zoom-out` on the `AccessibleModal` className provides visual close affordance

### Price Chart
- `ResponsiveContainer` is screen-reader-neutral (SVG chart)
- Section heading `priceChart.title` rendered as a visible `div` (not a heading element, consistent with existing pattern in `PriceChart.tsx`)
- Empty state message is plain text inside a border box — no special ARIA needed
- Loading state skeleton has `aria-hidden` pattern inherited from other skeletons in the modal

---

## i18n

All new strings use existing keys. No new keys are required for this feature — the implementation is complete.

Keys used:
- `priceChart.title` — "Price History" / "Historial de precios"
- `priceChart.noHistory` — no-data empty state message
- `priceChart.tooltipLabel` — "Price" / "Precio" (Recharts tooltip label)
- `cardDetail.viewLarger` — aria-label for the zoom-in trigger
- `cardDetail.lightboxTitle` — sr-only dialog title with card name interpolation
- `common.close` — aria-label for the lightbox close button

---

## Responsive Design

The `CardDetailModal` uses `max-w-2xl w-full` with `flex-col md:flex-row` layout. On mobile (`flex-col`), the image panel stacks above the data panel. The `PriceChart` sits in the right/bottom panel and uses `ResponsiveContainer width="100%"` — it adapts to whatever width the right panel provides, which is `flex-1` in the row layout.

The lightbox image uses `max-w-[488px] max-h-[680px]` — it will never exceed the viewport on typical screens. `AccessibleModal` handles centering; the image itself has `w-auto h-auto object-contain` so it scales down gracefully on small viewports.

---

## No Backend Changes Required

The backend is complete:
- `GET /api/cards/{id}/price-history?days=90` returns `{ card_id, currency, points }` (route at `backend/api/routes/cards.py` line 313)
- Returns 501 if PostgreSQL is unavailable (Google Sheets mode) — the frontend handles this via `usePriceHistory` returning no data (TanStack Query will show error state, but `points ?? []` fallback renders the empty state gracefully)
- Returns empty `points` array (not 404/500) when card has no history yet

---

## Dependencies

- `recharts ^3.7.0` — already installed in `frontend/package.json`
- `react-i18next` — already used in `CardDetailModal.tsx`
- `AccessibleModal` — already imported in `CardDetailModal.tsx`
- `PriceHistoryPoint`, `PriceHistoryResponse` — already exported from `api/client.ts`
