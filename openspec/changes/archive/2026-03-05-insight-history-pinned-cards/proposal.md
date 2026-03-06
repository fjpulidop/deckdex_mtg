## Why

The Collection Insights panel currently shows only one result at a time — running a new insight replaces the previous result. This means users lose context as they explore questions. Power users want to compare insights side by side and keep their favourite insights visible across page loads without re-running them every time.

## What Changes

- **Insight history (array of results)**: Replace the single `activeResult` state with an array `results: InsightResult[]`. New results are prepended so the most recent appears first. Each card shows the question, rendered answer, a dismiss (X) button, and a pin toggle.
- **Pin/unpin toggle**: Pinned insights show a filled pin icon; unpinned show an outline. Pinned cards are visually distinct (e.g. a subtle top-border accent). Clicking pin toggles pinned state.
- **localStorage persistence**: Pinned insight IDs are saved to `deckdex:pinned_insights` (an array of `insight_id` strings). On page load, pinned insights auto-execute in background and their results are pre-populated in the results array.
- **Dismiss button**: Each result card has an X button that removes it from the array. Pinning a card and then dismissing it still removes it from view but retains the pin (so it re-appears on next load).
- **i18n**: New keys `pin`, `unpin`, `dismiss` added to both `en.json` and `es.json` inside the `insights` namespace.

## Non-goals

- No backend changes — pinning is pure frontend state.
- No drag-and-drop reordering.
- No limit on number of simultaneous result cards (natural limit from usage patterns).
- No server-side persistence of pins.

## Capabilities

### Modified Capabilities

- `collection-insights`: Extended to support multi-result history with pin/unpin and localStorage persistence.

## Impact

- **`frontend/src/components/CollectionInsights.tsx`**: Rewire state from single result to array; add pin logic, localStorage effects, auto-execute on mount for pinned IDs.
- **`frontend/src/components/insights/InsightResponse.tsx`**: Added optional `hideQuestion` prop.
- **`frontend/src/locales/en.json`** and **`es.json`**: Add `insights.pin`, `insights.unpin`, `insights.dismiss` keys.
- **No backend changes**.
- **No API changes**.
