## 1. Backend — Repository

- [x] 1.1 Add `update_user_profile(user_id, display_name, avatar_url)` method to `CollectionRepository` abstract base and `PostgresCollectionRepository` implementation in `deckdex/storage/repository.py`

## 2. Backend — Auth Routes

- [x] 2.1 Update `GET /api/auth/me` in `backend/api/routes/auth.py` to fetch user from DB by `sub` claim instead of returning JWT payload fields
- [x] 2.2 Add `PATCH /api/auth/profile` endpoint in `backend/api/routes/auth.py` accepting `{ display_name?, avatar_url? }`, calling `repo.update_user_profile()`, returning updated `UserPayload`
- [x] 2.3 Add 500KB body size guard on `PATCH /api/auth/profile` (return HTTP 413 if exceeded)

## 3. Frontend — Auth Context

- [x] 3.1 Update `User` interface in `AuthContext.tsx`: rename `picture` → `avatar_url` and ensure `display_name` is present
- [x] 3.2 Add `refreshUser(): Promise<void>` method to `AuthContext` that re-calls `GET /api/auth/me` and updates `user` state
- [x] 3.3 Expose `refreshUser` in `AuthContextType` and `AuthProvider`

## 4. Frontend — npm Dependency

- [x] 4.1 Install `react-easy-crop` in the frontend (`npm install react-easy-crop`)

## 5. Frontend — ProfileModal Component

- [x] 5.1 Create `frontend/src/components/ProfileModal.tsx` with display name input, avatar preview circle, and "Change photo" trigger
- [x] 5.2 Implement file input (hidden, `accept="image/*"`) triggered by clicking the avatar area
- [x] 5.3 Implement crop sub-modal using `react-easy-crop` with circular crop, drag to reposition, and zoom slider
- [x] 5.4 Implement `getCroppedImg` canvas helper: renders crop area to 256×256 canvas, returns `canvas.toDataURL('image/jpeg', 0.85)`
- [x] 5.5 Wire Save button: call `PATCH /api/auth/profile`, then `refreshUser()`, then close modal on success
- [x] 5.6 Add loading state on Save button, error message on failure, and ESC/Cancel dismiss

## 6. Frontend — SettingsModal Component

- [x] 6.1 Create `frontend/src/components/SettingsModal.tsx` wrapping the existing Settings page content in a modal overlay
- [x] 6.2 Move all JSX and logic from `frontend/src/pages/Settings.tsx` into `SettingsModal.tsx`

## 7. Frontend — Navbar Refactor

- [x] 7.1 Remove "Settings" from `navLinks` array in `Navbar.tsx`
- [x] 7.2 Add `profileOpen` and `settingsOpen` state to `Navbar.tsx`
- [x] 7.3 Update user dropdown to show "Profile", "Settings" (with divider), and "Logout"; clicking Profile/Settings opens respective modal
- [x] 7.4 Render `<ProfileModal>` and `<SettingsModal>` inside `Navbar.tsx` controlled by the new state
- [x] 7.5 Ensure avatar renders `avatar_url` as `object-cover` filling the circle (update field reference from `picture` → `avatar_url`)

## 8. Frontend — Settings Page Cleanup

- [x] 8.1 Replace the body of `frontend/src/pages/Settings.tsx` with a `<Navigate to="/dashboard" replace />` redirect
- [x] 8.2 Verify that any remaining references to `user.picture` across the frontend are updated to `user.avatar_url`
