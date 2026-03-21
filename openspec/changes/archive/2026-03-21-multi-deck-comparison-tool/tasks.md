# Implementation Tasks: Multi-Deck Comparison Tool

Tasks are ordered: backend data model → backend route → API client types → frontend components → i18n → wiring → tests.

---

## Task 1: Backend — Pydantic models and stats helper functions [backend]

**Description:** Add the response Pydantic models and the pure-Python helper functions that compute per-deck stats from a card list. No route wiring yet.

**Files:**
- Modify: `backend/api/routes/decks.py`

**Work:**
1. Add Pydantic models (append after the existing `DeckImportResponse` block):
   - `DeckManaCurveBucket(BaseModel)`: fields `cmc: str`, `count: int`
   - `DeckColorCount(BaseModel)`: fields `color: str`, `count: int`
   - `DeckComparisonStats(BaseModel)`: fields `deck_id: int`, `deck_name: str`, `total_cards: int`, `total_value: float`, `creature_count: int`, `instant_count: int`, `mana_curve: List[DeckManaCurveBucket]`, `color_distribution: List[DeckColorCount]`
   - `OverlapCard(BaseModel)`: fields `name: str`, `card_id: Optional[int]`, `mana_cost: Optional[str]`, `type: Optional[str]`, `price: Optional[str]`, `deck_ids: List[int]`
   - `DeckComparisonResponse(BaseModel)`: fields `deck_ids: List[int]`, `decks: List[DeckComparisonStats]`, `overlap_cards: List[OverlapCard]`

2. Add module-level helper functions (private, prefixed with `_`):
   - `_parse_price(price: Optional[str]) -> float` — same logic as `parsePrice` in `DeckDetailModal.tsx`; returns 0.0 on None/empty/"N/A".
   - `_cmc_bucket(cmc: Optional[float]) -> str` — buckets 0–6 as strings, ≥7 as "7+", None as "0" (count lands/colorless toward 0).
   - `_primary_type(type_line: Optional[str]) -> str` — returns "Creature", "Instant", or "Other" (only need these two for the ratio; use the same priority list as `analytics.py` but only branch on Creature and Instant).
   - `_compute_deck_stats(deck_id: int, deck_name: str, cards: List[Dict]) -> DeckComparisonStats` — iterates cards, builds `mana_curve`, `color_distribution`, `creature_count`, `instant_count`, `total_value`, `total_cards`.
   - `_compute_overlap(decks_cards: Dict[int, List[Dict]]) -> List[OverlapCard]` — builds name→deck_ids mapping; returns OverlapCard list for entries with ≥2 deck IDs, sorted alphabetically.

**Acceptance criteria:**
- All five Pydantic models exist and are importable.
- `_compute_deck_stats` correctly computes `total_cards` as sum of `quantity` fields, `total_value` as sum of `price * quantity`, CMC buckets 0–7+, WUBRG+C color distribution, and creature/instant counts.
- `_compute_overlap` returns only cards present in ≥2 decks, sorted by name ascending.
- No route is registered yet.

**Dependencies:** None.

---

## Task 2: Backend — `GET /api/decks/compare` route [backend]

**Description:** Implement and register the compare endpoint.

**Files:**
- Modify: `backend/api/routes/decks.py`

**Work:**
1. Add route function after the existing import route:

```python
@router.get("/compare", response_model=DeckComparisonResponse)
async def compare_decks(
    ids: str = Query(..., description="Comma-separated deck IDs (2-4)"),
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
```

2. Inside the handler:
   a. Parse `ids.split(",")` — strip whitespace, convert to `int`. On `ValueError` raise `HTTPException(status_code=400, detail="ids must be comma-separated integers")`.
   b. Validate count is between 2 and 4 inclusive. On failure raise `HTTPException(status_code=400, detail="Select between 2 and 4 decks")`.
   c. Deduplicate IDs while preserving order.
   d. Fetch each deck with `repo.get_deck_with_cards(deck_id, user_id=user_id)`. If any returns `None`, raise `HTTPException(status_code=404, detail=f"Deck {deck_id} not found")`.
   e. Call `_compute_deck_stats` for each deck.
   f. Call `_compute_overlap` with the cards dict.
   g. Return `DeckComparisonResponse(deck_ids=parsed_ids, decks=stats_list, overlap_cards=overlap)`.

