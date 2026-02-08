-- DeckDex MTG: card_images table (PostgreSQL)
-- Run with: psql $DATABASE_URL -f migrations/003_card_images_table.sql
-- Stores card image bytes so they persist across sessions and do not require re-downloading from Scryfall.

CREATE TABLE IF NOT EXISTS card_images (
    card_id BIGINT PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
    content_type TEXT NOT NULL,
    data BYTEA NOT NULL
);
