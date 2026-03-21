# Context Bundle: Multi-Deck Comparison Tool

This file is the implementation reference. Read every section before writing any code.

---

## 1. Backend: Route registration pattern

**File:** `backend/api/routes/decks.py`

```python
# line 16 — router definition
router = APIRouter(prefix="/api/decks", tags=["decks"])

# line 19-26 — the guard used by ALL deck endpoints
def require_deck_repo() -> DeckRepository:
    repo = get_deck_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Decks require Postgres. Set DATABASE_URL to use the deck builder.",
        )
    return repo
```

**CRITICAL:** The new `GET /compare` route MUST be registered BEFORE `GET /{deck_id}`. FastAPI matches routes in declaration order. If `/{deck_id}` comes first, the path `/compare` will be matched with `deck_id="compare"` and raise a 422.

Insert the `compare_decks` function immediately before the `get_deck` function (line 94 in the current file):

```python
@router.get("/{deck_id}")       # line 94 currently — compare MUST appear above this
async def get_deck(...):
```

---

## 2. Backend: Existing card data shape from `get_deck_with_cards`

`repo.get_deck_with_cards(deck_id, user_id=user_id)` returns a `dict` like:

```json
{
  "id": 1,
  "name": "My Deck",
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00",
  "cards": [
    {
      "id": 10,
      "name": "Lightning Bolt",
      "type": "Instant",
      "mana_cost": "{R}",
      "cmc": 1.0,
      "color_identity": "R",
      "price": "0.35",
      "quantity": 1,
      "is_commander": false
    }
  ]
}
```

Relevant card fields for the compare endpoint:
- `name` (str) — used for overlap detection (lowercase comparison)
- `type` (str or None) — used for creature/instant type classification
- `mana_cost` (str or None) — returned in `OverlapCard`
- `cmc` (float or None) — used for mana curve bucketing
- `color_identity` (str or None) — used for color distribution (e.g. "WU", "R", "C", "")
- `price` (str or None) — the raw price string (e.g. "0.35", "N/A", None)
- `quantity` (int) — multiply by count in stats
- `id` (int) — used as `card_id` in `OverlapCard`

**Price parsing:** The existing JS helper `parsePrice` in `DeckDetailModal.tsx` (line 15-20) shows the pattern. Port to Python:
```python
def _parse_price(price: Optional[str]) -> float:
    if not price or price.strip() in ("", "N/A"):
        return 0.0
    try:
        return float(str(price).replace(",", ".").strip())
    except (ValueError, TypeError):
        return 0.0
```

---

## 3. Backend: CMC bucketing

Existing JS logic in `DeckDetailModal.tsx` (lines 22-26):
```javascript
function cmcBucket(cmc: number | undefined): number {
  if (cmc == null || !Number.isFinite(cmc)) return 0;
  const n = Math.floor(Number(cmc));
  return n >= 7 ? 7 : Math.max(0, n);
}
```

Python equivalent for the compare endpoint:
```python
def _cmc_bucket(cmc) -> str:
    if cmc is None:
        return "0"  # lands/colorless count toward 0
    try:
        n = int(float(cmc))
        if n >= 7:
            return "7+"
        return str(max(0, n))
    except (ValueError, TypeError):
        return "0"
```

The CMC bucket order for response is: `["0","1","2","3","4","5","6","7+"]`. Always emit all 8 buckets even if count is 0.

---

## 4. Backend: Color distribution logic

The `color_identity` field is a WUBRG string (e.g. `"WU"`, `"R"`, `""`, `"C"`, None).

Color distribution algorithm used in the compare endpoint:
```python
WUBRG = ["W", "U", "B", "R", "G"]

def _color_dist(cards: list) -> list[DeckColorCount]:
    totals = {c: 0 for c in WUBRG}
    colorless = 0
    for card in cards:
        ci = (card.get("color_identity") or "").strip().upper()
        qty = card.get("quantity") or 1
        letters = [ch for ch in ci if ch in totals]
        if not letters or ci == "C":
            colorless += qty
        else:
            for ch in letters:
                totals[ch] += qty
    result = [DeckColorCount(color=c, count=totals[c]) for c in WUBRG]
    result.append(DeckColorCount(color="C", count=colorless))
    return result
```

This is consistent with the `transformToRadar` function in `ColorRadar.tsx` (lines 33-65), which uses the same distribution approach.

---

## 5. Backend: Type classification for creature/instant ratio

