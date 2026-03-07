# Design: Fix Avatar Upload and Profile API Migration

## Impact Analysis

### Backend — `backend/api/routes/auth.py`

Two functions require changes:

1. **`_validate_avatar_url(url)`** (lines 388–404): Currently rejects any URL where `urlparse(url).scheme != "https"`. Must be extended to also accept `data:image/*;base64,...` URIs since the frontend legitimately produces them from canvas crop operations.

2. **`update_profile` route handler** (lines 407–439): After successfully calling `repo.update_user_profile()`, must invalidate the stale avatar cache for this user. The cache key is `{user_id}_{sha256(old_avatar_url)[:16]}.img` — but we do not know the old URL at this point. The correct approach is to delete **all** files matching `{user_id}_*.img` and `{user_id}_*.ct` in `_AVATAR_CACHE_DIR`. This is safe because the proxy endpoint will re-populate on next request.

3. **`ProfileUpdateRequest` Pydantic model** (line 370–373): Add `display_name` max-length constraint. Pydantic v2 allows `Field(max_length=100)` or using `constr`. The existing codebase uses Pydantic v2 (FastAPI ≥0.100 with Pydantic v2 semantics). Use `Optional[str] = Field(default=None, max_length=100)`.

### Frontend — `frontend/src/api/client.ts`

Add two items:

1. **`ProfileUpdateBody` interface**: `{ display_name?: string; avatar_url?: string }` — mirrors `ProfileUpdateRequest` on the backend.

2. **`UserProfile` interface** (returned by `PATCH /api/auth/profile`): Backend returns a `UserPayload` shape: `{ id, email, display_name, picture, is_admin }`. Define this as `ProfileResponse` in client.ts.

3. **`api.updateProfile(body: ProfileUpdateBody): Promise<ProfileResponse>`**: Calls `PATCH /api/auth/profile` via `apiFetch`, throws on non-OK with the backend `detail` message.

### Frontend — `frontend/src/components/ProfileModal.tsx`

Replace the raw `fetch` block in `handleSave` (lines 118–128) with `api.updateProfile(body)`. The error handling shape changes slightly: instead of `res.ok` check + `res.json()`, the `api.updateProfile` call throws an `Error` on failure. The existing `catch (err)` block already handles this correctly.

## Detailed Design

### 1. `_validate_avatar_url` — accepting data URIs

**New logic:**

```
if url starts with "data:":
    validate format: must match "data:image/(jpeg|png|gif|webp);base64,<non-empty>"
    if valid → return url
    if invalid → raise 400 "Invalid data URI format"
else:
    existing HTTPS + domain check
```

**Regex pattern**: `^data:image/(jpeg|png|gif|webp);base64,[A-Za-z0-9+/]+=*$`

**Why regex over urlparse for data URIs**: `urlparse` is designed for hierarchical URLs; applying it to data URIs produces misleading parse results (scheme=`data`, path=rest). A targeted regex check is clearer and faster.

**Security**: Data URIs are stored in the DB as-is and decoded server-side by `get_avatar()` (lines 563–588), which already handles them safely. The regex prevents injection of non-image MIME types (e.g., `data:text/html;...`). Size is bounded by the existing 500KB content-length guard on the `update_profile` route (line 411).

**Why this approach over alternatives**:
- Alternative A: Accept data URIs and immediately decode + store to disk in `update_profile`. Rejected — adds complexity, changes the storage contract, and the proxy already does this lazily on first request.
- Alternative B: Add `data:` to the scheme allowlist and skip domain check. Rejected — still allows arbitrary MIME types; regex is more precise.

### 2. Avatar cache invalidation in `update_profile`

