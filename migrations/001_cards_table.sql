-- DeckDex MTG: cards table (PostgreSQL)
-- Run with: psql $DATABASE_URL -f migrations/001_cards_table.sql
-- Surrogate id + columns aligned to Card model (data-model.md).

CREATE TABLE IF NOT EXISTS cards (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    english_name TEXT,
    type_line TEXT,
    description TEXT,
    keywords TEXT,
    mana_cost TEXT,
    cmc DOUBLE PRECISION,
    colors TEXT,
    color_identity TEXT,
    power TEXT,
    toughness TEXT,
    rarity TEXT,
    set_id TEXT,
    set_name TEXT,
    set_number TEXT,
    release_date TEXT,
    edhrec_rank TEXT,
    scryfall_uri TEXT,
    price_eur TEXT,
    price_usd TEXT,
    price_usd_foil TEXT,
    last_price_update TIMESTAMP WITH TIME ZONE,
    game_strategy TEXT,
    tier TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX IF NOT EXISTS idx_cards_name ON cards (name);
CREATE INDEX IF NOT EXISTS idx_cards_set_name ON cards (set_name);
