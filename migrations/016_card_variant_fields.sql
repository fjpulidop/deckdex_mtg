-- DeckDex MTG: add variant treatment fields to cards
-- Run with: psql $DATABASE_URL -f migrations/016_card_variant_fields.sql

ALTER TABLE cards
  ADD COLUMN IF NOT EXISTS finish TEXT NOT NULL DEFAULT 'nonfoil',
  ADD COLUMN IF NOT EXISTS promo_types TEXT,
  ADD COLUMN IF NOT EXISTS frame_effects TEXT,
  ADD COLUMN IF NOT EXISTS border_color TEXT,
  ADD COLUMN IF NOT EXISTS variant_label TEXT;

CREATE INDEX IF NOT EXISTS idx_cards_name_finish ON cards (user_id, name, finish);
