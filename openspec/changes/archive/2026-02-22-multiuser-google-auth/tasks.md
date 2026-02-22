# Tasks: Multiuser Google Auth

## 1. Database Migrations

- [x] 1.1 Create migration `005_users_table.sql`: `users` table with `id`, `google_id` (unique), `email` (unique), `display_name`, `avatar_url`, `created_at`, `last_login`
- [x] 1.2 Create migration `006_add_user_id.sql`: add nullable `user_id` column to `cards` and `decks` tables with FK to `users.id`; insert seed user (`admin@deckdex.local`, `google_id='__seed_pending__'`); backfill all existing rows; add NOT NULL constraint; add indexes on `user_id`

## 2. Backend Dependencies and Configuration

- [x] 2.1 Add `python-jose[cryptography]` to `requirements.txt`
- [x] 2.2 Add `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `JWT_SECRET_KEY` to `.env.example` and `docker-compose.yml` environment section

## 3. Backend Auth Layer

- [x] 3.1 Create `backend/api/routes/auth.py` with endpoints: `GET /api/auth/google` (redirect to Google consent), `GET /api/auth/callback` (exchange code, upsert user, set JWT cookie, redirect to frontend), `GET /api/auth/me` (return current user), `POST /api/auth/logout` (clear cookie)
- [x] 3.2 Implement JWT helper functions: `create_jwt(user)` and `decode_jwt(token)` using `python-jose` with `JWT_SECRET_KEY`, 1h expiry, HS256 algorithm
- [x] 3.3 Implement seed user google_id update: when OAuth callback matches email `admin@deckdex.local` and existing user has `google_id='__seed_pending__'`, update to the real Google `sub`
- [x] 3.4 Add `get_current_user` and `get_current_user_id` FastAPI dependencies in `dependencies.py` that read JWT from cookie, validate, and return user payload or raise 401
- [x] 3.5 Register auth router in `backend/api/main.py`

## 4. Backend User-Scoped Data

- [x] 4.1 Update `CollectionRepository` interface: add `user_id` parameter to `get_all_cards`, `create`, `update`, `delete`, `replace_all`, `get_cards_for_price_update`, `get_cards_for_process`, `get_card_by_id`
- [x] 4.2 Update `PostgresCollectionRepository`: add `WHERE user_id = :user_id` to all queries; include `user_id` in INSERT statements
- [x] 4.3 Update `DeckRepository`: add `WHERE user_id = :user_id` to all deck queries; include `user_id` in deck INSERT; scope deck_cards operations through the deck's ownership
- [x] 4.4 Update `backend/api/routes/cards.py`: inject `get_current_user_id` dependency; pass `user_id` to all repository calls
- [x] 4.5 Update `backend/api/routes/decks.py`: inject `get_current_user_id` dependency; pass `user_id` to all deck repository calls
- [x] 4.6 Update `backend/api/routes/stats.py`: inject `get_current_user_id`; scope stats queries by user
- [x] 4.7 Update `backend/api/routes/analytics.py`: inject `get_current_user_id`; scope analytics queries by user
- [x] 4.8 Update `backend/api/routes/process.py`: inject `get_current_user_id`; pass `user_id` so processor and price updates operate only on the user's cards
- [x] 4.9 Update `backend/api/routes/import_routes.py`: inject `get_current_user_id`; set `user_id` on imported cards
- [x] 4.10 Update `backend/api/dependencies.py`: update `get_collection_repo` and `get_deck_repo` helpers; update `get_cached_collection` to accept and use `user_id`

## 5. Frontend Auth Layer

- [x] 5.1 Create `frontend/src/contexts/AuthContext.tsx`: provider that calls `GET /api/auth/me` on mount; exposes `user`, `isAuthenticated`, `isLoading`, `logout()`
- [x] 5.2 Create `frontend/src/pages/Login.tsx`: centered card with DeckDex logo, "Continue with Google" button (links to `/api/auth/google`), error display for `?error=auth_failed`, redirect to `/` if already authenticated
- [x] 5.3 Create `frontend/src/components/ProtectedRoute.tsx`: wraps children; redirects to `/login` when `!isAuthenticated && !isLoading`; shows loading spinner when `isLoading`
- [x] 5.4 Update `frontend/src/App.tsx`: wrap routes with `AuthProvider`; add `/login` route (unprotected); wrap all other routes with `ProtectedRoute`

## 6. Frontend Navbar Updates

- [x] 6.1 Update `frontend/src/components/Navbar.tsx`: add user avatar (circular image or fallback icon), display name, and logout button in the right section (desktop); include these in the mobile hamburger menu
- [x] 6.2 Conditionally hide navbar on `/login` route (do not render `Navbar` when path is `/login`)

## 7. Docker and Environment

- [x] 7.1 Update `docker-compose.yml`: add `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `JWT_SECRET_KEY` to backend service environment
