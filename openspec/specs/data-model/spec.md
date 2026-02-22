# data-model Specification

## Purpose
TBD - created by archiving change multiuser-google-auth. Update Purpose after archive.
## Requirements
### Requirement: Users entity
The data model SHALL include a `users` entity for storing authenticated user identity from Google OAuth.

#### Scenario: Users table schema
- **WHEN** the database is set up
- **THEN** the `users` table SHALL have columns: `id` (bigserial PK), `google_id` (text, unique, not null), `email` (text, unique, not null), `display_name` (text, nullable), `avatar_url` (text, nullable), `created_at` (timestamptz, default now), `last_login` (timestamptz, default now)

### Requirement: Cards have user ownership
Each card in the `cards` table SHALL be associated with a user via a `user_id` foreign key.

#### Scenario: Cards table user_id column
- **WHEN** the database is set up after migration
- **THEN** the `cards` table SHALL have a `user_id` column (bigint, NOT NULL, FK to `users.id`) with an index

#### Scenario: Card belongs to one user
- **WHEN** a card is created
- **THEN** the card SHALL have a non-null `user_id` referencing the creating user

### Requirement: Decks have user ownership
Each deck in the `decks` table SHALL be associated with a user via a `user_id` foreign key.

#### Scenario: Decks table user_id column
- **WHEN** the database is set up after migration
- **THEN** the `decks` table SHALL have a `user_id` column (bigint, NOT NULL, FK to `users.id`) with an index

#### Scenario: Deck belongs to one user
- **WHEN** a deck is created
- **THEN** the deck SHALL have a non-null `user_id` referencing the creating user

### Requirement: Seed migration for existing data
The migration SHALL create a seed user for `fj.pulidop@gmail.com` and assign all existing cards and decks to that user.

#### Scenario: Seed user created
- **WHEN** migration 005 runs
- **THEN** a user row SHALL be created with `email = 'fj.pulidop@gmail.com'` and `google_id = '__seed_pending__'`

#### Scenario: Existing data assigned to seed user
- **WHEN** migration 006 runs
- **THEN** all existing `cards` and `decks` rows with `user_id IS NULL` SHALL be updated to reference the seed user's ID

#### Scenario: Seed user google_id updated on first login
- **WHEN** the seed user logs in with Google for the first time
- **THEN** the backend SHALL update `google_id` from `'__seed_pending__'` to the real Google `sub` value

