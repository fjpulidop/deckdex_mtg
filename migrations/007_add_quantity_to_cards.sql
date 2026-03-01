-- DeckDex MTG: add quantity field to cards
-- Run with: psql $DATABASE_URL -f migrations/007_add_quantity_to_cards.sql

ALTER TABLE cards ADD COLUMN IF NOT EXISTS quantity INTEGER NOT NULL DEFAULT 1;

CREATE INDEX IF NOT EXISTS idx_cards_name_set_user ON cards (user_id, name, set_id);
