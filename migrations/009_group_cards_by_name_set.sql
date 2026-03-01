-- DeckDex MTG: group duplicate (user_id, name, set_id) card rows into one with summed quantity
-- Run with: psql $DATABASE_URL -f migrations/009_group_cards_by_name_set.sql
-- Safe to run multiple times (idempotent after first run).

BEGIN;

-- For each group of duplicate (user_id, name, set_id), keep the row with the lowest id,
-- set its quantity to the total count of duplicates, and delete the rest.
WITH grouped AS (
    SELECT
        MIN(id) AS keep_id,
        user_id,
        name,
        set_id,
        COUNT(*) AS total_qty
    FROM cards
    WHERE name IS NOT NULL AND name != ''
    GROUP BY user_id, name, set_id
    HAVING COUNT(*) > 1
)
UPDATE cards c
SET quantity = g.total_qty
FROM grouped g
WHERE c.id = g.keep_id;

DELETE FROM cards
WHERE id NOT IN (
    SELECT MIN(id)
    FROM cards
    WHERE name IS NOT NULL AND name != ''
    GROUP BY user_id, name, set_id
)
AND name IS NOT NULL AND name != '';

COMMIT;
