# Design: Insight History and Pinned Dashboard Cards

## Architecture

This is a pure frontend change. No new API endpoints or backend modifications are required. All state management lives inside `CollectionInsights.tsx` and uses React state + localStorage.

## State Shape

```typescript
// Defined inside CollectionInsights.tsx
interface InsightResultEntry {
  id: string;                    // unique per render: `${insight_id}_${Date.now()}`
  response: InsightResponseType; // the full API response from api/client.ts
  pinned: boolean;
  executedAt: number;            // Date.now() timestamp
}
```

The component manages:
- `results: InsightResultEntry[]` — full ordered list, most recent first (for manual runs), oldest first (for auto-executed pinned on mount)
- `pinnedIds: string[]` — insight IDs persisted to localStorage

## localStorage

Key: `deckdex:pinned_insights`
Value: JSON array of `insight_id` strings, e.g. `["total_value","by_rarity"]`

On mount: read `pinnedIds`, execute each via the existing `execute.mutateAsync` call, append results with `pinned: true`.

On pin toggle: update `pinnedIds` in state and write to localStorage.

On dismiss: remove from `results` array. Intentionally does NOT remove from `pinnedIds` — the pin is a preference, not a display state.

## Component Structure

```
CollectionInsights
  ├── SearchInput + Dropdown (unchanged)
  ├── Suggestion chips (unchanged)
  └── results.map(entry => InsightResultCard)
        ├── Pin toggle button (SVG icons, aria-label from i18n)
        ├── Dismiss (X) button
        └── InsightResponse (existing renderer, hideQuestion=true)
```

`InsightResultCard` is defined as a module-level function in `CollectionInsights.tsx` — not extracted to a separate file since it depends on the `InsightResultEntry` type and has no independent reuse.

## Pin visual design

- Pinned card: `border-l-4 border-indigo-400` left accent
- Unpinned card: `border-gray-100 dark:border-gray-600` standard border
- Pin button: filled SVG icon when pinned (indigo), outline SVG when not (gray → indigo on hover)

## InsightResponse.tsx `hideQuestion` prop

Added optional `hideQuestion?: boolean` (default `false`). When `true`, the function returns the renderers directly in a React fragment without the outer `<div>` wrapper or `<h3>` question heading. This allows `InsightResultCard` to own the card chrome and question rendering.

## Error handling

Pinned auto-execution on mount silently skips failures (empty `catch` block). Manual execution surfaces errors via the existing `execute.isError` state.
