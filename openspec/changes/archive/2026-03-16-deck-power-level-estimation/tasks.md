# Implementation Tasks: Deck Power Level Auto-Estimation

Tasks are ordered by dependency. All backend tasks must be complete before frontend integration tasks.

---

## Task 1 [core] — Implement pure scoring engine

**File**: `deckdex/services/power_level.py` (new file)

**Description**: Create the `estimate_power_level(cards: list[dict]) -> PowerLevelResult` function and its supporting data (curated card sets, bracket mapping, summary builder). This module has zero I/O — it receives a pre-loaded list and returns a result.

**Implement**:
- `FAST_MANA`, `COMBO_PIECES` frozen sets (lowercase card names)
- `PREMIUM_LANDS` frozen set (ten original duals, ten shocklands, ten fetchlands, Zendikar battle lands)
- `FactorBreakdown` Pydantic model (six float fields, all 0.0–1.0)
- `PowerLevelResult` Pydantic model (`score: float`, `bracket: int`, `summary: str`, `breakdown: FactorBreakdown`)
- Signal scoring functions for each of the six factors (see design.md for formulas)
- `_compute_bracket(score: float) -> int` using score threshold table
- `_build_summary(score: float, breakdown: FactorBreakdown) -> str` — template-based one-sentence summary
- `estimate_power_level(cards: list[dict]) -> PowerLevelResult` — public entry point

**Field name note**: card dicts use `"description"` for oracle text and `"type"` for type line (matching `_row_to_card` output in `repository.py`). Do not expect `"oracle_text"` or `"type_line"`.

**Acceptance criteria**:
- A 100-card list with Sol Ring, Mana Crypt, Demonic Tutor, Vampiric Tutor, and 5 fetchlands produces a score >= 6.0
- An empty list returns score=1.0, bracket=1
- A list of 99 basic lands + 1 Commander produces score <= 3.0
- `estimate_power_level` is callable with no network access (unit-testable in isolation)

---

## Task 2 [core] — Write unit tests for scoring engine

**File**: `tests/test_power_level.py` (new file)

**Description**: Pytest unit tests covering the scoring engine. All fixtures use `scope="function"`.

