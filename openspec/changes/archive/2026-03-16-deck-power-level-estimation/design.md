# Technical Design: Deck Power Level Auto-Estimation

---

## Architecture Overview

```
GET /api/decks/{deck_id}/power-level
        |
        v
backend/api/routes/decks.py (new endpoint, auth guard)
        |
        v
backend/api/services/power_level_service.py   <-- thin adapter/cache layer
        |
        v
deckdex/services/power_level.py               <-- pure scoring engine (no I/O)
        |
        v
DeckRepository.get_deck_with_cards()          <-- existing data access (no new queries)
```

The scoring engine (`deckdex/services/power_level.py`) receives a pre-loaded list of card dicts (identical to the structure already returned by `get_deck_with_cards`) and returns a structured result. It performs zero database access — all I/O is handled by the route handler.

---

## Scoring Algorithm

### Signal Definitions

The engine scores the following six signals, each producing a normalized contribution (0.0–1.0) that feeds into the final weighted sum.

#### 1. Fast Mana Density (weight: 2.5)

Fast mana is the single strongest power indicator. Cards producing mana acceleration in the first two turns compress the effective game speed of the entire deck.

**Detection**: card `name` exact-match against a curated set. Using name matching (not oracle text) is intentional: oracle text varies across printings, and name is the canonical identifier.

```
FAST_MANA = {
    "sol ring", "mana crypt", "mana vault", "chrome mox", "mox diamond",
    "mox opal", "lotus petal", "dark ritual", "cabal ritual", "elvish spirit guide",
    "simian spirit guide", "ancient tomb", "gaea's cradle", "serra's sanctum",
    "mishra's workshop", "jeweled lotus", "lotus bloom", "mox amber",
    "mana drain",           # free counterspell that produces mana
    "dockside extortionist", # conditional but ubiquitous
    "vault of whispers", "seat of the synod", "tree of tales",  # artifact lands
    "great furnace", "ancient den", "darksteel citadel",
}
```

Score = min(fast_mana_count / 4.0, 1.0)
- 0 fast mana cards → 0.0
- 1 card → 0.25
- 4+ cards → 1.0 (capped)

#### 2. Tutor Density (weight: 2.0)

Tutors compress variance, converting a 99-card random sample into an on-demand toolbox.

**Detection**: oracle_text substring search for "search your library" (case-insensitive). This matches all Demonic Tutor variants, Enlightened Tutor, Vampiric Tutor, Imperial Seal, etc. False positives (fetchlands, basic land cyclers) are acceptable noise at this level; they genuinely do provide consistency.

Score = min(tutor_count / 5.0, 1.0)
- 0 tutors → 0.0
- 5+ tutors → 1.0

#### 3. Combo Infrastructure (weight: 2.0)

Two-card infinite combos dramatically raise the threat ceiling of any deck.

**Detection**: keyword presence + oracle text patterns. The engine checks for cards that:
- Contain "infinite" in oracle_text, OR
- Are well-known combo enablers by name:

```
COMBO_PIECES = {
    "thassa's oracle", "demonic consultation", "tainted pact",
    "thoracle",         # alias handled by name normalisation
    "labman",           # Laboratory Maniac
    "laboratory maniac", "jace, wielder of mysteries",
    "isochron scepter", "dramatic reversal",
    "staff of domination", "umbral mantle", "sword of the paruns",
    "basalt monolith", "rings of brighthearth",
    "splinter twin", "kiki-jiki, mirror breaker",
    "devoted druid", "vizier of remedies",
    "heliod, sun-crowned", "walking ballista",
    "necropotence", "ad nauseam",   # storm enablers / near-combo
}
```

Score = min(combo_count / 3.0, 1.0)
- 0 combo pieces → 0.0
- 3+ → 1.0

#### 4. Average CMC (weight: 1.5)

Lower average CMC correlates with tempo and resilience. Measured on non-land cards only.

Scoring table:
- avg_cmc <= 1.5 → 1.0
- avg_cmc <= 2.0 → 0.85
- avg_cmc <= 2.5 → 0.70
- avg_cmc <= 3.0 → 0.55
- avg_cmc <= 3.5 → 0.40
- avg_cmc <= 4.0 → 0.25
- avg_cmc > 4.0 → 0.10

#### 5. Land Base Quality (weight: 1.0)

