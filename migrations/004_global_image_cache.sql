-- DeckDex MTG: global image cache migration
-- Adds scryfall_id to cards, drops per-user card_images, creates global card_image_cache.
-- Run with: psql $DATABASE_URL -f migrations/004_global_image_cache.sql

-- 1. Add scryfall_id to cards (nullable, populated lazily on first image request)
ALTER TABLE cards ADD COLUMN IF NOT EXISTS scryfall_id TEXT;

CREATE INDEX IF NOT EXISTS idx_cards_scryfall_id ON cards (scryfall_id);

-- 2. Drop old per-user image cache
DROP TABLE IF EXISTS card_images;

-- 3. Create global image cache keyed by scryfall_id
CREATE TABLE IF NOT EXISTS card_image_cache (
    scryfall_id TEXT PRIMARY KEY,
    content_type TEXT NOT NULL,
    data BYTEA NOT NULL,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);
