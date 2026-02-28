## 1. Backend: Fix Content-Type in card_image_service.py

- [x] 1.1 In `backend/api/services/card_image_service.py` line 111, replace `content_type = "image/jpeg"` with `content_type = resp.headers.get('content-type', 'image/jpeg')` so the real MIME type from Scryfall is stored in the cache and returned to the client.

---

## 2. Frontend client: Add authenticated image fetch helper

- [x] 2.1 In `frontend/src/api/client.ts`, add a `fetchCardImage(id: number): Promise<string>` async function to the `api` object.
  - Uses `apiFetch(`${API_BASE}/cards/${id}/image`)` (inherits Authorization header)
  - Throws if `!response.ok` (include status code in error message)
  - Returns `URL.createObjectURL(await response.blob())` — a Blob URL string

---

## 3. Frontend hook: Create useCardImage

- [x] 3.1 Create `frontend/src/hooks/useCardImage.ts`.
  - Accepts `cardId: number | null`
  - Returns `{ src: string | null; loading: boolean; error: boolean }`
  - When `cardId` is null: returns `{ src: null, loading: false, error: false }`
  - On mount / when `cardId` changes: call `api.fetchCardImage(cardId)`, store the Blob URL in state
  - `useEffect` cleanup: call `URL.revokeObjectURL(src)` to release memory
  - Sets `loading: true` while fetching, `error: true` on failure
  - Do NOT use TanStack Query here — image data is binary and Blob URLs are tab-local; a plain `useState`+`useEffect` is correct and simpler

---

## 4. Update InsightListRenderer.tsx

- [x] 4.1 In `frontend/src/components/insights/InsightListRenderer.tsx`, refactor `CardThumbnail`:
  - Remove local `useState(false)` for error (hook handles it)
  - Call `const { src, error } = useCardImage(cardId)`
  - If `error` is true, return null (same as before)
  - Pass `src` to `<img src={src ?? undefined}>` (undefined hides broken placeholder)
  - Import `useCardImage` from `../../hooks/useCardImage`

---

## 5. Update CardDetailModal.tsx

- [x] 5.1 In `frontend/src/components/CardDetailModal.tsx`:
  - Remove line `const imageUrl = cardId != null ? api.getCardImageUrl(cardId) : null;`
  - Add `const { src: imageUrl, loading: imageLoading } = useCardImage(cardId)`
  - Replace `[imageLoaded, setImageLoaded]` and `[imageError, setImageError]` state with the hook's values where possible, or keep them only for the lightbox open/close interaction (the `onLoad`/`onError` handlers can be simplified since the hook handles errors)
  - Import `useCardImage` from `../hooks/useCardImage`
  - Pass `imageUrl ?? undefined` to `<img src>` (avoids null type error)

---

## 6. Update DeckDetailModal.tsx

- [x] 6.1 In `frontend/src/components/DeckDetailModal.tsx`:
  - Remove line `const bigImageUrl = bigImageCardId != null ? api.getCardImageUrl(bigImageCardId) : null;`
  - Add `const { src: bigImageUrl } = useCardImage(bigImageCardId)`
  - Pass `bigImageUrl ?? undefined` wherever `bigImageUrl` is used as `<img src>` or similar
  - Import `useCardImage` from `../hooks/useCardImage`

---

## 7. Update DeckBuilder.tsx

- [x] 7.1 In `frontend/src/pages/DeckBuilder.tsx`, the deck list renders commander images as CSS `backgroundImage`.
  - Each deck card is rendered inside a `.map()` — `commanderImageUrl` is computed inline per deck using `api.getCardImageUrl(deck.commander_card_id)`
  - Extract a small `DeckCard` component (or use a hook at the map level) so that `useCardImage` can be called per deck item (hooks cannot be called inside callbacks)
  - The new component receives `commanderCardId: number | null` and renders the button with the background image, calling `useCardImage(commanderCardId)` internally
  - Use `src ?? ''` in `style={{ backgroundImage: src ? \`url(\${src})\` : 'none' }}`
  - Pass all other needed props (deck, onClick, etc.) to the extracted component

---

## 8. Cleanup

- [x] 8.1 Remove the now-unused `getCardImageUrl` function from `frontend/src/api/client.ts` (or keep it if it is referenced elsewhere — check with grep first)
- [x] 8.2 Verify no component still imports or calls `api.getCardImageUrl`

---

## 9. Validation

- [ ] 9.1 Start backend and frontend locally; open the library/dashboard and confirm card thumbnails load in `CollectionInsights`
- [ ] 9.2 Open a card detail modal and confirm the card image loads
- [ ] 9.3 Open the deck builder and confirm commander images appear on deck cards
- [ ] 9.4 Open a deck detail modal and confirm the preview image loads
- [ ] 9.5 Open browser DevTools Network tab — confirm image requests return 200 with correct Content-Type (not 401)
- [ ] 9.6 Open browser DevTools Memory tab — create and destroy several card modals; confirm Blob URL count does not grow unboundedly
- [ ] 9.7 Remove the auth token from sessionStorage manually and confirm image requests return 401 (endpoint is still protected)
