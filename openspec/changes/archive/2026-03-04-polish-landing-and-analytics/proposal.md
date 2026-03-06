## Why

The app is feature-complete for its current scope but has visible polish gaps that make it look unfinished: the landing page BentoGrid shows raw placeholder text with pixel dimensions, GitHub links use `yourusername`, there's dead code (`InteractiveDemo.tsx`), and the analytics drill-down has a silent positional argument bug that breaks `set_name`/`price` filtering plus missing `color_identity`/`cmc` drill-down support.

## What Changes

- **Fix positional argument bug** in `backend/api/analytics.py` and stats route — `set_name` currently falls into the `color_identity` slot, shifting all subsequent args
- **Add `color_identity` and `cmc` as query params** to analytics and stats endpoints, thread through `_filtered_collection`
- **Add `cmc` filtering** to `filter_collection` in `backend/api/filters.py`
- **Update frontend `buildParams`/`statsParams`** in `Analytics.tsx` to pass `color_identity` and `cmc` to the API
- **Replace BentoGrid placeholders** — remove dimension-text labels, use meaningful visual content (gradient illustrations or styled placeholders with icons)
- **Fix GitHub links** — replace `yourusername` with `fjpulidop` in `BentoGrid.tsx` and `FinalCTA.tsx`
- **Remove `InteractiveDemo.tsx`** — dead code, not mounted anywhere
- **Clean up debug images** — remove `debug-demo.png` and `debug-landing.png` from `frontend/public/`

## Non-goals

- Adding Playwright screenshot automation (existing script works, just needs to be run manually)
- Redesigning the landing page layout or adding new sections
- Adding new analytics chart types

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `analytics-dashboard`: Adding `color_identity` and `cmc` as drill-down filter dimensions, fixing positional argument bug in backend filter calls
- `landing-page`: Replacing placeholder content in BentoGrid, fixing GitHub links, removing dead code

## Impact

- `backend/api/analytics.py` — fix positional args, add query params
- `backend/api/filters.py` — add `cmc` filter support
- `backend/api/routes/stats.py` — fix positional args, add query params
- `frontend/src/pages/Analytics.tsx` — pass `color_identity`/`cmc` to API
- `frontend/src/components/landing/BentoGrid.tsx` — replace placeholders, fix links
- `frontend/src/components/landing/BentoCard.tsx` — update to render visual content instead of label text
- `frontend/src/components/landing/FinalCTA.tsx` — fix GitHub link
- `frontend/src/components/landing/InteractiveDemo.tsx` — delete
- `frontend/public/debug-*.png` — delete