The creature/instant ratio only needs to distinguish three buckets. Use the same priority list as `analytics.py` (`_TYPE_PRIORITY`, line 106-114) but simplified:

```python
def _primary_type(type_line: Optional[str]) -> str:
    if not type_line:
        return "Other"
    main = type_line.split("—")[0].split("//")[0]
    words = main.split()
    if "Creature" in words:
        return "Creature"
    if "Instant" in words:
        return "Instant"
    return "Other"
```

---

## 6. Backend: Overlap detection

```python
def _compute_overlap(
    decks_cards: Dict[int, List[Dict[str, Any]]],
) -> List[OverlapCard]:
    # name_lower -> {deck_id -> first card payload}
    name_map: Dict[str, Dict[int, Dict]] = {}
    for deck_id, cards in decks_cards.items():
        for card in cards:
            key = (card.get("name") or "").lower().strip()
            if not key:
                continue
            if key not in name_map:
                name_map[key] = {}
            if deck_id not in name_map[key]:
                name_map[key][deck_id] = card

    result: List[OverlapCard] = []
    for name_lower, deck_map in sorted(name_map.items()):
        if len(deck_map) < 2:
            continue
        representative = next(iter(deck_map.values()))
        result.append(OverlapCard(
            name=representative.get("name") or name_lower,
            card_id=representative.get("id"),
            mana_cost=representative.get("mana_cost"),
            type=representative.get("type"),
            price=representative.get("price"),
            deck_ids=list(deck_map.keys()),
        ))
    return result
```

---

## 7. Backend: Test fixture pattern (scope="function")

**File to extend:** `tests/test_decks.py`

Exact fixture template to use for the new compare tests:

```python
@pytest.fixture(scope="function")
def compare_client():
    mock_repo = MagicMock(spec=DeckRepository)
    app.dependency_overrides[require_deck_repo] = lambda: mock_repo
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client, mock_repo
    app.dependency_overrides.pop(require_deck_repo, None)
    app.dependency_overrides.pop(get_current_user_id, None)
```

Sample card data for tests:
```python
SAMPLE_CARD_BOLT = {
    "id": 10, "name": "Lightning Bolt", "type": "Instant",
    "mana_cost": "{R}", "cmc": 1.0, "color_identity": "R",
    "price": "0.35", "quantity": 1, "is_commander": False,
}
SAMPLE_CARD_SOLRING = {
    "id": 20, "name": "Sol Ring", "type": "Artifact",
    "mana_cost": "{1}", "cmc": 1.0, "color_identity": "",
    "price": "1.20", "quantity": 1, "is_commander": False,
}

DECK_1 = {"id": 1, "name": "Deck A", "cards": [SAMPLE_CARD_BOLT, SAMPLE_CARD_SOLRING]}
DECK_2 = {"id": 2, "name": "Deck B", "cards": [SAMPLE_CARD_BOLT]}
DECK_3 = {"id": 3, "name": "Deck C", "cards": [SAMPLE_CARD_SOLRING]}
```

Mock setup example:
```python
def test_compare_detects_overlap(compare_client):
    client, mock_repo = compare_client
    mock_repo.get_deck_with_cards.side_effect = lambda deck_id, user_id: (
        DECK_1 if deck_id == 1 else DECK_2
    )
    r = client.get("/api/decks/compare?ids=1,2")
    assert r.status_code == 200
    data = r.json()
    assert len(data["overlap_cards"]) == 1
    assert data["overlap_cards"][0]["name"] == "Lightning Bolt"
```

---

## 8. Frontend: Existing chart theme helpers

**File:** `frontend/src/components/analytics/constants.ts`

Use these imports in all new chart components:
```typescript
import {
  buildChartTheme,     // (isDark: boolean) => ChartTheme
  tooltipContentStyle, // (theme: ChartTheme) => CSSProperties
  MTG_COLOR_MAP,       // {W, U, B, R, G, C} → {label, hex}
  WUBRG_ORDER,         // ['W','U','B','R','G'] as const
  CHART_COLORS,        // ['#6366f1', '#06b6d4', ...] for badges
  formatCurrency,      // (value: number) => string — EUR
} from './analytics/constants';
```

Key hex values from `MTG_COLOR_MAP`:
- W: `#f5f0e1`, U: `#0e68ab`, B: `#4b4b4b`, R: `#d32029`, G: `#00733e`, C: `#9ca3af`

---

## 9. Frontend: `AccessibleModal` usage pattern

**File:** `frontend/src/components/AccessibleModal.tsx` (lines 40-165)

