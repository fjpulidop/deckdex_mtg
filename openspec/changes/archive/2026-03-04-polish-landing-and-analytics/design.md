## Context

The app is feature-complete but has visible polish gaps. The landing page BentoGrid shows raw dimension text ("Collection View (600x500px)") as placeholder content, GitHub links use `yourusername`, and `InteractiveDemo.tsx` is dead code. The analytics drill-down has a positional argument bug that silently breaks `set_name` and price filtering, plus `color_identity` and `cmc` are not wired through the backend despite `color_identity` already being supported in `filter_collection`.

## Goals / Non-Goals

**Goals:**
- Fix the positional argument bug in analytics/stats backend calls
- Complete drill-down filtering for all 4 dimensions (rarity, color_identity, cmc, set_name)
- Replace BentoGrid placeholders with styled visual content (gradient illustrations with icons)
- Fix GitHub placeholder links
- Remove dead code and debug artifacts

**Non-Goals:**
- Real screenshots (would need Playwright CI pipeline — out of scope)
- New analytics chart types
- Landing page redesign

## Decisions

### D1: Fix positional arg bug → use keyword arguments

The `_filtered_collection` helper in `analytics.py` calls `filter_collection` positionally, skipping `color_identity` and shifting `set_name` into the wrong slot. Same bug in `stats.py`.

**Fix:** Switch all `filter_collection` calls to keyword arguments. This is the safest approach — it makes the code resilient to future parameter order changes.

**Alternative considered:** Insert `None` positionally for `color_identity`. Rejected because it's fragile and the same bug could recur if `filter_collection` adds parameters.

### D2: Add `cmc` filter to `filter_collection`

`color_identity` is already supported in `filter_collection`. `cmc` is not. We need to add a `cmc` parameter that matches the same bucketing logic used in the analytics CMC endpoint (0–6 as exact match, "7+" for >= 7, "Unknown" for null/unparseable).

**Layer:** `backend/api/filters.py` — this is the shared filter module, correct place for it.

### D3: Add `color_identity` and `cmc` as Query params on analytics + stats endpoints

All 4 analytics endpoints and the stats endpoint need new optional query parameters. Thread them through `_filtered_collection` and `_cache_key`.

### D4: BentoCard placeholders → styled gradient illustrations with icons

Instead of real screenshots (which need Playwright + a running app), replace the placeholder boxes with styled gradient panels featuring relevant Lucide icons and a subtle visual. Each card already has a gradient color scheme — enhance the placeholder area to feel intentional rather than "TODO".

Remove the `label` prop entirely from `BentoCard` — it was only used for dimension annotations.

**Alternative considered:** Using `InteractiveDemo.tsx` as a live widget in one card. Rejected — it would be inconsistent with the other cards and adds unnecessary bundle weight on the landing page.

### D5: GitHub links → use actual repo URL

Replace `yourusername` with `fjpulidop` in BentoGrid and FinalCTA. The repo is `fjpulidop/deckdex-mtg` based on the PR history.

### D6: Delete `InteractiveDemo.tsx`

Dead code. The `/demo` route uses `DemoProvider` + full `Dashboard`, making this standalone component redundant. Clean delete.

### D7: Delete debug images

`debug-demo.png` and `debug-landing.png` are untracked debug artifacts in `frontend/public/`. Delete them.

## Risks / Trade-offs

- **Cache invalidation**: Adding `color_identity` and `cmc` to the cache key means existing cached results won't match new requests — this is correct behavior (new params = new key). The 30s TTL means stale entries auto-expire quickly.
- **BentoGrid without real screenshots**: Styled gradient illustrations are better than dimension text but still not as compelling as real screenshots. This is an acceptable trade-off for now.
