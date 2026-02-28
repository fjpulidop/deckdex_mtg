## Why

Card images don't load in the library and any other view that displays them. The root cause is a mismatch between how authentication works and how the browser loads images natively.

The frontend token lives in `sessionStorage` and is injected only through the `apiFetch` wrapper. But every component that shows a card image uses `<img src={api.getCardImageUrl(cardId)}>`, which is a native browser image fetch — it never sends the `Authorization: Bearer` header. The backend endpoint `GET /api/cards/{id}/image` requires authentication via `Depends(get_current_user_id)`, so every image request silently returns 401, and `onError` hides the broken image.

A secondary bug: `card_image_service.py` always stores and returns `content_type = "image/jpeg"`, regardless of what Scryfall actually sends (PNG for high-res, JPEG for normal). This causes rendering problems for PNG images.

The fix must be production-ready: authentication stays required on the image endpoint, no token in query params or URLs, and images are always served from the PostgreSQL cache after the first fetch.

## What Changes

- **Frontend**: Replace `<img src={url}>` with a hook (`useCardImage`) that fetches images via `apiFetch` (with Authorization header), converts the response to a Blob URL, and passes it to `<img src>`. Blob URLs are revoked on unmount to avoid memory leaks.
- **Backend**: Read the real `Content-Type` from the Scryfall response headers instead of hardcoding `"image/jpeg"`. Store it correctly in `card_image_cache`.
- **DB**: No schema change needed — `content_type` column already exists in `card_image_cache`.

## Capabilities

### Modified Capabilities
- `card-image-storage`: Frontend image loading now goes through authenticated fetch; backend returns correct Content-Type
- `global-image-cache`: Cached content_type is now accurate (PNG vs JPEG)

## Impact

**Affected code:**
- `frontend/src/api/client.ts` — add `fetchCardImage()` that returns a Blob URL
- `frontend/src/hooks/useCardImage.ts` — new hook wrapping `fetchCardImage` with loading/error state and Blob URL lifecycle
- `frontend/src/components/insights/InsightListRenderer.tsx` — use `useCardImage` hook instead of bare `img src`
- `frontend/src/components/CardDetailModal.tsx` — use `useCardImage` hook
- `frontend/src/components/DeckDetailModal.tsx` — use `useCardImage` hook
- `frontend/src/pages/DeckBuilder.tsx` — use `useCardImage` hook
- `backend/api/services/card_image_service.py` — fix `content_type` to read from Scryfall response headers

**New files:**
- `frontend/src/hooks/useCardImage.ts`

**Non-breaking:**
- The backend endpoint contract is unchanged (same URL, same auth, same 404 behavior)
- No DB migrations required