Note: The route path must be `/compare` (i.e. `/api/decks/compare`). Because FastAPI matches routes in registration order, this static path MUST be registered BEFORE the `/{deck_id}` path-param route to avoid being shadowed. Verify the existing route order in `decks.py` and insert `compare_decks` before `get_deck`.

**Acceptance criteria:**
- `GET /api/decks/compare?ids=1,2` with two valid decks returns 200 with `DeckComparisonResponse` shape.
- `GET /api/decks/compare?ids=1` returns 400.
- `GET /api/decks/compare?ids=1,2,3,4,5` returns 400.
- `GET /api/decks/compare?ids=1,999` where deck 999 does not exist returns 404.
- `GET /api/decks/compare?ids=abc` returns 400.
- `GET /api/decks/compare?ids=1,2` with no Postgres returns 501.
- Route appears in OpenAPI docs at `GET /api/decks/compare`.

**Dependencies:** Task 1.

---

## Task 3: Backend — Tests for the compare endpoint [backend]

**Description:** Add pytest tests for the new compare route following the `scope="function"` fixture pattern from `tests/test_decks.py`.

**Files:**
- Modify: `tests/test_decks.py`

**Work:**

Add a `compare_client` fixture (scope="function") identical in structure to `deck_client` — overrides `require_deck_repo` and `get_current_user_id`.

Add test functions:

1. `test_compare_decks_returns_200` — mock `get_deck_with_cards` to return two decks with sample cards; assert status 200 and response contains `decks` (len 2) and `overlap_cards`.
2. `test_compare_decks_too_few_ids` — `ids=1`; assert 400.
3. `test_compare_decks_too_many_ids` — `ids=1,2,3,4,5`; assert 400.
4. `test_compare_decks_non_integer_ids` — `ids=1,foo`; assert 400.
5. `test_compare_decks_deck_not_found` — mock returns `None` for second deck; assert 404.
6. `test_compare_decks_overlap_detection` — provide two decks both containing "Lightning Bolt"; assert `overlap_cards` contains one entry with `name="Lightning Bolt"` and `deck_ids` of length 2.
7. `test_compare_decks_no_overlap` — two decks with no shared card names; assert `overlap_cards` is empty.
8. `test_compare_decks_requires_auth` — without auth override; assert the route still requires auth (status not 200 without token).

Fixtures use `scope="function"`. All mocks use `unittest.mock.MagicMock`. No real database.

**Acceptance criteria:**
- All 8 tests pass with `pytest tests/test_decks.py`.
- No `scope="module"` on any fixture in this test file.

**Dependencies:** Task 2.

---

## Task 4: Frontend — TypeScript interfaces and `api.compareDecks` [frontend]

**Description:** Add the TypeScript types and the new API client method.

**Files:**
- Modify: `frontend/src/api/client.ts`

