-- Migration 016: New Set Card Recommendations
-- Tracks which Scryfall set codes have already been processed
-- so the polling job can detect new sets incrementally.
CREATE TABLE IF NOT EXISTS seen_set_codes (
    set_code     TEXT PRIMARY KEY,
    set_name     TEXT NOT NULL,
    released_at  DATE NOT NULL,
    detected_at  TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- Cached per-deck suggestions, one row per (deck, card) pair.
-- Truncated and rebuilt whenever a new set is detected.
CREATE TABLE IF NOT EXISTS deck_suggestions (
    id              BIGSERIAL PRIMARY KEY,
    deck_id         BIGINT NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL,
    set_code        TEXT NOT NULL,
    scryfall_id     TEXT NOT NULL,
    card_name       TEXT NOT NULL,
    mana_cost       TEXT,
    cmc             NUMERIC(5, 2),
    type_line       TEXT,
    color_identity  TEXT,
    oracle_text     TEXT,
    reason          TEXT NOT NULL,
    score           NUMERIC(8, 4) NOT NULL DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX IF NOT EXISTS idx_deck_suggestions_deck_id
    ON deck_suggestions (deck_id);
CREATE INDEX IF NOT EXISTS idx_deck_suggestions_user_id
    ON deck_suggestions (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_deck_suggestions_deck_card
    ON deck_suggestions (deck_id, scryfall_id);
