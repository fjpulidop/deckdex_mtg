-- DeckDex MTG: decks and deck_cards tables (PostgreSQL)
-- Decks reference cards from the collection by card id.

CREATE TABLE IF NOT EXISTS decks (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS deck_cards (
    deck_id BIGINT NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    card_id BIGINT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    is_commander BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (deck_id, card_id)
);

CREATE INDEX IF NOT EXISTS idx_deck_cards_deck_id ON deck_cards (deck_id);
CREATE INDEX IF NOT EXISTS idx_deck_cards_card_id ON deck_cards (card_id);
