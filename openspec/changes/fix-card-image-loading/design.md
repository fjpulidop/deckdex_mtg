## Context

The system serves card images through an authenticated REST endpoint (`GET /api/cards/{id}/image`). The spec (`card-image-storage`) explicitly requires:
- Authentication check: 401 if no valid token
- PostgreSQL `card_image_cache` table as the authoritative store
- Correct `Content-Type` in the response

Current state breaks both the frontend (images never load) and the backend (wrong Content-Type).

**Frontend failure path:**
```
<img src="/api/cards/42/image">
    ↓ Browser native fetch — no Authorization header
    ↓ Backend: get_current_user_id → 401 Unauthorized
    ↓ onError={() => setError(true)}  → silent failure
```

**Backend failure:**
```python
content_type = "image/jpeg"  # hardcoded, ignores Scryfall response headers
repo.save_card_image_to_global_cache(scryfall_id, content_type, data)
# Stores wrong content_type — PNG cards served with image/jpeg header
```

## Goals / Non-Goals

**Goals:**
- All card images load correctly in: library insights, card detail modal, deck detail modal, deck builder
- Authentication remains required on the image endpoint (production-safe)
- No token ever appears in a URL query parameter or path
- Images are served from DB cache after the first fetch (no repeated Scryfall calls)
- Correct `Content-Type` returned for all images (PNG and JPEG)
- Blob URLs are cleaned up on component unmount (no memory leaks)

**Non-Goals:**
- Prefetching or preloading images proactively
- Service worker caching of images in the browser
- Image resizing or format conversion
- Changing the backend endpoint URL or auth mechanism

## Decisions

### Decision 1: fetch + Blob URL instead of alternatives

**Choice:** Use `apiFetch` to load images, convert response to `Blob`, create `URL.createObjectURL(blob)`, pass to `<img src>`.

**Alternatives considered:**

| Option | Problem |
|--------|---------|
| Token in query param (`?token=xxx`) | Token exposed in server logs, browser history, referrer headers — insecure for production |
| Remove auth from image endpoint | Violates spec requirement; any unauthenticated request could drain Scryfall quota and serve card data |
| HTTP-only cookie for token | Would require overhauling the entire auth system; disproportionate scope |
| Store token in localStorage, read via JS on img load | `<img>` still can't send headers; same problem |

**Rationale:**
`fetch + Blob URL` is the standard browser pattern for loading authenticated binary resources. It reuses the existing `apiFetch` wrapper (no auth changes), keeps the token in `sessionStorage` (unchanged), and is invisible to components — they just receive a plain `src` string as before.

### Decision 2: Centralize in a `useCardImage` hook

**Choice:** Create `frontend/src/hooks/useCardImage.ts` — accepts `cardId: number | null`, returns `{ src: string | null, loading: boolean, error: boolean }`.

**Rationale:**
- Single place to manage fetch, Blob URL creation, and cleanup (`URL.revokeObjectURL` on unmount)
- Components stay simple: call hook, render `<img src={src}>`
- Makes future changes (prefetch, retry, placeholder) trivial
- Pattern is consistent with the existing `useApi` hook convention in the codebase

**Hook contract:**
```typescript
function useCardImage(cardId: number | null): {
  src: string | null;   // Blob URL or null
  loading: boolean;
  error: boolean;
}
```

### Decision 3: `fetchCardImage` helper on `api` object

**Choice:** Add `fetchCardImage(id: number): Promise<string>` to `client.ts`. Returns a Blob URL string (not a Response). The hook calls this; components never touch fetch directly.

**Rationale:**
- Keeps all backend communication in `client.ts` (existing convention)
- Easy to test in isolation
- Blob URL creation is the responsibility of the client, not the hook — cleaner separation

### Decision 4: Content-Type from Scryfall response headers

**Choice:** Replace `content_type = "image/jpeg"` with `content_type = resp.headers.get('content-type', 'image/jpeg')` in `card_image_service.py`.

**Rationale:**
- Scryfall returns `image/jpeg` for normal-size images and `image/png` for `png` format
- The wrong content-type can cause browsers to misinterpret image data
- The `card_image_cache` table already has a `content_type TEXT` column — storing the correct value costs nothing

### Decision 5: Blob URL revocation on unmount

**Choice:** `useEffect` cleanup calls `URL.revokeObjectURL(src)` when the component unmounts or `cardId` changes.

**Rationale:**
- Each Blob URL holds a reference to an in-memory copy of the image
- Without revocation, navigating across many cards would accumulate unbounded memory
- This is the standard browser API contract for Blob URLs

## Risks / Trade-offs

### Risk 1: Extra network round-trip per image
**Risk:** Unlike `<img src>`, which the browser can handle in parallel with page load, `fetch` is sequential from JS perspective.
**Mitigation:** React Query (TanStack Query) is already in the stack — the hook uses it for caching (same `cardId` → same cached Blob URL across remounts). After first load, no extra fetch occurs within the session.

### Risk 2: Blob URL lifetime management
**Risk:** If a Blob URL is revoked while the `<img>` still references it, the image disappears.
**Mitigation:** Revocation happens only in the `useEffect` cleanup — i.e., only when the component unmounts or `cardId` changes. The `<img>` is always unmounted before its Blob URL is revoked.

### Risk 3: Blob URL not shareable / bookmarkable
**Risk:** Blob URLs are tab-local and can't be shared or cached by the browser's disk cache.
**Mitigation:** This is fine — images are already served from the PostgreSQL cache on the backend. The browser disk cache would only help for network-heavy scenarios, which don't apply here since the backend is local or on a controlled server.

### Trade-off 1: Slightly more complex component code
Each component now calls a hook instead of computing a URL string directly. The trade-off is accepted: the alternative (broken images) is worse, and the hook pattern is already used throughout the codebase.

## Migration Plan

### Phase 1: Backend fix (no frontend impact)
1. Fix `content_type` in `card_image_service.py` to read from Scryfall headers
2. Existing broken `<img>` tags continue to fail (unchanged), but cache now stores correct type

### Phase 2: Frontend hook + client method
1. Add `fetchCardImage()` to `api/client.ts`
2. Create `useCardImage` hook
3. Update all four callsites: `InsightListRenderer`, `CardDetailModal`, `DeckDetailModal`, `DeckBuilder`

### Phase 3: Validate
1. Run frontend locally, verify images load in all views
2. Verify Blob URLs are cleaned up (DevTools Memory tab)
3. Verify 401 is returned for unauthenticated requests

## Open Questions

_None — all decisions are resolved above._
