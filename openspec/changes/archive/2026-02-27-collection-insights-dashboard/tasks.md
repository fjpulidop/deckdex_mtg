## 1. Dashboard cleanup (navbar + title)

- [x] 1.1 Update Navbar logo area to include subtle "MTG" suffix alongside "DeckDex"
- [x] 1.2 Remove the title block (h1 "DeckDex MTG" + subtitle) from Dashboard.tsx
- [x] 1.3 Remove TopValueCards import and usage from Dashboard.tsx; remove the unfiltered allCardsData query if no longer needed

## 2. Mana icons in color filters

- [x] 2.1 Replace plain letter text in Filters.tsx color toggle buttons with `card-symbol card-symbol-{symbol}` spans; adjust button sizing if needed to fit the SVG icons

## 3. Backend: Insights catalog and service

- [x] 3.1 Create `backend/api/services/insights_service.py` with the InsightsCatalog (17 questions with id, label, label_key, keywords, category, icon, response_type, popular)
- [x] 3.2 Implement InsightsService.execute() dispatch method and all 3 summary insights: `total_value`, `total_cards`, `avg_card_value`
- [x] 3.3 Implement all 5 distribution insights: `by_color`, `by_rarity`, `by_set`, `value_by_color`, `value_by_set`
- [x] 3.4 Implement all 3 ranking insights: `most_valuable`, `least_valuable`, `most_collected_set`
- [x] 3.5 Implement all 4 patterns insights: `duplicates`, `missing_colors`, `no_price`, `singleton_sets`
- [x] 3.6 Implement all 3 activity insights: `recent_additions`, `monthly_summary`, `biggest_month`
- [x] 3.7 Implement InsightsSuggestionEngine with signal detection (recent activity, duplicates, missing colors, no price, collection size, value variance) and weighted scoring

## 4. Backend: Insights API routes

- [x] 4.1 Create `backend/api/routes/insights.py` with `GET /api/insights/catalog`, `GET /api/insights/suggestions`, and `POST /api/insights/{insight_id}` endpoints (auth-gated via get_current_user_id)
- [x] 4.2 Register insights router in `backend/api/main.py`

## 5. Frontend: API client and hooks

- [x] 5.1 Add insights API methods to `frontend/src/api/client.ts`: `getInsightsCatalog()`, `getInsightsSuggestions()`, `executeInsight(id)`
- [x] 5.2 Add TanStack Query hooks in `frontend/src/hooks/useApi.ts`: `useInsightsCatalog()`, `useInsightsSuggestions()`, `useInsightExecute()`

## 6. Frontend: CollectionInsights component

- [x] 6.1 Create `CollectionInsights.tsx` with the search input, autocomplete dropdown (fuzzy keyword matching against catalog), and suggestion chips layout
- [x] 6.2 Implement suggestion chips with hover effects (shadow-lg, scale 1.03, border color transition 200ms) and click-to-execute behavior
- [x] 6.3 Create `InsightResponse.tsx` container that dispatches to the correct renderer based on response_type

## 7. Frontend: Response renderers

- [x] 7.1 Create `InsightValueRenderer.tsx` — big number display with count-up animation and optional breakdown with staggered fade-in
- [x] 7.2 Create `InsightDistributionRenderer.tsx` — horizontal bars with grow animation (400ms ease-out, 80ms stagger), mana symbols via card-symbol CSS for color distributions, percentage labels
- [x] 7.3 Create `InsightListRenderer.tsx` — ranked list with slide-in animation (60ms stagger), optional card thumbnails, clickable items that open CardDetailModal
- [x] 7.4 Create `InsightComparisonRenderer.tsx` — check/cross icons with scale-in bounce animation for WUBRG presence, mana symbols
- [x] 7.5 Create `InsightTimelineRenderer.tsx` — period bars with staggered grow animation, count and value labels

## 8. Frontend: Integration

- [x] 8.1 Wire CollectionInsights into Dashboard.tsx in place of TopValueCards (between StatsCards and Filters), pass onCardClick for list-type responses that reference card IDs
- [x] 8.2 Delete `TopValueCards.tsx` component file (functionality preserved via `most_valuable` insight)
