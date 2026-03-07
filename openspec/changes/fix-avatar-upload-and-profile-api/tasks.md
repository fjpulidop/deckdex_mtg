# Tasks: Fix Avatar Upload and Profile API Migration

## Group 1 — Backend: `backend/api/routes/auth.py`

### Task 1 — Extend `_validate_avatar_url` to accept data URIs

**File**: `backend/api/routes/auth.py`

**Context**: `_validate_avatar_url()` is at lines 388–404. It currently raises HTTP 400 for any URL where `urlparse(url).scheme != "https"`. Data URIs (`data:image/jpeg;base64,...`) produced by the frontend crop workflow are rejected here, making avatar upload completely non-functional.

**What to do**:

At the top of `_validate_avatar_url`, before the existing HTTPS/domain check, add a data URI branch:

```python
import re

_DATA_URI_RE = re.compile(
    r'^data:image/(jpeg|png|gif|webp);base64,[A-Za-z0-9+/]+=*$'
)

def _validate_avatar_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if url.startswith("data:"):
        if not _DATA_URI_RE.match(url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data URI format for avatar",
            )
        return url
    # existing HTTPS + domain check below (unchanged)
    parsed = urlparse(url)
    ...
```

Place `_DATA_URI_RE` as a module-level constant near `_SAFE_AVATAR_DOMAINS` (around line 376). Do not use `re.compile` inside the function — it runs per-call.

**Acceptance criteria**:
- `_validate_avatar_url("data:image/jpeg;base64,/9j/4AA...")` returns the URL unchanged (no exception).
- `_validate_avatar_url("data:text/html;base64,abc")` raises HTTP 400.
- `_validate_avatar_url("data:image/jpeg;base64,")` (empty data) raises HTTP 400.
- `_validate_avatar_url("data:image/png;base64,abc==")` returns the URL unchanged.
- Existing behaviour for `http://`, `https://evil.com`, and allowed HTTPS domains is unchanged.

**Dependencies**: None.

---

### Task 2 — Add display_name max-length validation to `ProfileUpdateRequest`

**File**: `backend/api/routes/auth.py`

**Context**: `ProfileUpdateRequest` is at line 370. Currently `display_name` is `Optional[str] = None` with no length constraint.

**What to do**:

Add `Field` import from pydantic (check if already imported; if not, add it) and update the model:

```python
from pydantic import BaseModel, Field

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = None
```

FastAPI + Pydantic v2 automatically returns HTTP 422 with a descriptive error body when `max_length` is violated.

**Acceptance criteria**:
- `PATCH /api/auth/profile` with `display_name` of 101 characters returns HTTP 422.
- `PATCH /api/auth/profile` with `display_name` of exactly 100 characters returns HTTP 200 (given valid token and mock repo).
- All existing `TestProfileUpdate` tests continue to pass.

**Dependencies**: None.

---

### Task 3 — Invalidate avatar disk cache on profile update

**File**: `backend/api/routes/auth.py`

**Context**: The `update_profile` route handler is at lines 407–439. After `repo.update_user_profile()` succeeds, the cached avatar files at `_AVATAR_CACHE_DIR/{user_id}_{hash}.img` and `_AVATAR_CACHE_DIR/{user_id}_{hash}.ct` become stale. The proxy endpoint (`get_avatar`) will serve the old image until the cache is cleared.

**What to do**:

After confirming `updated is not None`, add cache invalidation before the return statement:

```python
updated = repo.update_user_profile(...)
if updated is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

# Invalidate stale cached avatar files for this user
if body.avatar_url is not None:
    for cached_file in _AVATAR_CACHE_DIR.glob(f"{user_id}_*"):
        try:
            cached_file.unlink(missing_ok=True)
        except OSError as exc:
            logger.debug(f"Avatar cache cleanup failed for user {user_id}: {exc}")

return UserPayload(...)
```

Only invalidate when `body.avatar_url is not None` — if only `display_name` changed, the avatar cache is still valid.

**Acceptance criteria**:
- After `PATCH /api/auth/profile` with a new `avatar_url`, all `{user_id}_*.img` and `{user_id}_*.ct` files in `_AVATAR_CACHE_DIR` are deleted.
- If no `avatar_url` is in the request body (only `display_name`), no files are touched.
- An `OSError` during file deletion does not cause the endpoint to return an error; HTTP 200 is still returned.
- The endpoint still returns HTTP 200 even if `_AVATAR_CACHE_DIR` is empty.

**Dependencies**: Tasks 1 and 2 should be done first (same file, reduces merge conflicts), but this task is logically independent.

---

## Group 2 — Frontend: `frontend/src/api/client.ts`

### Task 4 — Add `ProfileUpdateBody`, `ProfileResponse`, and `api.updateProfile`

**File**: `frontend/src/api/client.ts`