After `repo.update_user_profile()` returns successfully, the handler must remove stale cache files. Since the cache key encodes the old `avatar_url` hash (which we don't have here without an extra DB read), we invalidate **all** cached files for this user using a glob pattern:

```python
import glob
for f in _AVATAR_CACHE_DIR.glob(f"{user_id}_*"):
    try:
        f.unlink(missing_ok=True)
    except OSError:
        pass  # non-fatal: stale file served until it's overwritten
```

**Why glob over hash lookup**: To find the old cache key we'd need to read `avatar_url` from the DB before the update, do the SHA-256 hash, then update. That's an extra round-trip. The glob is a single directory scan for files matching the user prefix — O(files in avatar dir) which is small (one `.img` + one `.ct` per user, plus any leftover from URL changes).

**Error handling**: Cache deletion failures are non-fatal and logged at DEBUG. The proxy will serve stale data at worst until the next URL rotation produces a new hash — but since we glob all files for the user, this only happens if deletion fails at OS level.

**Where to place this**: Inline in the `update_profile` route handler, after `updated` is confirmed non-None, before returning the response. No service abstraction needed — this is thin route logic (cleanup of a route-owned cache).

### 3. `ProfileUpdateRequest` — display_name max length

```python
class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = None
```

Pydantic v2 will raise a `ValidationError` on fields exceeding `max_length=100`, which FastAPI automatically translates to HTTP 422 Unprocessable Entity with a descriptive JSON body. No additional code required.

**Why 100 chars**: Matches common display name constraints (Twitter: 50, GitHub: 39, Google: ~100). The `users` table column is `VARCHAR(255)` so 100 is well within schema bounds.

### 4. `api.updateProfile` in `client.ts`

Following existing patterns in `client.ts` (e.g., `updateCardQuantity`, `updateDeck`):

```typescript
export interface ProfileUpdateBody {
  display_name?: string;
  avatar_url?: string;
}

export interface ProfileResponse {
  id: number;
  email: string;
  display_name?: string;
  picture?: string;
  is_admin: boolean;
}

// In the api object:
updateProfile: async (body: ProfileUpdateBody): Promise<ProfileResponse> => {
  const response = await apiFetch(`${API_BASE}/auth/profile`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Failed to update profile');
  }
  return response.json();
},
```

**Why this approach**: Matches the exact pattern used by `updateDeck`, `updateCardQuantity`, and `setScryfallCredentials`. The `apiFetch` wrapper provides 401 auto-refresh + network error normalization that the raw `fetch` in `ProfileModal` currently lacks.

### 5. `ProfileModal.tsx` — `handleSave` migration

Replace lines 118–128:

```typescript
// Before (raw fetch):
const res = await fetch('/api/auth/profile', { method: 'PATCH', ... });
if (!res.ok) { ... }

// After (api client):
await api.updateProfile(body);
```

The existing `catch (err)` block at line 130 already handles thrown errors correctly — `api.updateProfile` throws `Error` instances with the backend detail message, so no change needed there. The `setSaving(false)` in `finally` also remains unchanged.

**Import addition**: `import { api } from '../api/client';` must be added to `ProfileModal.tsx`.

## Data Flow

```
User selects image
    → react-easy-crop produces crop area
    → getCroppedImg() → canvas.toDataURL('image/jpeg', 0.85)
    → pendingCropDataUrl = "data:image/jpeg;base64,..."

User clicks Save
    → ProfileModal.handleSave()
    → api.updateProfile({ avatar_url: "data:image/jpeg;base64,..." })
    → apiFetch PATCH /api/auth/profile
    → Backend: _validate_avatar_url("data:image/jpeg;base64,...")
        → regex match → accepted, returned as-is
    → repo.update_user_profile(user_id, avatar_url="data:...")
    → cache invalidation: unlink {user_id}_*.img, {user_id}_*.ct
    → return UserPayload
    → refreshUser() → GET /api/auth/me
    → AuthContext sets avatar_url = /api/auth/avatar/{user_id}

User sees updated avatar
    → GET /api/auth/avatar/{user_id} (cache miss after invalidation)
    → backend decodes data URI, writes to cache, serves FileResponse
```

## Risks and Edge Cases

**1. Concurrent save + avatar request during invalidation**
If the proxy serves while unlink is in progress, it may read the old cached file (if unlink hasn't completed) or get a cache miss (if unlink completed). Both outcomes are acceptable — the proxy falls back to re-decoding from DB on cache miss.

**2. Data URI size**
A 256×256 JPEG at quality 0.85 typically produces 15–30KB base64-encoded. The existing 500KB content-length guard on `update_profile` is ample. No additional guard needed.

**3. `glob` performance**
`_AVATAR_CACHE_DIR` holds at most O(users × 2) files (one `.img` + one `.ct` per user). For any realistic deployment this is under a few hundred files. No performance concern.

**4. Pydantic 422 vs 400 for max_length**
The existing `test_profile_update_invalid_avatar_url_http_returns_400` test passes a 400 expectation for domain/scheme errors. The new `display_name` max-length violation will return 422 (Pydantic validation). These are different mechanisms — no existing tests are affected.

**5. `missing_ok` on Python 3.7**
`Path.unlink(missing_ok=True)` requires Python 3.8+. Project requires Python 3.8+ (CLAUDE.md: "Python 3.8+"), so this is safe.

**6. Existing tests for `_validate_avatar_url`**
`test_profile_update_invalid_avatar_url_http_returns_400` sends `http://` scheme → still 400 (no change).
`test_profile_update_disallowed_avatar_domain_returns_400` sends `https://evil.com` → still 400 (no change).
New tests needed: data URI accepted, malformed data URI rejected.
