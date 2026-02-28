## Context

The dashboard currently shows a static "Top 5 most valuable cards" widget and a redundant title block ("DeckDex MTG / Manage your Magic: The Gathering collection") that duplicates the navbar branding. The color filter buttons display plain letters (W, U, B, R, G) instead of leveraging the Scryfall mana symbol SVGs already used in ManaText and card detail views.

The backend follows a pattern of thin FastAPI routes calling into services/utilities, with collection data accessed through `get_cached_collection()` and filtered via `filter_collection()`. Analytics endpoints in `analytics.py` demonstrate the caching and aggregation patterns we'll reuse.

## Goals / Non-Goals

**Goals:**
- Replace Top 5 widget with an interactive Collection Insights component that provides recurring value
- Implement 17 predefined insight queries that run server-side as pure computation (no LLM, no external API costs)
- Contextual suggestion chips that rotate based on collection state signals
- Rich, animated response visualizations (value, distribution, list, comparison, timeline)
- Use Scryfall mana symbol SVGs in color filter buttons and distribution visualizations
- Remove dashboard title block; navbar already provides branding
- i18n-ready data model with key-based labels (translate later, not now)

**Non-Goals:**
- LLM/AI-powered answers — all insights are deterministic SQL/aggregation queries
- Multi-language UI in this change — we prepare the structure but ship English only
- Price history tracking — insights use current snapshot data only
- Custom user-defined questions — catalog is predefined and extensible by developers only

## Decisions

### 1. Insights as a dispatch service (not individual endpoints per question)

**Choice:** Single `InsightsService` class with `execute(insight_id)` dispatch to internal methods, exposed through 3 endpoints (`GET /catalog`, `GET /suggestions`, `POST /{insight_id}`).

**Alternative considered:** One endpoint per insight (e.g., `GET /api/insights/total-value`). Rejected because 17+ individual routes adds clutter and each would need identical auth + caching boilerplate. The dispatch pattern matches how analytics.py aggregates behind a few endpoints.

**Rationale:** Adding a new insight = add entry to catalog + implement one method. No new route needed. The POST verb for execute is intentional — the action "runs a computation" rather than "fetches a resource".

### 2. Catalog lives in backend, not frontend

**Choice:** Question catalog (IDs, labels, keywords, categories) is defined server-side and fetched via `GET /api/insights/catalog`. Frontend uses it for autocomplete matching.

**Alternative considered:** Hardcode catalog in frontend JSON file. Rejected because the backend needs the catalog too (for validation and suggestion engine) — single source of truth avoids drift.

**Rationale:** When we add i18n, the backend can return localized labels based on a locale header. Frontend never needs to maintain its own copy.

### 3. Suggestion engine uses lightweight signal queries

**Choice:** `GET /api/insights/suggestions` runs ~5 cheap COUNT/EXISTS queries to detect collection signals (recent activity, duplicates, missing colors, cards without price, collection size, value variance), then scores and returns the top 5-6 most relevant insight IDs.

**Alternative considered:** Always return the same static suggestions. Rejected because the whole point is replacing a static widget with something that feels alive.

**Rationale:** The signal queries are O(n) scans over the cached collection (same data already in memory from `get_cached_collection()`), not additional DB round-trips. Lightweight.

### 4. Response types as a discriminated union

**Choice:** 5 response types, each with a typed `data` shape:

| Type | Data Shape | Visualization |
|------|-----------|---------------|
| `value` | `{ primary_value, unit?, breakdown?: {label, value}[] }` | Big number + optional sub-breakdown |
| `distribution` | `{ items: {label, count, value?, percentage, color?}[] }` | Horizontal bars with mana symbols for colors |
| `list` | `{ items: {card_id?, name, detail, image_url?}[] }` | Ranked list with optional thumbnails |
| `comparison` | `{ items: {label, present: boolean, detail?}[] }` | Check/cross icons per item |
| `timeline` | `{ items: {period, count, value?}[] }` | Horizontal bars by period |

**Rationale:** Frontend implements one renderer per type. New insights only need to return the right type — no new UI code needed.

### 5. Animations via CSS transitions (no animation library)

**Choice:** All response animations (count-up numbers, bar growth, staggered fade-in) use Tailwind transitions + inline `transitionDelay` for stagger effects.

**Alternative considered:** Framer Motion or React Spring. Rejected — adds bundle size for effects achievable with CSS. The animations are simple (grow, fade, slide) and don't need spring physics.

### 6. Mana symbols in filters: reuse card-symbol CSS

**Choice:** Replace the letter text in color filter buttons with `<span className="card-symbol card-symbol-{symbol}">` wrapped inside the existing circular button. Same approach for color distribution bars in insight responses.

**Rationale:** Zero new infrastructure. The Scryfall CSS (`mana-symbols-scryfall.css`) is already imported globally and handles all WUBRG symbols.

### 7. Service file placement

**Choice:** New file at `backend/api/services/insights_service.py`, following the existing pattern of `backend/api/services/`. Route at `backend/api/routes/insights.py`.

**Rationale:** Consistent with existing `card_image_service.py`, `processor_service.py`, `scryfall_service.py` placement.

### 8. i18n preparation without i18n framework

**Choice:** Define a `label_key` field on each insight question (e.g., `insights.total_value.question`) but use plain English strings as the actual display text for now. The response `answer_text` also gets a key. When i18n is added, these keys map to translation files.

**Rationale:** Minimal overhead now — just a string field that's currently unused by the frontend. No i18n library dependency yet.

## Risks / Trade-offs

**[Performance] Collection scanned multiple times for suggestions** → The suggestion engine runs ~5 lightweight passes over the cached collection. Mitigation: `get_cached_collection()` already caches in memory for 30s; the signal queries are simple counters, not full aggregations. For collections under 10k cards this is negligible.

**[UX] 17 insights may overwhelm autocomplete** → Mitigation: Categorized results in dropdown, contextual chips surface the most relevant 5-6. Users don't need to browse all 17.

**[Maintenance] Each new insight requires backend + catalog entry** → This is intentional. The catalog is the contract. Mitigation: Adding an insight is ~20 lines of Python + 1 catalog entry.

**[Data gaps] Some insights depend on fields that may be empty** → Cards without `created_at`, `color_identity`, or `price` can skew results. Mitigation: Each insight handles nulls gracefully and some insights specifically surface these gaps (e.g., `no_price`).
