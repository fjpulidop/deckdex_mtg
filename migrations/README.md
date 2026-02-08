# Database migrations

PostgreSQL migrations for DeckDex MTG (cards and sessions).

**Prerequisites:** PostgreSQL running, `DATABASE_URL` set (e.g. `postgresql://user:password@localhost:5432/deckdex`).

**Run all migrations (in order):**

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/deckdex"
psql "$DATABASE_URL" -f migrations/001_cards_table.sql
psql "$DATABASE_URL" -f migrations/002_sessions_table.sql
psql "$DATABASE_URL" -f migrations/003_card_images_table.sql
```

Or from repo root:

```bash
for f in migrations/*.sql; do psql "$DATABASE_URL" -f "$f"; done
```

**Create the database (if needed):**

```bash
createdb deckdex
```
