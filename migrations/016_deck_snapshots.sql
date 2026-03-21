-- DeckDex MTG: deck_snapshots table for version history and undo
-- Stores full deck card state after each mutating operation.
-- snapshot_data is a JSONB array of {card_id, name, quantity, is_commander}.

CREATE TABLE IF NOT EXISTS deck_snapshots (
    id            BIGSERIAL PRIMARY KEY,
    deck_id       BIGINT NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    created_by    BIGINT NOT NULL REFERENCES users(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    snapshot_data JSONB NOT NULL,
    change_summary TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_deck_snapshots_deck_id_created_at
    ON deck_snapshots (deck_id, created_at DESC);