**Test cases**:
- Empty deck → score=1.0, bracket=1
- Deck with 4 fast mana cards only → fast_mana breakdown >= 1.0, score elevated
- Deck with 5 tutor cards only → tutors breakdown = 1.0
- Deck with known combo pieces (Thassa's Oracle + Demonic Consultation) → combo_pieces > 0
- Low avg CMC deck (all CMC 1–2 spells) → cmc score high
- High avg CMC deck (all CMC 5+) → cmc score low
- Full premium mana base (10 fetchlands) → land_quality = 1.0
- `_compute_bracket`: verify all boundary values (score 3.0→1, 4.0→2, 6.0→3, 8.0→4)
- `_build_summary`: returns a non-empty string for any valid breakdown
- Integration: a representative cEDH-style input (fast mana + tutors + combos) produces score >= 8.0

**Acceptance criteria**:
- All tests pass with `pytest tests/test_power_level.py`
- No external I/O, no database connections, no HTTP calls in any test

---

## Task 3 [backend] — Implement backend service (caching layer)

**File**: `backend/api/services/power_level_service.py` (new file)

**Description**: Thin service that wraps `estimate_power_level` with an in-process cache.

**Implement**:
- Module-level `_cache: dict[tuple, tuple[PowerLevelResult, datetime]]` and `_CACHE_TTL_SECONDS = 300`
- Cache key: `(deck_id, user_id, card_count, updated_at_str)` where `card_count` is `len(deck["cards"])` and `updated_at_str` is `deck.get("updated_at", "")`.
- `get_power_level(deck_id: int, repo: DeckRepository, user_id: int) -> PowerLevelResult | None`
  1. Call `repo.get_deck_with_cards(deck_id, user_id=user_id)`; return `None` if deck is `None`
  2. Build cache key from result
  3. Return cached result if present and not expired
  4. Otherwise call `estimate_power_level(deck["cards"])`, store in cache, return result

**Acceptance criteria**:
- Two consecutive calls with the same deck (unchanged) produce exactly one call to `estimate_power_level` (cache hit on second call)
- A deck with a changed `updated_at` value produces a cache miss
- Returns `None` when deck is not found

---

## Task 4 [backend] — Add API endpoint

**File**: `backend/api/routes/decks.py`

**Description**: Register the new endpoint on the existing `router`.

**Add**:
```python
class PowerLevelBreakdownResponse(BaseModel):
    fast_mana: float
    tutors: float
    combo_pieces: float
    avg_cmc: float
    land_quality: float
    staple_density: float

class PowerLevelResponse(BaseModel):
    score: float
    bracket: int
    summary: str
    breakdown: PowerLevelBreakdownResponse
```

```python
@router.get("/{deck_id}/power-level", response_model=PowerLevelResponse)
async def get_deck_power_level(
    deck_id: int,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Return heuristic power level score and Commander Bracket for a deck."""
    from ..services.power_level_service import get_power_level
    result = get_power_level(deck_id, repo, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return result
```

**Note**: Import `get_power_level` inside the function body to keep the module-level import surface clean and consistent with the existing pattern in this codebase.

**Acceptance criteria**:
- `GET /api/decks/1/power-level` returns 200 with the correct JSON structure for an existing deck
- `GET /api/decks/9999/power-level` returns 404
- Endpoint appears in the OpenAPI docs at `/docs`
- Pydantic validation errors in request path params return 400 (handled by existing `validation_exception_handler`)

---

## Task 5 [backend] — Write API endpoint tests

**File**: `tests/test_deck_power_level_api.py` (new file)

**Description**: Integration-style tests for the endpoint using a mocked `DeckRepository`.

All fixtures use `scope="function"`.

**Test cases**:
- 200 response with valid score/bracket/summary/breakdown shape when deck exists
- 404 when `get_power_level` returns None (deck not found)
- Response score is within [1.0, 10.0]
- Response bracket is within {1, 2, 3, 4}
- 501 when no Postgres repo (mock `require_deck_repo` to raise HTTPException 501)

**Acceptance criteria**:
- All tests pass with `pytest tests/test_deck_power_level_api.py`
- No real database connections; `DeckRepository` is mocked

---

## Task 6 [frontend] — Add API types and client method

**File**: `frontend/src/api/client.ts`

**Description**: Add the TypeScript interface and API function.

**Add interfaces** (after `BatchAddResult`):
```typescript
export interface PowerLevelBreakdown {
  fast_mana: number;
  tutors: number;
  combo_pieces: number;
  avg_cmc: number;
  land_quality: number;
  staple_density: number;
}

export interface PowerLevelResponse {
  score: number;
  bracket: number;
  summary: string;
  breakdown: PowerLevelBreakdown;
}
```

**Add to `api` object** (after `importDeckText`):
```typescript
getDeckPowerLevel: async (deckId: number): Promise<PowerLevelResponse> => {
  const response = await apiFetch(`${API_BASE}/decks/${deckId}/power-level`);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    if (response.status === 404) throw new Error('Deck not found');
    if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
    throw new Error((err as { detail?: string }).detail || 'Failed to fetch power level');
  }
  return response.json();
},
```

**Acceptance criteria**:
- TypeScript compiles without errors (`npm run build`)
- `api.getDeckPowerLevel` is callable with a number argument and resolves to `PowerLevelResponse`

---

## Task 7 [frontend] — Power level badge on DeckCardButton

**File**: `frontend/src/pages/DeckBuilder.tsx`

**Description**: Add a lazy-loaded power level badge to each `DeckCardButton`.

**Changes inside `DeckCardButton`**:
1. Add `useQuery` call:
   ```typescript
   const { data: powerLevel } = useQuery({
     queryKey: ['deckPowerLevel', deck.id],
     queryFn: () => api.getDeckPowerLevel(deck.id),
     retry: false,
     staleTime: 5 * 60 * 1000,  // 5 min, matching backend cache TTL
   });
   ```
2. Add bracket-to-colour helper (inline const or small function):
   ```typescript
   const BRACKET_COLORS = ['', 'bg-green-600', 'bg-blue-600', 'bg-orange-500', 'bg-red-600'];
   ```
3. Render badge (absolute position, bottom-right, only when `powerLevel` is defined):
   ```tsx
   {powerLevel && (
     <span
       className={`absolute bottom-2 right-2 z-20 text-white text-xs font-semibold px-1.5 py-0.5 rounded ${BRACKET_COLORS[powerLevel.bracket]}`}
       title={powerLevel.summary}
     >
       B{powerLevel.bracket} · {powerLevel.score.toFixed(1)}
     </span>
   )}
   ```

**Acceptance criteria**:
- Badge visible on deck tiles when power level loads
- Badge absent (no spinner, no error text) when loading or on error
- `title` attribute shows the summary string (native browser tooltip)
- No TypeScript errors
- Existing snapshot tests still pass (badge is conditionally rendered, test mock returns undefined by default)

---

## Task 8 [frontend] — Power level section in DeckDetailModal

**File**: `frontend/src/components/DeckDetailModal.tsx`

**Description**: Add a power level display to the modal header area.

**Changes**:
1. Add `useQuery` for power level (same query key as Task 7 — cache deduplication):
   ```typescript
   const { data: powerLevel } = useQuery({
     queryKey: ['deckPowerLevel', deckId],
     queryFn: () => api.getDeckPowerLevel(deckId),
     retry: false,
     staleTime: 5 * 60 * 1000,
   });
   ```
2. Add `BRACKET_LABELS` map:
   ```typescript
   const BRACKET_LABELS: Record<number, string> = {
     1: 'Casual',
     2: 'Mid Power',
     3: 'High Power',
     4: 'Optimised',
   };
   ```
3. Render the power level section in the header row (between mana curve and action buttons), only when `powerLevel` is defined:
   ```tsx
   {powerLevel && (
     <div
       className="relative group flex flex-col items-center shrink-0 cursor-help"
       title={powerLevel.summary}
     >
       <span className={`text-lg font-bold ${bracketTextColor(powerLevel.bracket)}`}>
         {powerLevel.score.toFixed(1)}
       </span>
       <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
         {BRACKET_LABELS[powerLevel.bracket]} · B{powerLevel.bracket}
       </span>
     </div>
   )}
   ```
4. Add `bracketTextColor` helper (inline):
   ```typescript
   const bracketTextColor = (b: number) => {
     if (b === 1) return 'text-green-500';
     if (b === 2) return 'text-blue-500';
     if (b === 3) return 'text-orange-500';
     return 'text-red-500';
   };
   ```

**Acceptance criteria**:
- Power level score and bracket label appear in the modal header for a deck with cards
- Colour of score text reflects bracket
- `title` tooltip shows full summary string
- Section absent when loading or on error (no visible placeholder)
- Existing `DeckDetailModal.test.tsx` tests still pass
- No TypeScript errors

---

## Task 9 [frontend] — Add i18n keys

**File**: `frontend/src/locales/en.json`, `frontend/src/locales/es.json`

**Description**: Add localisation keys for the power level feature.

**Keys to add under a new `powerLevel` namespace**:
```json
"powerLevel": {
  "badge": "B{{bracket}} · {{score}}",
  "casual": "Casual",
  "midPower": "Mid Power",
  "highPower": "High Power",
  "optimised": "Optimised",
  "bracket": "Bracket {{bracket}}",
  "loading": "Calculating..."
}
```

Add equivalent Spanish translations in `es.json`.

**Note**: Tasks 7 and 8 initially use hardcoded English strings for simplicity. This task upgrades them to use `useTranslation()`. If implementing in a single pass, use `t('powerLevel.casual')` etc. directly.

**Acceptance criteria**:
- Both `en.json` and `es.json` contain the `powerLevel` namespace
- No missing key warnings in browser console when navigating to DeckBuilder page

---

## Task 10 [backend] — Trigger updated_at bump on deck_cards mutations (recommended)

**File**: `deckdex/storage/deck_repository.py`

**Description**: After any `add_card`, `remove_card`, `add_cards_batch`, or `import` mutation, explicitly update `decks.updated_at` for the affected deck. This makes the service-layer cache key reliably reflect the true card composition.

**Change pattern** (add at end of each mutating transaction, before `conn.commit()`):
```python
conn.execute(
    text("UPDATE decks SET updated_at = NOW() AT TIME ZONE 'utc' WHERE id = :deck_id"),
    {"deck_id": deck_id},
)
```

**Acceptance criteria**:
- After `add_card`, `deck.updated_at` changes
- After `remove_card`, `deck.updated_at` changes
- Existing deck mutation tests still pass

---

## Dependency Order

```
Task 1 (scoring engine)
  └── Task 2 (engine tests)
  └── Task 3 (service layer)
        └── Task 4 (API endpoint)
              └── Task 5 (endpoint tests)
              └── Task 6 (client types)
                    └── Task 7 (tile badge)
                    └── Task 8 (modal section)
                          └── Task 9 (i18n)

Task 10 (updated_at bump) — independent, can run in parallel with any task
```
