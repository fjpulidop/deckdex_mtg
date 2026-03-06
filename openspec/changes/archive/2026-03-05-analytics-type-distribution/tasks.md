# Tasks: Type-Line Distribution Chart

Each task is atomic and independently committable. Execute in order.

---

## Task 1 — Backend: TypeCount model and _extract_primary_type helper

**Files:** `backend/api/routes/analytics.py`

**What to do:**
1. Add `_TYPE_PRIORITY` constant list after the `_VALID_COLORS` block.
2. Add `_extract_primary_type(type_line: str) -> str` function.
3. Add `TypeCount(BaseModel)` with fields `type_line: str`, `count: int`.

**Acceptance criteria:**
- `_extract_primary_type("Legendary Creature — Dragon")` returns `"Creature"`
- `_extract_primary_type("Artifact Creature — Golem")` returns `"Creature"`
  (Creature has higher priority than Artifact)
- `_extract_primary_type("Basic Land — Forest")` returns `"Land"`
- `_extract_primary_type("")` returns `"Other"`
- `_extract_primary_type("Scheme")` returns `"Other"`
- The function handles `None` gracefully (treat as empty string)

**Dependencies:** none

---

## Task 2 — Backend: GET /api/analytics/type endpoint

**Files:** `backend/api/routes/analytics.py`

**What to do:**
1. Add the `analytics_type` route function decorated with
   `@router.get("/type", response_model=list[TypeCount])`.
2. Signature must include all standard filter Query params identical to the
   other four analytics endpoints (search, rarity, type_filter aliased as
   "type", set_name, price_min, price_max, color_identity, cmc, user_id).
3. Use `_cache_key("type", ...)` and `_get_cached` / `_set_cached`.
4. Aggregate using Counter: for each card call `_extract_primary_type` on
   `c.get("type_line") or c.get("type") or ""`, add `quantity`.
5. Sort result descending by count.
6. Wrap in try/except, log errors, raise HTTPException 500.

**Acceptance criteria:**
- `GET /api/analytics/type` returns 200 with a list of `{type_line, count}`
- With `?type=Creature` the endpoint filters to creatures before aggregating
  (result will be a single entry "Creature" with the filtered count)
- Response is cached for 30 seconds

**Dependencies:** Task 1

---

## Task 3 — Frontend: TYPE_COLORS constant in constants.ts

**Files:** `frontend/src/components/analytics/constants.ts`

**What to do:**
Add `TYPE_COLORS` record after `RARITY_COLORS`:
