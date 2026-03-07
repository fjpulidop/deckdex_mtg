-- DeckDex MTG: price_history table
-- Records every price observation per card for time-series tracking.

CREATE TABLE IF NOT EXISTS price_history (
    id          BIGSERIAL PRIMARY KEY,
    card_id     BIGINT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    source      TEXT NOT NULL DEFAULT 'scryfall',
    currency    TEXT NOT NULL DEFAULT 'eur',
    price       NUMERIC(10, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_price_history_card_id_recorded_at
    ON price_history (card_id, recorded_at DESC);
