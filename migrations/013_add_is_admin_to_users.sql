-- Add is_admin column to users table.
-- Defaults to FALSE; bootstrap admin via DECKDEX_ADMIN_EMAIL env var
-- (the application promotes the matching user on first login).

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;
