# Technical Design: Multi-Deck Comparison Tool

---

## Architecture Overview

```
DeckBuilder page
  └─ "Compare Decks" button
       └─ DeckComparisonModal
            ├─ DeckMultiSelect        (selection step: choose 2-4 decks)
            └─ ComparisonView         (results step: shown after selection confirmed)
                 ├─ [per deck] ComparisonDeckColumn
                 │    ├─ KPI row (total cards, total value, creature:instant ratio)
                 │    ├─ ComparisonManaCurve (Recharts BarChart, 1 column per deck)
                 │    └─ ComparisonColorBar   (horizontal stacked bar, WUBRG+C)
                 └─ OverlapCardList   (cards shared by ≥2 selected decks)
```

The comparison data is fetched once from a single endpoint after the user confirms deck selection. The modal is self-contained: it does not mutate any deck or card state, so no query cache invalidation is needed.

---

## Backend Design

### New endpoint: `GET /api/decks/compare`

**Location:** `backend/api/routes/decks.py` (appended to the existing router)

**Query parameter:** `ids` — a comma-separated string of deck IDs, e.g. `?ids=1,3,7`

**Auth:** requires `get_current_user_id` (same as all deck endpoints)

**Postgres guard:** uses `require_deck_repo` (returns 501 if Postgres not configured)

#### Validation rules (return HTTP 400 via `HTTPException`):
- `ids` is required and non-empty.
- After splitting on `,` and parsing, the count must be between 2 and 4 inclusive.
- All values must parse to positive integers.

#### Authorisation:
- Each deck must be fetched with `user_id=user_id` scope. If any deck is missing (not found or belongs to another user), return 404.

#### Business logic (pure Python in the route layer; no new service needed):
1. For each deck ID, call `repo.get_deck_with_cards(deck_id, user_id=user_id)`. This reuses the existing query that returns full card payloads.
2. Compute per-deck stats from the card list (helper functions inside the route module, not exported):
   - `total_value`: sum of `parse_price(card.price) * card.quantity` for all cards.
   - `mana_curve`: count of cards per CMC bucket (0–7+), respecting `quantity`.
   - `color_distribution`: for each card, split `color_identity` by letter; accumulate counts per WUBRG letter; cards with empty/None identity count toward colorless.
   - `creature_count` / `instant_count`: filter by primary type using the same priority logic as the analytics route.
3. Compute overlap:
   - Build a `dict[card_name_lower, list[deck_id]]` across all selected decks.
   - Overlap entries are those where `len(deck_ids) >= 2`.
   - For each overlapping card, include the first matched full card payload (name, type, mana_cost, price, image/card_id) for display.

#### Response Pydantic models:

```python
class DeckManaCurveBucket(BaseModel):
    cmc: str          # "0".."6", "7+"
    count: int

class DeckColorCount(BaseModel):
    color: str        # "W", "U", "B", "R", "G", "C"
    count: int

class DeckComparisonStats(BaseModel):
    deck_id: int
    deck_name: str
    total_cards: int
    total_value: float
    creature_count: int
    instant_count: int
    mana_curve: list[DeckManaCurveBucket]
    color_distribution: list[DeckColorCount]

class OverlapCard(BaseModel):
    name: str
    card_id: Optional[int]
    mana_cost: Optional[str]
    type: Optional[str]
    price: Optional[str]
    deck_ids: list[int]   # which selected decks contain this card

class DeckComparisonResponse(BaseModel):
    deck_ids: list[int]
    decks: list[DeckComparisonStats]
    overlap_cards: list[OverlapCard]
```

#### HTTP status summary:

| Condition | Status |
|---|---|
| `ids` missing / fewer than 2 / more than 4 / non-integer | 400 |
| Any deck not found or not owned by user | 404 |
| Postgres not configured | 501 |
| Success | 200 |

---

## Frontend Design

### New files

#### `frontend/src/components/DeckComparisonModal.tsx`

The top-level modal. Uses `AccessibleModal` wrapper (same as `DeckDetailModal`).

**State machine (internal):**
- `step: 'select' | 'compare'`
- `selectedIds: number[]` — starts empty; updates when user toggles a deck.

**Props:**
```typescript
interface DeckComparisonModalProps {
  decks: DeckListItem[];   // full list already fetched by DeckBuilder
  onClose: () => void;
}
```