Shock lands, fetch lands, and dual lands provide reliable, early mana fixing that enables consistent fast starts.

**Detection**: name exact-match against curated set covering the ten original duals, ten shocklands, ten fetchlands, and the ten Zendikar battle lands.

Score = min(premium_land_count / 10.0, 1.0)
- 0 premium lands → 0.0
- 10+ → 1.0

#### 6. Staple Density (weight: 1.0)

Well-known high-power staples that don't fit the categories above.

**Detection**: EDHREC rank (already stored in `cards.edhrec_rank`). Cards with edhrec_rank <= 50 are considered staples.

Score = min(staple_count / 10.0, 1.0)

---

### Composite Score Calculation

```
raw = (
    fast_mana_score  * 2.5 +
    tutor_score      * 2.0 +
    combo_score      * 2.0 +
    cmc_score        * 1.5 +
    land_score       * 1.0 +
    staple_score     * 1.0
) / (2.5 + 2.0 + 2.0 + 1.5 + 1.0 + 1.0)  # = 10.0

score = round(max(1.0, min(10.0, raw * 10)), 1)
```

Division by the sum of weights normalises the range to [0, 1]; multiply by 10 and clamp to [1, 10].

---

### Commander Bracket Mapping

| Score | Bracket | Label          |
|-------|---------|----------------|
| 1–3   | 1       | Casual         |
| 4–5   | 2       | Mid Power      |
| 6–7   | 3       | High Power     |
| 8–10  | 4       | Optimised/cEDH |

---

### Summary String Generation

The summary is assembled from the dominant signals (those scoring above 0.5):

```python
def _build_summary(score, dominant_factors, avg_cmc):
    # "7 — strong tempo deck with premium mana base but few tutors"
```

Template components:
- Opening: `"{score:.0f} — "`
- Power adjective: casual / mid-power / strong / highly optimised
- Archetype hint from avg_cmc + land quality
- Notable positives (signals >= 0.7)
- Notable absences (expected signals that scored 0.0)

---

## New Files

### `deckdex/services/power_level.py`

Pure Python module with no dependencies beyond stdlib and the card dicts already provided by `get_deck_with_cards`. Accepts `List[Dict]` where each dict has keys: `name`, `oracle_text` (stored as `description` in DB), `type_line` (stored as `type`), `cmc`, `keywords`, `edhrec_rank`, `is_commander`, `quantity`.

**Note on field name mapping**: The card dicts returned by `_row_to_card` in `repository.py` map DB column `description` → `"description"` (oracle text) and `type_line` → `"type"`. The service must use these aliased names.

Public API:
```python
def estimate_power_level(cards: list[dict]) -> PowerLevelResult
```

`PowerLevelResult` is a Pydantic model (or dataclass) with:
```python
class FactorBreakdown(BaseModel):
    fast_mana: float
    tutors: float
    combo_pieces: float
    avg_cmc: float
    land_quality: float
    staple_density: float

class PowerLevelResult(BaseModel):
    score: float          # 1.0 – 10.0
    bracket: int          # 1 – 4
    summary: str          # "7 — strong tempo..."
    breakdown: FactorBreakdown
```

### `backend/api/services/power_level_service.py`

Thin service layer responsible for:
1. Cache lookup (in-process dict keyed by `(deck_id, card_count, updated_at)`).
2. Calling `repo.get_deck_with_cards()` when cache misses.
3. Calling `deckdex.services.power_level.estimate_power_level()`.
4. Storing result in cache with a 5-minute TTL.

Cache key includes `card_count` and `updated_at` so any deck mutation (add/remove card, import) will produce a cache miss without an explicit invalidation call.

```python
_cache: dict[tuple, tuple[PowerLevelResult, datetime]] = {}
_CACHE_TTL_SECONDS = 300

def get_power_level(deck_id: int, repo: DeckRepository, user_id: int) -> PowerLevelResult | None:
    ...
```

Returns `None` if the deck is not found (caller raises 404).

---

## New API Endpoint

### `GET /api/decks/{deck_id}/power-level`

**File**: `backend/api/routes/decks.py` (appended to existing router)

**Auth**: `get_current_user_id` — same guard as all other deck endpoints.

**Response model**:
```python
class PowerLevelResponse(BaseModel):
    score: float
    bracket: int
    summary: str
    breakdown: dict  # keys: fast_mana, tutors, combo_pieces, avg_cmc, land_quality, staple_density
```

