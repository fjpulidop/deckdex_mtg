-- Phase 1: Add nullable user_id columns with FK to users table
ALTER TABLE cards ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES users(id);
ALTER TABLE decks ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES users(id);

-- Phase 2: Create seed user for existing data
-- The google_id '__seed_pending__' will be updated on first real OAuth login
INSERT INTO users (google_id, email, display_name, avatar_url, created_at, last_login)
VALUES ('__seed_pending__', 'fj.pulidop@gmail.com', 'Seed User', NULL, NOW() AT TIME ZONE 'utc', NOW() AT TIME ZONE 'utc')
ON CONFLICT (email) DO NOTHING;

-- Phase 3: Backfill existing rows with seed user ID
UPDATE cards SET user_id = (SELECT id FROM users WHERE email = 'fj.pulidop@gmail.com') WHERE user_id IS NULL;
UPDATE decks SET user_id = (SELECT id FROM users WHERE email = 'fj.pulidop@gmail.com') WHERE user_id IS NULL;

-- Phase 4: Add NOT NULL constraint
ALTER TABLE cards ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE decks ALTER COLUMN user_id SET NOT NULL;

-- Phase 5: Add indexes on user_id for query performance
CREATE INDEX IF NOT EXISTS idx_cards_user_id ON cards (user_id);
CREATE INDEX IF NOT EXISTS idx_decks_user_id ON decks (user_id);
