# Tasks: Card Image Lightbox and Price History Chart

## Context

After a full code audit, both features are already implemented and wired together in the codebase. The tasks below document the implementation state and verify correctness of the existing code against the spec.

---

## Task 1: Verify PriceChart component implementation

**File:** `frontend/src/components/PriceChart.tsx`

**What to verify:**
- Component exports `PriceChart` with props `{ points: PriceHistoryPoint[], currency?: string, isLoading?: boolean }`
- Three rendering states are handled: loading (skeleton), empty (dashed box with `priceChart.noHistory`), data (Recharts LineChart)
- `ResponsiveContainer` wraps `LineChart` at `width="100%" height={160}`
- X-axis uses `formatDate` (locale-aware short month + day), Y-axis prefixes with currency symbol
- Tooltip formatter returns `[formattedPrice, t('priceChart.tooltipLabel')]`
- `Line` uses `stroke="#3b82f6"`, `strokeWidth={2}`, `dot={false}`, `activeDot={{ r: 4 }}`
- `CartesianGrid` uses Tailwind dark-mode classes for stroke color
- `useTranslation` is used; no hardcoded strings

**Acceptance criteria:** Component matches design spec exactly; no TypeScript errors; dark mode supported via Tailwind classes on CartesianGrid.

---

## Task 2: Verify usePriceHistory hook

**File:** `frontend/src/hooks/useApi.ts`

**What to verify:**
- `usePriceHistory(cardId: number | null | undefined, days = 90)` exists (line ~339)
- Uses `useQuery<PriceHistoryResponse>` with `queryKey: ['price-history', cardId, days]`
- `queryFn` calls `api.getPriceHistory(cardId!, days)` — non-null assertion correct because `enabled: cardId != null`
- `staleTime: 5 * 60 * 1000` (5 minutes)
- `enabled: cardId != null` prevents fetching when cardId is absent

**Acceptance criteria:** Hook is typed correctly; does not fetch when cardId is null; cache key includes both cardId and days for correct cache separation.

---

## Task 3: Verify api.getPriceHistory client method

**File:** `frontend/src/api/client.ts`

**What to verify:**
- `api.getPriceHistory(cardId: number, days = 90): Promise<PriceHistoryResponse>` exists (line ~562)
- Calls `apiFetch(`${API_BASE}/cards/${cardId}/price-history?days=${days}`)`
- Throws on non-ok response with message `'Failed to fetch price history'`
- `PriceHistoryPoint` interface has `{ recorded_at: string; price: number; source: string; currency: string }`
- `PriceHistoryResponse` interface has `{ card_id: number; currency: string; points: PriceHistoryPoint[] }`

**Acceptance criteria:** Types match backend `PriceHistoryResponse` Pydantic model exactly; no `any` types; error path throws with a descriptive message.

---

## Task 4: Verify PriceChart integration in CardDetailModal

**File:** `frontend/src/components/CardDetailModal.tsx`

**What to verify:**
- `PriceChart` is imported at top of file
- `usePriceHistory` is imported from `../hooks/useApi`
- `const { data: priceHistoryData, isLoading: priceHistoryLoading } = usePriceHistory(cardId)` is called unconditionally (hooks cannot be conditional)
- `PriceChart` is rendered inside the view-mode branch (not inside the `isEditing` branch), gated on `cardId != null`
- Props: `points={priceHistoryData?.points ?? []}`, `currency={priceHistoryData?.currency ?? 'eur'}`, `isLoading={priceHistoryLoading}`

**Acceptance criteria:** Chart is visible only in view mode; edit mode hides the chart; null card id suppresses the chart entirely; optional chaining prevents runtime errors when data is undefined.

---

## Task 5: Verify lightbox implementation in CardDetailModal

**File:** `frontend/src/components/CardDetailModal.tsx`