**Status codes**:
- 200: success
- 404: deck not found or does not belong to user
- 501: no Postgres configured (via `require_deck_repo`)

**Example response**:
```json
{
  "score": 7.2,
  "bracket": 3,
  "summary": "7 — strong tempo deck with premium mana base but few tutors",
  "breakdown": {
    "fast_mana": 0.75,
    "tutors": 0.2,
    "combo_pieces": 0.33,
    "avg_cmc": 0.7,
    "land_quality": 0.6,
    "staple_density": 0.5
  }
}
```

---

## Frontend Changes

### `frontend/src/api/client.ts`

Add new interface and API method:

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

### `frontend/src/pages/DeckBuilder.tsx` — Power Level Badge on `DeckCardButton`

`DeckCardButton` receives the `DeckListItem` which does not currently include power level data. Two options:

**Option A (chosen)**: Fetch power level lazily per tile using `useQuery` inside `DeckCardButton`, keyed by `deck.id`. The call is made only when the tile is rendered. This avoids changing the `DeckListItem` type and keeps the badge self-contained.

**Option B**: Batch fetch all power levels on page load. Requires a new batch endpoint. Deferred to a future optimisation.

`DeckCardButton` additions:
- New `useQuery` call: `queryKey: ['deckPowerLevel', deck.id]`, `queryFn: () => api.getDeckPowerLevel(deck.id)`.
- Render a small badge in the bottom-right of the tile: bracket number + score, e.g. `B3 · 7.2`.
- Badge styling: coloured pill using bracket-to-colour mapping:
  - Bracket 1 → green (`bg-green-600`)
  - Bracket 2 → blue (`bg-blue-600`)
  - Bracket 3 → orange (`bg-orange-500`)
  - Bracket 4 → red (`bg-red-600`)
- While loading: render nothing (badge simply absent — avoids layout shift).
- On error: render nothing (power level is non-critical; badge absence is acceptable degradation).

### `frontend/src/components/DeckDetailModal.tsx` — Power Level Section

A "Power Level" section is added to the modal header row, positioned after the mana curve and before the action buttons.

Contents:
- Large score number (e.g. "7.2") styled with the bracket colour.
- Bracket label (e.g. "High Power · B3").
- Tooltip (hover) showing the `summary` string and a mini-breakdown table.
- The data is fetched via `useQuery(['deckPowerLevel', deckId])` — same query key as the tile badge, so TanStack Query's cache ensures a single network request when both tile and modal are visible.

The power level section renders as a loading skeleton while the query is in-flight, and is omitted gracefully on error.

---

## Caching Strategy

No database columns are added. The in-process cache in `power_level_service.py` lives in the backend process memory.

**Cache key**: `(deck_id, user_id, card_count, updated_at_iso_string)`

**Why `user_id` in the key**: The `decks` table is user-scoped, but the cache is process-wide. Including `user_id` prevents a theoretical collision if two users happen to share the same `deck_id` across different PostgreSQL schemas (though the current schema uses a single shared table with `user_id` column — this is a safety measure, not a real risk).

**TTL**: 5 minutes. Short enough that a user who modifies their deck and re-opens the detail view gets a fresh score within a typical session. Long enough to absorb rapid navigation between tiles.

**Invalidation on mutation**: The cache key incorporates `card_count` and `updated_at`. After any `add_card`, `remove_card`, `add_cards_batch`, or `import` operation, the deck's `updated_at` changes (the `update_name` route already sets `updated_at = NOW()`). However, `add_card` and `remove_card` do NOT currently update `decks.updated_at`. A migration or explicit update should be added so the cache key reflects card mutations.

**Fallback**: If the cache lookup encounters a stale key, it recomputes. The entire algorithm runs in O(n) over the card list and completes in microseconds for 100 cards — there is no meaningful performance risk in a cache miss.

---

## Migration Requirements

None required for the core feature. The scoring algorithm uses only existing `cards` columns (`name`, `description`/oracle_text, `type`, `cmc`, `edhrec_rank`).

**Recommended follow-up migration** (not in scope for this change, flagged as a task): Add a `CASCADE UPDATE updated_at` trigger on the `deck_cards` table so that any INSERT/DELETE to `deck_cards` propagates an `updated_at` bump to the parent `decks` row. This makes the cache invalidation strategy bullet-proof.