**Context**: `client.ts` currently has no profile-related types or methods. `ProfileModal.tsx` uses a raw `fetch` call which bypasses the 401 auto-refresh and network error handling in `apiFetch`. All backend calls must go through `api/client.ts` per project conventions.

**What to do**:

1. Add interfaces after the existing `JobHistoryItem` or `Stats` interfaces (keep types grouped):

```typescript
export interface ProfileUpdateBody {
  display_name?: string;
  avatar_url?: string;
}

export interface ProfileResponse {
  id: number;
  email: string;
  display_name?: string | null;
  picture?: string | null;
  is_admin: boolean;
}
```

2. Add `updateProfile` to the `api` object (place it near other auth-adjacent methods — e.g., after `getJobHistory` or at the end of the object before the closing `}`):

```typescript
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

**Acceptance criteria**:
- `api.updateProfile` is exported and callable from `ProfileModal.tsx` via `import { api } from '../api/client'`.
- TypeScript compiles without errors (`npm run build` in `frontend/` passes).
- `ProfileUpdateBody` and `ProfileResponse` are exported so they can be imported by consumers if needed.
- The method uses `apiFetch` (not raw `fetch`), ensuring 401 auto-refresh applies.

**Dependencies**: None (backend tasks are parallel to frontend).

---

## Group 3 — Frontend: `frontend/src/components/ProfileModal.tsx`

### Task 5 — Migrate `handleSave` to `api.updateProfile`

**File**: `frontend/src/components/ProfileModal.tsx`

**Context**: `handleSave` (lines 102–135) calls `fetch('/api/auth/profile', ...)` directly, violating the project convention. The raw `fetch` lacks 401 auto-refresh and network error handling. Additionally, since the backend now accepts data URIs (Task 1), the previously-broken avatar save path will now succeed.

**What to do**:

1. Add the import at the top of the file:
   ```typescript
   import { api } from '../api/client';
   ```

2. Replace the raw `fetch` block (lines 118–128) in `handleSave`:

**Before:**
```typescript
const res = await fetch('/api/auth/profile', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify(body),
});
if (!res.ok) {
  const data = await res.json().catch(() => ({}));
  throw new Error(data.detail || `Error ${res.status}`);
}
```

**After:**
```typescript
await api.updateProfile(body);
```

3. Add frontend display name max-length validation in `handleSave`, alongside the existing empty-name check:

```typescript
if (!displayName.trim()) {
  setNameError(t('profile.nameRequired'));
  return;
}
if (displayName.trim().length > 100) {
  setNameError(t('profile.nameTooLong'));
  return;
}
```

4. Add the missing i18n key to `frontend/src/locales/en.json` and `frontend/src/locales/es.json`:
   - `"profile.nameTooLong"` → `"Name must be 100 characters or less"` (en) / `"El nombre debe tener 100 caracteres o menos"` (es)

The existing `catch (err)` block and `finally { setSaving(false) }` remain unchanged — `api.updateProfile` throws `Error` instances, which the catch block already handles.

**Acceptance criteria**:
- `ProfileModal.tsx` contains no `fetch(` calls.
- Selecting an image, cropping it, and clicking Save results in an HTTP 200 response (end-to-end, with backend Task 1 complete).
- Entering a display name longer than 100 characters shows a validation error without calling the API.
- The error message for a failed save shows the server's `detail` string (e.g., "Invalid data URI format for avatar").
- `npm run lint` passes on `ProfileModal.tsx`.
- TypeScript compiles without errors.

**Dependencies**: Task 4 must be complete before this task (imports `api.updateProfile`).

---

## Group 4 — Tests

### Task 6 — Add backend tests for data URI validation and cache invalidation

**File**: `tests/test_auth_e2e.py`

**Context**: `TestProfileUpdate` class (line 767) currently tests HTTPS validation but has no tests for data URI acceptance or cache invalidation. New behavior introduced in Tasks 1–3 must be covered.

**What to do**:

Add the following test methods to the existing `TestProfileUpdate` class:

**Test: data URI accepted**
```python
def test_profile_update_data_uri_avatar_succeeds(self):
    token = _make_token(user_id=10, email="user10@example.com")
    data_uri = "data:image/jpeg;base64,/9j/4AAQSkZJRgAB"  # valid-prefix stub
    updated = {
        "id": 10,
        "email": "user10@example.com",
        "display_name": None,
        "avatar_url": data_uri,
        "is_admin": False,
    }
    mock_repo = self._make_profile_mock_repo(updated)
    self.client.cookies.set("access_token", token)
    with patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo):
        resp = self.client.patch("/api/auth/profile", json={"avatar_url": data_uri})
    self.assertEqual(resp.status_code, 200)
