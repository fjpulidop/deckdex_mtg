-- Migration 010: Create catalog_cards and catalog_sync_state tables
-- Local card catalog storing all Scryfall card printings for offline lookups

-- catalog_cards: one row per card printing, keyed by Scryfall UUID
CREATE TABLE IF NOT EXISTS catalog_cards (
    scryfall_id TEXT PRIMARY KEY,
    oracle_id TEXT,
    name TEXT NOT NULL,
    type_line TEXT,
    oracle_text TEXT,
    mana_cost TEXT,
    cmc DOUBLE PRECISION,
    colors TEXT,
    color_identity TEXT,
    power TEXT,
    toughness TEXT,
    rarity TEXT,
    set_id TEXT,
    set_name TEXT,
    collector_number TEXT,
    release_date TEXT,
    image_uri_small TEXT,
    image_uri_normal TEXT,
    image_uri_large TEXT,
    prices_eur TEXT,
    prices_usd TEXT,
    prices_usd_foil TEXT,
    edhrec_rank INTEGER,
    keywords TEXT,
    legalities JSONB,
    scryfall_uri TEXT,
    image_status TEXT NOT NULL DEFAULT 'pending',
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_catalog_name ON catalog_cards (name);
CREATE INDEX IF NOT EXISTS idx_catalog_oracle_id ON catalog_cards (oracle_id);
CREATE INDEX IF NOT EXISTS idx_catalog_set ON catalog_cards (set_id);
CREATE INDEX IF NOT EXISTS idx_catalog_image_status ON catalog_cards (image_status);

-- catalog_sync_state: singleton row tracking sync progress
CREATE TABLE IF NOT EXISTS catalog_sync_state (
    id INTEGER PRIMARY KEY DEFAULT 1,
    last_bulk_sync TIMESTAMPTZ,
    last_image_cursor TEXT,
    total_cards INTEGER DEFAULT 0,
    total_images_downloaded INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'idle',
    error_message TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (id = 1)
);

-- Seed the singleton row
INSERT INTO catalog_sync_state (id, status) VALUES (1, 'idle')
ON CONFLICT (id) DO NOTHING;