**Work:**
1. Append the following interfaces after the `BatchAddResult` interface (around line 188):
   ```typescript
   export interface DeckManaCurveBucket { cmc: string; count: number; }
   export interface DeckColorCount { color: string; count: number; }
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

2. Inside the `api` object, append `compareDecks` after `importDeckText`:
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

**Acceptance criteria:**
- `api.compareDecks([1, 2])` is callable and TypeScript compiles without errors.
- Existing tests pass (`npm run lint` and `npm run build`).

**Dependencies:** None (can run in parallel with Task 1).

---

## Task 5: Frontend — `ComparisonManaCurve` component [frontend]

**Description:** Compact bar chart for mana curve comparison.

**Files:**
- Create: `frontend/src/components/ComparisonManaCurve.tsx`

**Work:**
```typescript
import { BarChart, Bar, XAxis, YAxis, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { buildChartTheme, tooltipContentStyle } from './analytics/constants';
import type { DeckManaCurveBucket } from '../api/client';

interface ComparisonManaCurveProps {
  data: DeckManaCurveBucket[];
  isDark: boolean;
}
```

- `ResponsiveContainer width="100%" height={100}`.
- `BarChart` with `margin={{ top: 4, right: 4, bottom: 12, left: -20 }}`.
- `XAxis dataKey="cmc"` with `tick={{ fontSize: 9, fill: theme.axisColor }}`, `tickLine={false}`.
- `YAxis` hidden.
- Single `Bar dataKey="count"` with `radius={[2,2,0,0]}` and fill `#6366f1` (indigo-500).
- `Tooltip` using `tooltipContentStyle(theme)`.

**Acceptance criteria:**
- Component renders without TypeScript errors.
- Receives `DeckManaCurveBucket[]` and `isDark: boolean` props.
- Uses `ResponsiveContainer` for layout.

**Dependencies:** Task 4 (for the type import).

---

## Task 6: Frontend — `ComparisonColorBar` component [frontend]

**Description:** Thin horizontal stacked bar visualising color distribution.

**Files:**
- Create: `frontend/src/components/ComparisonColorBar.tsx`

**Work:**
```typescript
import { BarChart, Bar, Cell, ResponsiveContainer, XAxis } from 'recharts';
import { MTG_COLOR_MAP } from './analytics/constants';
import type { DeckColorCount } from '../api/client';

interface ComparisonColorBarProps {
  data: DeckColorCount[];
  isDark: boolean;
}
```

Strategy: normalise counts to percentages, render one `Bar` per color using a single data row `[{name: 'colors', W: pctW, U: pctU, ...}]` with `BarChart layout="vertical"`.

- Height 28px for the bar, plus a 20px legend row below.
- One `Bar` per WUBRG+C color using `MTG_COLOR_MAP[color].hex` as fill.
- Legend row: colored squares (8x8px `span` with background) + letter labels in `text-xs`.
- If all counts are 0, render a placeholder grey bar.

**Acceptance criteria:**
- Renders a stacked bar with correct WUBRG+C colors from `MTG_COLOR_MAP`.
- Shows a colour legend row below the bar.
- No TypeScript errors.

**Dependencies:** Task 4 (for the type import).

---

## Task 7: Frontend — `ComparisonDeckColumn` component [frontend]

**Description:** One column of the side-by-side comparison grid, showing KPIs + charts for one deck.

**Files:**
- Create: `frontend/src/components/ComparisonDeckColumn.tsx`

**Work:**
```typescript
import { useTranslation } from 'react-i18next';
import { formatCurrency } from './analytics/constants';
import { ComparisonManaCurve } from './ComparisonManaCurve';
import { ComparisonColorBar } from './ComparisonColorBar';
import type { DeckComparisonStats } from '../api/client';

interface ComparisonDeckColumnProps {
  stats: DeckComparisonStats;
  isDark: boolean;
}
```

Layout (Tailwind):
```
<div className="flex flex-col gap-3 min-w-[180px] max-w-[240px] bg-gray-50 dark:bg-gray-900/40 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
  <h3>{stats.deck_name}</h3>
  <!-- KPI chips row -->
  <div className="flex flex-wrap gap-2 text-xs">
    <span>{stats.total_cards} {t('deckComparison.cards', {count: stats.total_cards})}</span>
    <span>{formatCurrency(stats.total_value)}</span>
    <span>{t('deckComparison.creatureInstantRatio')}: {stats.creature_count}:{stats.instant_count}</span>
  </div>
  <!-- Mana Curve -->
  <div>
    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('deckComparison.manaCurve')}</p>
    <ComparisonManaCurve data={stats.mana_curve} isDark={isDark} />
  </div>
  <!-- Color Distribution -->
  <div>
    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('deckComparison.colorDistribution')}</p>
    <ComparisonColorBar data={stats.color_distribution} isDark={isDark} />
  </div>
</div>
```

**Acceptance criteria:**
- Renders name, KPI chips, `ComparisonManaCurve`, and `ComparisonColorBar`.
- All strings use `t()` i18n keys.
- No TypeScript errors.

**Dependencies:** Tasks 5, 6 (for sub-components). Task 4 (for type import).

---

## Task 8: Frontend — `OverlapCardList` component [frontend]

**Description:** List of cards shared across ≥2 selected decks.

**Files:**
- Create: `frontend/src/components/OverlapCardList.tsx`

**Work:**
```typescript
import { useTranslation } from 'react-i18next';
import { ManaText } from './ManaText';
import type { OverlapCard, DeckComparisonStats } from '../api/client';

interface OverlapCardListProps {
  cards: OverlapCard[];
  decks: DeckComparisonStats[];  // used to resolve deck_id → deck_name
}
```

Layout:
- If `cards.length === 0`: `<p>{t('deckComparison.noOverlap')}</p>`.
- Otherwise: `<ul>` with `<li>` per card.
  - Each `<li>` has `bg-indigo-50 dark:bg-indigo-900/20 rounded px-3 py-2 flex items-center gap-2`.
  - Card name (truncated).
  - `ManaText` for mana_cost (if not null).
  - Price chip (if not null): `€{price}` in a small grey pill.
  - Deck name badges: one per deck_id in `overlap_card.deck_ids`, styled as small coloured pills (use `CHART_COLORS[index]` for variety).

**Acceptance criteria:**
- Renders empty state when `cards.length === 0`.
- Renders one row per overlap card with deck name badges.
- No TypeScript errors.

**Dependencies:** Task 4 (for type imports).

---

## Task 9: Frontend — `DeckMultiSelect` component [frontend]

**Description:** The deck selection step of the modal.

**Files:**
- Create: `frontend/src/components/DeckMultiSelect.tsx`

**Work:**
```typescript
import { useTranslation } from 'react-i18next';
import type { DeckListItem } from '../api/client';

interface DeckMultiSelectProps {
  decks: DeckListItem[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  onConfirm: () => void;
  onCancel: () => void;
}
```

Layout:
- `<h2 id="deck-comparison-modal-title">` — i18n key `deckComparison.selectTitle`.
- Prompt text — i18n key `deckComparison.selectPrompt`.
- Scrollable deck list: `<ul className="max-h-64 overflow-y-auto space-y-2">`. Each deck rendered as a `<button type="button" role="checkbox" aria-checked={isSelected}>` with:
  - Active: `ring-2 ring-indigo-500 bg-indigo-50 dark:bg-indigo-900/30`.
  - Disabled (4 already selected and not this one): `opacity-40 cursor-not-allowed`.
  - Content: deck name + card count.
- Footer: Cancel + "Compare" (disabled when `selectedIds.length < 2`).
- When exactly 4 are selected, show helper text `t('deckComparison.maxDecksReached')` in amber.

**Acceptance criteria:**
- Toggles deck in/out of selection on click.
- Disables toggle when 4 selected and deck is not selected.
- Compare button disabled when fewer than 2 selected.
- Correct `aria-checked` attribute on each deck button.
- No TypeScript errors.

**Dependencies:** Task 4 (for `DeckListItem` type).

---

## Task 10: Frontend — `ComparisonView` component [frontend]

**Description:** Orchestrates the TanStack Query fetch and renders the results grid.

**Files:**
- Create: `frontend/src/components/ComparisonView.tsx`

**Work:**
```typescript
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../contexts/ThemeContext';  // for isDark
import { api, DeckComparisonStats } from '../api/client';
import { ComparisonDeckColumn } from './ComparisonDeckColumn';
import { OverlapCardList } from './OverlapCardList';

interface ComparisonViewProps {
  selectedIds: number[];
}
```

Query key: `['deck-comparison', selectedIds.slice().sort().join(',')]` — sort IDs to avoid duplicate fetches from different selection orders.

Loading state: skeleton — three placeholder columns with `animate-pulse` divs.

Error state: error message + retry button (calls `refetch()`).

Success state:
- Horizontally scrollable container: `<div className="flex gap-4 overflow-x-auto pb-2">` with one `ComparisonDeckColumn` per deck.
- Below: `<OverlapCardList cards={data.overlap_cards} decks={data.decks} />`.

**Acceptance criteria:**
- Uses `useQuery` with correct key and `api.compareDecks`.
- Shows loading skeleton, error state with retry, and success state.
- Passes `isDark` from `ThemeContext` to child components.
- No TypeScript errors.

**Dependencies:** Tasks 7, 8 (for sub-components). Task 4 (for API types).

---

## Task 11: Frontend — `DeckComparisonModal` component [frontend]

**Description:** Top-level modal wrapping the two-step flow.

**Files:**
- Create: `frontend/src/components/DeckComparisonModal.tsx`

**Work:**
```typescript
import { useState } from 'react';
import { AccessibleModal } from './AccessibleModal';
import { DeckMultiSelect } from './DeckMultiSelect';
import { ComparisonView } from './ComparisonView';
import type { DeckListItem } from '../api/client';

interface DeckComparisonModalProps {
  decks: DeckListItem[];
  onClose: () => void;
}
```

State:
- `step: 'select' | 'compare'` — starts at `'select'`.
- `selectedIds: number[]` — starts as `[]`.

Rendering:
```tsx
<AccessibleModal
  isOpen={true}
  onClose={onClose}
  titleId="deck-comparison-modal-title"
  showCloseButton={true}
  className="z-50"
>
  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden">
    {step === 'select' && (
      <DeckMultiSelect
        decks={decks}
        selectedIds={selectedIds}
        onToggle={handleToggle}
        onConfirm={handleConfirm}
        onCancel={onClose}
      />
    )}
    {step === 'compare' && (
      <>
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
          <button onClick={() => setStep('select')}>{t('deckComparison.backButton')}</button>
          <h2 id="deck-comparison-modal-title">{t('deckComparison.title')}</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <ComparisonView selectedIds={selectedIds} />
        </div>
      </>
    )}
  </div>
</AccessibleModal>
```

`handleToggle(id)`: if in `selectedIds`, remove it; else if `selectedIds.length < 4`, add it.
`handleConfirm()`: set `step = 'compare'`.

**Acceptance criteria:**
- Renders `DeckMultiSelect` on first open.
- Transitions to `ComparisonView` on confirm.
- "Back" button returns to `DeckMultiSelect` (preserving `selectedIds`).
- Closes via Escape or the X button.
- `titleId` references a real `<h2 id="deck-comparison-modal-title">` element.
- No TypeScript errors.

**Dependencies:** Tasks 9, 10. Task 4 (for `DeckListItem`).

---

## Task 12: Frontend — Wire `DeckComparisonModal` into `DeckBuilder` page [frontend]

**Description:** Add the "Compare Decks" button and render the modal.

**Files:**
- Modify: `frontend/src/pages/DeckBuilder.tsx`

**Work:**
1. Add import: `import { DeckComparisonModal } from '../components/DeckComparisonModal';`.
2. Add state: `const [compareOpen, setCompareOpen] = useState(false);`.
3. In the page header (after the deck grid heading), add:
   ```tsx
   {!decksUnavailable && list.length >= 2 && (
     <button
       type="button"
       onClick={() => setCompareOpen(true)}
       className="px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-sm font-medium"
     >
       {t('deckComparison.compareDecksButton')}
     </button>
   )}
   ```
4. At the bottom of the JSX (alongside the existing modals), add:
   ```tsx
   {compareOpen && (
     <DeckComparisonModal
       decks={list}
       onClose={() => setCompareOpen(false)}
     />
   )}
   ```

**Acceptance criteria:**
- "Compare Decks" button appears only when `list.length >= 2` and `!decksUnavailable`.
- Clicking it opens `DeckComparisonModal`.
- Closing the modal sets `compareOpen = false`.
- No TypeScript errors; existing DeckBuilder tests still pass.

**Dependencies:** Task 11.

---

## Task 13: Frontend — i18n keys in `en.json` and `es.json` [frontend]

**Description:** Add all user-facing strings for this feature to both locale files.

**Files:**
- Modify: `frontend/src/locales/en.json`
- Modify: `frontend/src/locales/es.json`

**Work:**

In `en.json`, add a top-level `"deckComparison"` key (before the closing `}`):
```json
"deckComparison": {
  "title": "Compare Decks",
  "selectTitle": "Select Decks to Compare",
  "selectPrompt": "Choose 2 to 4 decks to compare side by side.",
  "compareButton": "Compare",
  "backButton": "Back",
  "cancelButton": "Cancel",
  "cards_one": "{{count}} card",
  "cards_other": "{{count}} cards",
  "totalValue": "Total Value",
  "creatureInstantRatio": "Creatures : Instants",
  "manaCurve": "Mana Curve",
  "colorDistribution": "Color Distribution",
  "overlapTitle": "Overlapping Cards",
  "noOverlap": "No cards are shared between the selected decks.",
  "loading": "Loading comparison…",
  "error": "Failed to load comparison",
  "compareDecksButton": "Compare Decks",
  "maxDecksReached": "Maximum 4 decks selected",
  "minDecksRequired": "Select at least 2 decks"
}
```

In `es.json`, add parallel Spanish translations:
```json
"deckComparison": {
  "title": "Comparar Mazos",
  "selectTitle": "Selecciona Mazos para Comparar",
  "selectPrompt": "Elige entre 2 y 4 mazos para comparar en paralelo.",
  "compareButton": "Comparar",
  "backButton": "Atrás",
  "cancelButton": "Cancelar",
  "cards_one": "{{count}} carta",
  "cards_other": "{{count}} cartas",
  "totalValue": "Valor Total",
  "creatureInstantRatio": "Criaturas : Instantáneos",
  "manaCurve": "Curva de Maná",
  "colorDistribution": "Distribución de Color",
  "overlapTitle": "Cartas Compartidas",
  "noOverlap": "Los mazos seleccionados no comparten ninguna carta.",
  "loading": "Cargando comparación…",
  "error": "Error al cargar la comparación",
  "compareDecksButton": "Comparar Mazos",
  "maxDecksReached": "Máximo 4 mazos seleccionados",
  "minDecksRequired": "Selecciona al menos 2 mazos"
}
```

**Acceptance criteria:**
- All i18n keys referenced by components in Tasks 5–12 have entries in both `en.json` and `es.json`.
- Both files remain valid JSON.
- No existing keys are modified.

**Dependencies:** Tasks 5–12 (to know which keys are needed); can be done in parallel if keys are known from the design.

---

## Task 14: Frontend — Smoke test for `DeckComparisonModal` [frontend]

**Description:** Add a basic component test to verify the modal renders and the selection step works.

**Files:**
- Create: `frontend/src/components/__tests__/DeckComparisonModal.test.tsx`

**Work:**

Mock `api.compareDecks` and `api.getDecks`. Provide a sample deck list (2 decks).

Tests:
1. `renders DeckMultiSelect on open` — render `<DeckComparisonModal decks={sampleDecks} onClose={vi.fn()} />`. Assert `role="dialog"` exists. Assert "Select Decks to Compare" heading is visible.
2. `disables Compare button when fewer than 2 decks selected` — assert the "Compare" button is disabled initially.
3. `enables Compare button when 2 decks selected` — click two deck buttons; assert "Compare" button is enabled.
4. `transitions to ComparisonView on confirm` — select 2 decks, click "Compare", mock `api.compareDecks` to return a valid response; assert the comparison title appears.
5. `calls onClose when X button is clicked` — assert `onClose` mock called after clicking X.

Follow existing test patterns: `vi.mock('../api/client')`, `@testing-library/react`, `vitest`.

**Acceptance criteria:**
- All 5 tests pass.
- No `scope="module"` fixtures.
- `api.compareDecks` is mocked, never calls real backend.

**Dependencies:** Task 11, Task 13.
