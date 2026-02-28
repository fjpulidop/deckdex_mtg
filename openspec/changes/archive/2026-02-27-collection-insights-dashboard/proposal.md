## Why

The Top 5 Most Valuable Cards section on the dashboard is static — once a user recognizes their expensive cards, it provides no recurring value. The dashboard title ("DeckDex MTG / Manage your Magic: The Gathering collection") is redundant with the navbar branding. The color filter buttons show plain letters instead of the Scryfall mana symbol icons already used elsewhere in the app. Together, these reduce the dashboard's visual polish and utility.

## What Changes

- **Remove dashboard title block**: Eliminate the "DeckDex MTG / Manage your Magic: The Gathering collection" heading from the Dashboard page; the navbar already provides branding.
- **Mana icons in color filters**: Replace the plain letter buttons (W, U, B, R, G) in the Filters component with Scryfall mana symbol SVGs using the existing `card-symbol` CSS infrastructure.
- **Replace Top 5 with Collection Insights**: Remove the TopValueCards component and introduce an interactive "Collection Insights" widget that lets users ask predefined questions about their collection (e.g., "How much is my collection worth?", "Do I have duplicates?"). Questions are resolved server-side via pure computation (no LLM). The widget includes a search/autocomplete input, contextual suggestion chips that rotate based on collection state, and rich animated response visualizations (value displays, distribution bars with mana symbols, card lists, comparisons, timelines).
- **Insights backend**: New API endpoints and service layer for executing insight queries against the user's collection data, plus a suggestion engine that picks the most relevant questions based on collection signals.
- **i18n-ready data model**: Question labels and answer templates use key-based references so the system can be localized later without restructuring.

## Capabilities

### New Capabilities
- `collection-insights`: Server-side insight engine with 17 predefined questions across 5 categories (summary, distribution, ranking, patterns, activity), contextual suggestion logic, and rich response types (value, distribution, list, comparison, timeline).

### Modified Capabilities
- `web-dashboard-ui`: Dashboard layout changes — remove title block, replace TopValueCards with CollectionInsights widget, integrate branding into navbar.
- `web-api-backend`: New insight routes (GET /api/insights/catalog, GET /api/insights/suggestions, POST /api/insights/{insight_id}).
- `navigation-ui`: Navbar absorbs the app subtitle/tagline previously shown on the dashboard.

## Impact

- **Frontend**: Dashboard.tsx (layout restructure), Navbar.tsx (subtitle integration), Filters.tsx (mana icons), new CollectionInsights component tree (~5 sub-components for response renderers), remove TopValueCards.tsx.
- **Backend**: New insights service module, new API routes, new suggestion engine. All queries use existing repository layer — no schema changes needed.
- **Dependencies**: No new external dependencies. Uses existing Scryfall mana symbol CSS, existing card-symbol infrastructure, existing TanStack Query patterns.
- **API surface**: 3 new endpoints added. No breaking changes to existing endpoints.
