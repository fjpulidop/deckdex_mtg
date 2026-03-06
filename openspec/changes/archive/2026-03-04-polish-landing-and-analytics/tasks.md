## 1. Fix backend filter bug and add missing filters

- [x] 1.1 Add `cmc` parameter to `filter_collection` in `backend/api/filters.py` with bucket matching (0-6 exact, "7+" for >=7, "Unknown" for null/unparseable)
- [x] 1.2 Fix `_filtered_collection` in `backend/api/routes/analytics.py` to use keyword arguments and add `color_identity` + `cmc` parameters
- [x] 1.3 Add `color_identity` and `cmc` as Query parameters to all 4 analytics endpoints and thread through `_filtered_collection` and `_cache_key`
- [x] 1.4 Fix `filter_collection` call in `backend/api/routes/stats.py` to use keyword arguments and add `color_identity` + `cmc` query params

## 2. Fix frontend analytics drill-down

- [x] 2.1 Update `buildParams` in `Analytics.tsx` to pass `color_identity` and `cmc` to the API
- [x] 2.2 Update `statsParams` in `Analytics.tsx` to pass `color_identity` and `cmc` to the stats API
- [x] 2.3 Update `api.getStats` / `useStats` if needed to accept and forward `color_identity` and `cmc` params

## 3. Polish landing page

- [x] 3.1 Replace BentoCard placeholder with styled gradient illustration + icon (remove `label` prop, add icon-based visual)
- [x] 3.2 Update BentoGrid to pass icon elements for the illustration area instead of label strings
- [x] 3.3 Fix GitHub links in BentoGrid.tsx — replace `yourusername` with `fjpulidop`
- [x] 3.4 Fix GitHub link in FinalCTA.tsx — replace `yourusername` with `fjpulidop`

## 4. Cleanup

- [x] 4.1 Delete `frontend/src/components/landing/InteractiveDemo.tsx`
- [x] 4.2 Delete `frontend/public/debug-demo.png` and `frontend/public/debug-landing.png`