Required props: `isOpen`, `onClose`, `titleId`. Optional: `showCloseButton`, `className`.

The `titleId` MUST match an actual `id` attribute on an element INSIDE the modal panel. For `DeckComparisonModal`, the `<h2>` rendered in the select step carries `id="deck-comparison-modal-title"`, but in the compare step a different `<h2>` with the same id must be rendered to maintain the `aria-labelledby` reference. The simplest approach: always render `<h2 id="deck-comparison-modal-title" className="sr-only">` in the modal root when step is 'compare', and make it visible in the compare header.

---

## 10. Frontend: TanStack Query pattern for the comparison fetch

Pattern from `DeckDetailModal.tsx` (lines 90-93):
```typescript
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['deck', deckId],
  queryFn: () => api.getDeck(deckId),
});
```

For `ComparisonView`:
```typescript
const sortedIds = [...selectedIds].sort((a, b) => a - b);

const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['deck-comparison', sortedIds.join(',')],
  queryFn: () => api.compareDecks(selectedIds),
  enabled: selectedIds.length >= 2,
});
```

Sorting the IDs in the query key prevents duplicate cache entries when the user picks decks in different orders. The actual request still sends IDs in the order the user selected them (which doesn't affect the backend result).

---

## 11. Frontend: `ManaText` component

**File:** `frontend/src/components/ManaText.tsx`

Usage in `OverlapCardList`:
```tsx
import { ManaText } from './ManaText';
// ...
{card.mana_cost && <ManaText text={card.mana_cost} className="text-sm" />}
```

---

## 12. Frontend: ThemeContext — getting `isDark`

**File:** `frontend/src/contexts/ThemeContext.tsx`

Usage pattern (from `Analytics.tsx`):
```typescript
import { useTheme } from '../contexts/ThemeContext';
// inside component:
const { isDark } = useTheme();
```

Pass `isDark` as a prop down to `ComparisonDeckColumn`, `ComparisonManaCurve`, `ComparisonColorBar`.

---

## 13. Frontend: Recharts imports already in the project

Recharts is already installed (used in `DeckDetailModal.tsx` and all analytics components). The following are already in use and can be imported freely:

```typescript
import {
  BarChart, Bar, XAxis, YAxis, Cell,
  ResponsiveContainer, Tooltip,
  // For color bar stacked layout:
  // same BarChart, add layout="vertical" prop
} from 'recharts';
```

Existing bar chart pattern from `DeckDetailModal.tsx` (lines 305-336):
```tsx
<ResponsiveContainer width="100%" height="100%">
  <BarChart data={manaCurveData} margin={{ top: 0, right: 2, bottom: 0, left: 2 }}>
    <XAxis
      dataKey="cmc"
      tick={{ fontSize: 9, fill: 'currentColor' }}
      tickLine={false}
    />
    <YAxis hide domain={[0, 'auto']} />
    <Bar dataKey="count" radius={[3, 3, 0, 0]}>
      {manaCurveData.map((entry, idx) => (
        <Cell key={idx} fill="#6366f1" />
      ))}
    </Bar>
  </BarChart>
</ResponsiveContainer>
```

---

## 14. Frontend: Deck list already fetched by `DeckBuilder`

The `DeckBuilder` page (lines 61-70) already fetches the deck list:
```typescript
const { data: decks, isLoading, error: decksError, refetch: refetchDecks } = useQuery({
  queryKey: ['decks'],
  queryFn: () => api.getDecks(),
  retry: (_, err) => !(err instanceof Error && err.message.includes('Postgres')),
});
const list: DeckListItem[] = decks ?? [];
```

Pass `list` directly to `DeckComparisonModal`. No additional fetch needed at this level.

---

## 15. Frontend: i18n locale file structure

**Files:**
- `frontend/src/locales/en.json`
- `frontend/src/locales/es.json`

Both files use top-level namespaces (e.g. `"deckDetail"`, `"deckImport"`). Add `"deckComparison"` as a new top-level namespace. Do NOT add to existing namespaces.

Usage in components:
```typescript
import { useTranslation } from 'react-i18next';
// inside component:
const { t } = useTranslation();
t('deckComparison.title') // → "Compare Decks"
t('deckComparison.cards_other', { count: 60 }) // → "60 cards"
```

---

## 16. Frontend: Component test pattern

**File to follow:** `frontend/src/components/__tests__/DeckDetailModal.test.tsx`

Key patterns for the comparison modal test:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import * as clientModule from '../../api/client';

vi.mock('../../api/client', () => ({
  api: {
    compareDecks: vi.fn().mockResolvedValue({
      deck_ids: [1, 2],
      decks: [ /* ... */ ],
      overlap_cards: [],
    }),
    getDecks: vi.fn().mockResolvedValue([]),
  },
}));
```

Wrap renders in the required providers (QueryClientProvider, i18n). Follow the setup in the existing test files.

---

## 17. API endpoint URL reference

| Existing endpoints | Method | Path |
|---|---|---|
| List decks | GET | `/api/decks/` |
| Create deck | POST | `/api/decks/` |
| **New: compare** | **GET** | **`/api/decks/compare`** |
| Get single deck | GET | `/api/decks/{deck_id}` |
| Update deck name | PATCH | `/api/decks/{deck_id}` |
| Delete deck | DELETE | `/api/decks/{deck_id}` |

**The `/compare` path must appear before `/{deck_id}` in `decks.py`.**

---

## 18. API response shape example

`GET /api/decks/compare?ids=1,2` happy path response:

```json
{
  "deck_ids": [1, 2],
  "decks": [
    {
      "deck_id": 1,
      "deck_name": "Mono Red Burn",
      "total_cards": 60,
      "total_value": 45.80,
      "creature_count": 12,
      "instant_count": 20,
      "mana_curve": [
        {"cmc": "0", "count": 0},
        {"cmc": "1", "count": 24},
        {"cmc": "2", "count": 18},
        {"cmc": "3", "count": 12},
        {"cmc": "4", "count": 4},
        {"cmc": "5", "count": 2},
        {"cmc": "6", "count": 0},
        {"cmc": "7+", "count": 0}
      ],
      "color_distribution": [
        {"color": "W", "count": 0},
        {"color": "U", "count": 0},
        {"color": "B", "count": 0},
        {"color": "R", "count": 60},
        {"color": "G", "count": 0},
        {"color": "C", "count": 0}
      ]
    },
    {
      "deck_id": 2,
      "deck_name": "Izzet Control",
      "total_cards": 60,
      "total_value": 120.50,
      "creature_count": 6,
      "instant_count": 28,
      "mana_curve": [
        {"cmc": "0", "count": 0},
        {"cmc": "1", "count": 12},
        {"cmc": "2", "count": 18},
        {"cmc": "3", "count": 16},
        {"cmc": "4", "count": 10},
        {"cmc": "5", "count": 4},
        {"cmc": "6", "count": 0},
        {"cmc": "7+", "count": 0}
      ],
      "color_distribution": [
        {"color": "W", "count": 0},
        {"color": "U", "count": 60},
        {"color": "B", "count": 0},
        {"color": "R", "count": 60},
        {"color": "G", "count": 0},
        {"color": "C", "count": 4}
      ]
    }
  ],
  "overlap_cards": [
    {
      "name": "Lightning Bolt",
      "card_id": 42,
      "mana_cost": "{R}",
      "type": "Instant",
      "price": "0.35",
      "deck_ids": [1, 2]
    },
    {
      "name": "Scalding Tarn",
      "card_id": 78,
      "mana_cost": null,
      "type": "Land",
      "price": "18.50",
      "deck_ids": [1, 2]
    }
  ]
}
```

---

## 19. Validation error format reminder

As per project convention (`backend/api/main.py` lines 76-82), Pydantic validation errors return HTTP 400 (not 422). The new route does NOT use Pydantic models for the query parameter (`ids` is a plain `str`), so manual validation with `HTTPException(status_code=400, ...)` is correct.

---

## 20. File locations for quick reference

| Artifact | Path |
|---|---|
| Backend route | `backend/api/routes/decks.py` |
| DeckRepository | `deckdex/storage/deck_repository.py` |
| API client | `frontend/src/api/client.ts` |
| Analytics constants | `frontend/src/components/analytics/constants.ts` |
| AccessibleModal | `frontend/src/components/AccessibleModal.tsx` |
| ManaText | `frontend/src/components/ManaText.tsx` |
| DeckBuilder page | `frontend/src/pages/DeckBuilder.tsx` |
| DeckDetailModal | `frontend/src/components/DeckDetailModal.tsx` |
| en.json | `frontend/src/locales/en.json` |
| es.json | `frontend/src/locales/es.json` |
| Deck tests | `tests/test_decks.py` |
| ThemeContext | `frontend/src/contexts/ThemeContext.tsx` |
