-- DeckDex MTG: card filter indexes
-- Composite index on (user_id, rarity) for filtered queries that combine user scope
-- with rarity filtering. Index on cmc for range queries and analytics GROUP BY.

CREATE INDEX IF NOT EXISTS idx_cards_user_rarity ON cards (user_id, rarity);

CREATE INDEX IF NOT EXISTS idx_cards_cmc ON cards (cmc);
