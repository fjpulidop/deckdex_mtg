# Data Model — Delta Spec

This delta updates the data model spec to formally define the `price_history` table.

## Addition: price_history table

Add to the data model spec under a new "Price History" section:

**PriceHistory** (Postgres only): `id` (BIGSERIAL PK), `card_id` (BIGINT FK → cards.id ON DELETE CASCADE), `recorded_at` (TIMESTAMPTZ, default NOW() UTC), `source` (TEXT, default 'scryfall'), `currency` (TEXT, default 'eur'), `price` (NUMERIC(10,2) NOT NULL).

Cardinality: `Card 1:N PriceHistory`. A card may have zero or many price history records.

The `price_history` table is append-only by convention. No application code updates or deletes individual rows; cascade delete on `cards` removes orphaned records automatically.

## Type clarification

The existing `cards.price_eur` column remains `TEXT` (existing data, no migration needed). New `price_history.price` uses `NUMERIC(10,2)` for exact decimal arithmetic. This is intentional: changing `price_eur` to numeric would require a data migration and break existing text-based price parsing logic.

## Migration

Introduced in migration `014_price_history.sql`.