**Rendering:**
- When `step === 'select'`: renders `DeckMultiSelect`.
- When `step === 'compare'`: renders `ComparisonView` which owns the `useQuery` for the comparison endpoint.
- A "Back" button in compare step resets to `step = 'select'`.

Accessible: `titleId="deck-comparison-modal-title"`, `showCloseButton={true}`.

---

#### `frontend/src/components/DeckMultiSelect.tsx`

**Props:**
```typescript
interface DeckMultiSelectProps {
  decks: DeckListItem[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  onConfirm: () => void;
  onCancel: () => void;
}
```

**Rendering:**
- A scrollable list of deck cards (name + card_count). Each is a toggle button styled with an active ring when selected.
- Disables toggling a deck when already 4 are selected and it is not currently selected.
- "Compare" button enabled only when `selectedIds.length >= 2`.
- "Cancel" button calls `onCancel`.

---

#### `frontend/src/components/ComparisonView.tsx`

Owns the data fetch. Uses `useQuery` with key `['deck-comparison', selectedIds.join(',')]`.

**Fetches from:** `api.compareDeckst(ids)` — new API client method.

**On success:** renders one `ComparisonDeckColumn` per deck in a `flex` row (horizontally scrollable on small screens).

Below the column grid: `OverlapCardList`.

**Loading state:** skeleton placeholders per column.

**Error state:** error message with retry button.

---

#### `frontend/src/components/ComparisonDeckColumn.tsx`

**Props:**
```typescript
interface ComparisonDeckColumnProps {
  stats: DeckComparisonStats;
  isDark: boolean;
}
```

**Rendering:**
- Deck name heading.
- Three KPI chips: total cards, total value (formatted as currency via `formatCurrency`), creature:instant ratio ("{{creature}}:{{instant}}").
- `ComparisonManaCurve` — a Recharts `BarChart` (not `AreaChart`; bars are faster to visually compare side-by-side).
- `ComparisonColorBar` — a horizontal stacked `BarChart` with 100% normalization, one cell per color using `MTG_COLOR_MAP` hex values.

---

#### `frontend/src/components/ComparisonManaCurve.tsx`

Reuses the `BarChart` + `Cell` pattern from `DeckDetailModal` (already imported from Recharts in that file). Does NOT reuse the `ManaCurve` (AreaChart) component from analytics — a BarChart is superior for comparing two side-by-side curves at a glance because discrete bars make per-bucket comparison easier than area overlap.

**Props:**
```typescript
interface ComparisonManaCurveProps {
  data: DeckManaCurveBucket[];
  isDark: boolean;
}
```

Height: 120px (compact for side-by-side). Responsive via `ResponsiveContainer`.

---

#### `frontend/src/components/ComparisonColorBar.tsx`

A thin horizontal stacked bar showing color proportions. Uses Recharts `BarChart` with `layout="vertical"` and a single data point with one `Bar` per WUBRG+C color.

**Props:**
```typescript
interface ComparisonColorBarProps {
  data: DeckColorCount[];
  isDark: boolean;
}
```

Renders a legend row (colored squares + letter labels) below the bar.

---

#### `frontend/src/components/OverlapCardList.tsx`

**Props:**
```typescript
interface OverlapCardListProps {
  cards: OverlapCard[];
  deckNames: Record<number, string>;   // deck_id → name for badge labels
}
```

**Rendering:**
- If `cards.length === 0`: "No cards are shared between the selected decks." message.
- Otherwise: a sorted list (alphabetical by name) with each card on a row showing:
  - Card name
  - Mana cost (via `ManaText` component)
  - Price chip (EUR)
  - Deck name badges for each deck that contains the card
- The entire row has a highlighted background (indigo-50 / indigo-900/20).

---

### Modified files

#### `frontend/src/pages/DeckBuilder.tsx`

Add a "Compare Decks" button in the page header area, visible only when `list.length >= 2` and Postgres is available (i.e. `!decksUnavailable`).

State: `compareOpen: boolean` — controls whether `DeckComparisonModal` is rendered.

The `DeckComparisonModal` receives `decks={list}` (already fetched) and `onClose={() => setCompareOpen(false)}`.

---

#### `frontend/src/api/client.ts`

Add TypeScript interfaces and a new API method:

