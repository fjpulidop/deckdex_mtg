## 1. State refactor in CollectionInsights.tsx

- [x] 1.1 Define `InsightResultEntry` interface (id, response, pinned, executedAt) inside `CollectionInsights.tsx`
- [x] 1.2 Replace `activeResult: InsightResponseType | null` state with `results: InsightResultEntry[]`
- [x] 1.3 Add `pinnedIds: string[]` state initialised from `localStorage.getItem('deckdex:pinned_insights')` (parse JSON, fall back to `[]`)
- [x] 1.4 Add `useEffect` on mount that sequentially executes each pinned insight ID and prepends results with `pinned: true`

## 2. Insight result card UI

- [x] 2.1 Implement `InsightResultCard` inline functional component with: pin toggle button (aria-label from i18n), dismiss button (X), and `InsightResponse` renderer
- [x] 2.2 Apply pinned visual style: `border-l-4 border-indigo-400` for pinned cards, neutral border for unpinned
- [x] 2.3 Replace single `{activeResult && <InsightResponse .../>}` render with `results.map(entry => <InsightResultCard .../>)` list

## 3. Pin/unpin logic

- [x] 3.1 Implement `handleTogglePin(entryId, currentResults)` that flips `pinned` on the matching entry and syncs `pinnedIds` + localStorage
- [x] 3.2 Implement `handleDismiss(entryId)` that removes the entry from `results`

## 4. runInsight update

- [x] 4.1 Update `runInsight` to prepend the new result to `results` with `pinned` set based on whether the insight_id is already in `pinnedIds`

## 5. i18n

- [x] 5.1 Add `insights.pin`, `insights.unpin`, `insights.dismiss` to `frontend/src/locales/en.json`
- [x] 5.2 Add `insights.pin`, `insights.unpin`, `insights.dismiss` to `frontend/src/locales/es.json`

## 6. InsightResponse.tsx update

- [x] 6.1 Add optional `hideQuestion` prop to `InsightResponse` — when true, render only the typed renderers without the outer wrapper div and question heading

## 7. TypeScript verification

- [x] 7.1 TypeScript types verified — no `any` types, all interfaces explicit, `hideQuestion` defaults to `false`