```

Note: The regex `_DATA_URI_RE` requires the base64 data to match `[A-Za-z0-9+/]+=*`. Use a valid base64 stub like `"/9j/4AAQSkZJRgAB"` (JPEG magic bytes base64-encoded without padding, which is a valid match).

**Test: malformed data URI rejected (wrong MIME)**
```python
def test_profile_update_data_uri_wrong_mime_rejected(self):
    token = _make_token(user_id=10, email="user10@example.com")
    self.client.cookies.set("access_token", token)
    resp = self.client.patch(
        "/api/auth/profile",
        json={"avatar_url": "data:text/html;base64,PHNjcmlwdD4="},
    )
    self.assertEqual(resp.status_code, 400)
```

**Test: malformed data URI rejected (empty data)**
```python
def test_profile_update_data_uri_empty_data_rejected(self):
    token = _make_token(user_id=10, email="user10@example.com")
    self.client.cookies.set("access_token", token)
    resp = self.client.patch(
        "/api/auth/profile",
        json={"avatar_url": "data:image/jpeg;base64,"},
    )
    self.assertEqual(resp.status_code, 400)
```

**Test: display name max length — over limit**
```python
def test_profile_update_display_name_too_long_returns_422(self):
    token = _make_token(user_id=10, email="user10@example.com")
    self.client.cookies.set("access_token", token)
    resp = self.client.patch(
        "/api/auth/profile",
        json={"display_name": "A" * 101},
    )
    self.assertEqual(resp.status_code, 422)
```

**Test: display name at max length — accepted**
```python
def test_profile_update_display_name_at_max_length_succeeds(self):
    token = _make_token(user_id=10, email="user10@example.com")
    name_100 = "A" * 100
    updated = {
        "id": 10,
        "email": "user10@example.com",
        "display_name": name_100,
        "avatar_url": None,
        "is_admin": False,
    }
    mock_repo = self._make_profile_mock_repo(updated)
    self.client.cookies.set("access_token", token)
    with patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo):
        resp = self.client.patch("/api/auth/profile", json={"display_name": name_100})
    self.assertEqual(resp.status_code, 200)
```

**Test: cache invalidation called when avatar_url changes**
```python
def test_profile_update_avatar_invalidates_cache(self):
    import tempfile
    from pathlib import Path
    token = _make_token(user_id=42, email="user42@example.com")
    data_uri = "data:image/jpeg;base64,/9j/4AAQSkZJRgAB"
    updated = {
        "id": 42,
        "email": "user42@example.com",
        "display_name": None,
        "avatar_url": data_uri,
        "is_admin": False,
    }
    mock_repo = self._make_profile_mock_repo(updated)

    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        # Create fake cached files for user 42
        (cache_dir / "42_abc123.img").write_bytes(b"fake")
        (cache_dir / "42_abc123.ct").write_text("image/jpeg")
        (cache_dir / "99_other.img").write_bytes(b"other")  # should NOT be deleted

        self.client.cookies.set("access_token", token)
        with patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo), \
             patch("backend.api.routes.auth._AVATAR_CACHE_DIR", cache_dir):
            resp = self.client.patch("/api/auth/profile", json={"avatar_url": data_uri})

    self.assertEqual(resp.status_code, 200)
    self.assertFalse((cache_dir / "42_abc123.img").exists())
    self.assertFalse((cache_dir / "42_abc123.ct").exists())
    self.assertTrue((cache_dir / "99_other.img").exists())  # unrelated user untouched
```

**Test: no avatar_url in body does not touch cache**
```python
def test_profile_update_display_name_only_does_not_invalidate_cache(self):
    import tempfile
    from pathlib import Path
    token = _make_token(user_id=43, email="user43@example.com")
    updated = {
        "id": 43,
        "email": "user43@example.com",
        "display_name": "New Name",
        "avatar_url": None,
        "is_admin": False,
    }
    mock_repo = self._make_profile_mock_repo(updated)

    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        (cache_dir / "43_xyz.img").write_bytes(b"cached")

        self.client.cookies.set("access_token", token)
        with patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo), \
             patch("backend.api.routes.auth._AVATAR_CACHE_DIR", cache_dir):
            resp = self.client.patch("/api/auth/profile", json={"display_name": "New Name"})

    self.assertEqual(resp.status_code, 200)
    self.assertTrue((cache_dir / "43_xyz.img").exists())  # cache not touched
```

**Acceptance criteria**:
- All new test methods pass: `pytest tests/test_auth_e2e.py::TestProfileUpdate -v`
- All previously existing `TestProfileUpdate` tests still pass.
- Total test suite (`pytest tests/`) passes without regression.

**Dependencies**: Tasks 1, 2, 3 must be complete before these tests can pass.

---

## Execution Order

```
Task 1 (validate data URI)
Task 2 (max_length)        } — can be done in parallel (same file, same PR)
Task 3 (cache invalidation)

Task 4 (api.updateProfile) — can be done in parallel with Tasks 1-3

Task 5 (ProfileModal)      — depends on Task 4

Task 6 (tests)             — depends on Tasks 1, 2, 3 being in place
```