```typescript
// New interfaces (append after BatchAddResult)
export interface DeckManaCurveBucket {
  cmc: string;
  count: number;
}

export interface DeckColorCount {
  color: string;
  count: number;
}

export interface DeckComparisonStats {
  deck_id: number;
  deck_name: string;
  total_cards: number;
  total_value: number;
  creature_count: number;
  instant_count: number;
  mana_curve: DeckManaCurveBucket[];
  color_distribution: DeckColorCount[];
}

export interface OverlapCard {
  name: string;
  card_id: number | null;
  mana_cost: string | null;
  type: string | null;
  price: string | null;
  deck_ids: number[];
}

export interface DeckComparisonResponse {
  deck_ids: number[];
  decks: DeckComparisonStats[];
  overlap_cards: OverlapCard[];
}
```

New API method inside the `api` object:

```typescript
compareDecks: async (ids: number[]): Promise<DeckComparisonResponse> => {
  const query = ids.join(',');
  const response = await apiFetch(`${API_BASE}/decks/compare?ids=${query}`);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    if (response.status === 501) throw new Error((err as {detail?: string}).detail || 'Decks require Postgres');
    if (response.status === 404) throw new Error((err as {detail?: string}).detail || 'One or more decks not found');
    if (response.status === 400) throw new Error((err as {detail?: string}).detail || 'Invalid deck selection');
    throw new Error((err as {detail?: string}).detail || 'Failed to compare decks');
  }
  return response.json();
},
```

---

#### `frontend/src/locales/en.json`

Add a `deckComparison` namespace key:

```json
"deckComparison": {
  "title": "Compare Decks",
  "selectTitle": "Select Decks to Compare",
  "selectPrompt": "Choose 2 to 4 decks to compare side by side.",
  "compareButton": "Compare",
  "backButton": "Back",
  "cancelButton": "Cancel",
  "cards": "{{count}} cards",
  "totalValue": "Total Value",
  "creatureInstantRatio": "Creatures : Instants",
  "manaCurve": "Mana Curve",
  "colorDistribution": "Color Distribution",
  "overlapTitle": "Overlapping Cards",
  "noOverlap": "No cards are shared between the selected decks.",
  "loading": "Loading comparison…",
  "error": "Failed to load comparison",
  "deckBadge": "{{name}}",
  "compareDecksButton": "Compare Decks",
  "maxDecksReached": "Maximum 4 decks selected",
  "minDecksRequired": "Select at least 2 decks"
}
```

#### `frontend/src/locales/es.json`

Parallel Spanish translations for the same keys.

---

## Recharts Integration

The feature reuses the already-imported `recharts` package. No new dependency is needed.

Chart components use:
- `BarChart`, `Bar`, `Cell`, `XAxis`, `YAxis`, `ResponsiveContainer`, `Tooltip` — already used in `DeckDetailModal.tsx` and the analytics barrel.
- `buildChartTheme`, `tooltipContentStyle`, `MTG_COLOR_MAP`, `formatCurrency` — imported from `components/analytics/constants.ts`.

The comparison view does NOT reuse `ManaCurve` (the analytics area chart) directly, because the area chart is designed for a single dataset and does not expose a raw-bar variant suitable for per-deck comparison. Instead, `ComparisonManaCurve` is a small standalone component using `BarChart` at compact height.

---

## Data Flow

```
DeckBuilder
  → "Compare Decks" button click
  → setCompareOpen(true)
  → <DeckComparisonModal decks={list} onClose={...}>
       → DeckMultiSelect (no network)
       → user confirms selection (selectedIds: [1,3])
       → ComparisonView
            → useQuery(['deck-comparison', '1,3'], () => api.compareDecks([1,3]))
            → GET /api/decks/compare?ids=1,3
            → renders columns + overlap list
```

The comparison result is never written to any global cache key that would be invalidated by deck mutations. It is purely a read.

---

## Error Handling Summary

| Scenario | UI Response |
|---|---|
| Postgres not configured | The "Compare Decks" button is hidden (same condition as deck list unavailability) |
| Fewer than 2 decks in the user's collection | Button is hidden (`list.length < 2`) |
| API returns 400 (invalid IDs) | Error message inside `ComparisonView` |
| API returns 404 (deck not found) | Error message inside `ComparisonView` |
| Network error | Error message inside `ComparisonView` with retry button |

---

## Accessibility

- `DeckComparisonModal` uses `AccessibleModal` which provides `role="dialog"`, `aria-modal="true"`, focus trap, Escape-to-close, and body scroll-lock.
- `DeckMultiSelect` deck buttons use `aria-pressed` to reflect selection state.
- Overlap card list uses a `ul`/`li` structure.
- All interactive elements have visible focus rings (Tailwind `focus:ring`).