**What to verify:**
- `const [imageLightboxOpen, setImageLightboxOpen] = useState(false)` state exists
- Image wrapper in left panel uses `role="button"`, `tabIndex={0}`, `aria-label={t('cardDetail.viewLarger')}`, `className="cursor-zoom-in inline-block"`
- `onClick` handler guards `imageLoaded` before setting lightbox open: `() => imageLoaded && setImageLightboxOpen(true)`
- `onKeyDown` activates on `Enter` key with same guard
- Lightbox renders as `{imageLightboxOpen && imageUrl && (...)}` (conditional on both state and image availability)
- Lightbox uses `<AccessibleModal isOpen={true} onClose={() => setImageLightboxOpen(false)} titleId="card-detail-lightbox-title" className="z-[60] cursor-zoom-out">`
- Lightbox content is a `role="button"` div that closes on click and Enter/Space keydown
- Lightbox title uses `<span id="card-detail-lightbox-title" className="sr-only">` with `t('cardDetail.lightboxTitle', { name: displayName })`
- Lightbox image uses `max-w-[488px] max-h-[680px] w-auto h-auto object-contain rounded-lg shadow-2xl`

**Acceptance criteria:** Lightbox opens only after image has loaded; ESC closes it via AccessibleModal; clicking inside closes it; clicking outside (backdrop) closes it via AccessibleModal; parent modal remains open; z-index is correct.

---

## Task 6: Verify i18n keys in en.json and es.json

**Files:** `frontend/src/locales/en.json`, `frontend/src/locales/es.json`

**What to verify in en.json:**
- `priceChart.title`: `"Price History"`
- `priceChart.noHistory`: `"No price history yet — run a price update to start tracking."`
- `priceChart.tooltipLabel`: `"Price"`
- `cardDetail.viewLarger`: `"View image larger"`
- `cardDetail.lightboxTitle`: `"Card image: {{name}}"` (interpolation key must be `name`)

**What to verify in es.json:**
- `priceChart.title`: `"Historial de precios"`
- `priceChart.noHistory`: present (Spanish translation)
- `priceChart.tooltipLabel`: `"Precio"`
- `cardDetail.viewLarger`: present (Spanish translation)
- `cardDetail.lightboxTitle`: present with `{{name}}` interpolation

**Acceptance criteria:** All five keys exist in both locale files; interpolation placeholder `{{name}}` is present in both versions of `cardDetail.lightboxTitle`; no missing keys that would cause i18next to fall back to key strings.

---

## Task 7: Verify backend endpoint (no changes needed)

**File:** `backend/api/routes/cards.py` lines 308-344

**What to verify:**
- `GET /{id}/price-history` route exists under the cards router
- `days` query param: `Query(default=90, ge=1, le=365)`
- Requires `get_current_user_id` dependency (auth enforced)
- Returns 501 when no Postgres (`get_collection_repo()` returns None)
- Returns 404 when card not found for the user
- Returns `PriceHistoryResponse(card_id=id, currency="eur", points=[...])`
- Points are `PriceHistoryPoint` models: `recorded_at`, `price`, `source`, `currency`

**Acceptance criteria:** No backend changes required; endpoint matches what `api.getPriceHistory` in the frontend expects; 501 response handled gracefully by the frontend (empty points fallback in PriceChart).

---

## Task 8: Write tests for PriceChart component

**File:** `tests/test_price_chart.py` (or frontend test if applicable)

Note: If a frontend test suite exists, add a React Testing Library test for `PriceChart`. If only pytest is used, this task covers the backend endpoint tests.

**Backend test — add to existing cards test file if one exists:**
- `GET /api/cards/{id}/price-history` with valid card returns 200 with `{ card_id, currency, points }`
- Returns 501 when repo is None (Google Sheets mode)
- Returns 404 when card not found
- `days` param validation: `days=0` returns 422 (below `ge=1`), `days=400` returns 422 (above `le=365`)

**Frontend unit test (if RTL is configured):**
- `PriceChart` renders skeleton when `isLoading={true}`
- `PriceChart` renders empty state message when `points=[]`
- `PriceChart` renders the chart container when points are provided

**Acceptance criteria:** At minimum, the backend endpoint happy-path and 501/404 error paths are tested; no regressions in existing card route tests.
