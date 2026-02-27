## Why

The app currently shows "Seed User" as the display name after login because the seed user's `display_name` is never updated from the DB default, and there is no way to change it. Users have no way to personalize their identity in the app. Additionally, Settings is exposed as a top-level navbar link, which is not standard UX — it should be contextual to the user.

## What Changes

- `GET /api/auth/me` will read the user record from the database on every call instead of returning stale JWT payload data, so profile updates are immediately visible
- New `PATCH /api/auth/profile` endpoint allows updating `display_name` and `avatar_url`
- New `ProfileModal` component lets users set a custom username and upload a profile photo with interactive circular crop
- Settings is removed from the top navbar and moved to the user dropdown menu, accessed as a modal
- The user dropdown now contains: Profile, Settings, and Logout
- Profile photo is stored as a base64 data URI in `users.avatar_url` (no migration needed — column already exists as TEXT)

## Capabilities

### New Capabilities

- `user-profile`: User profile editor — view and edit display name and avatar photo. Includes interactive circular crop UI for photos. Accessed from navbar user dropdown as a modal overlay.

### Modified Capabilities

- `user-auth`: `/me` changes to read from DB instead of JWT; new `PATCH /profile` endpoint added; `AuthContext` gains `refreshUser()` method; `User` type updates `picture` → `avatar_url`
- `navigation-ui`: Settings link removed from primary nav links; user dropdown extended with Profile and Settings entries; Settings converted from a routed page to a modal

## Impact

- **Backend**: `auth.py` (2 route changes), `repository.py` (new `update_user_profile` method)
- **Frontend**: `AuthContext.tsx`, `Navbar.tsx`, new `ProfileModal.tsx`, new `SettingsModal.tsx`, `Settings.tsx` (gutted/redirected), `App.tsx` (route change)
- **Dependencies**: `react-easy-crop` npm package (circular crop UI)
- **No DB migration needed**: `users.avatar_url TEXT` already exists and accepts base64 data URIs
