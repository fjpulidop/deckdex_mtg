## ADDED Requirements

### Requirement: Global image cache table
The system SHALL store card images in a global `card_image_cache` table keyed by `scryfall_id` (Scryfall UUID). This table is shared across all users — one row per card printing, regardless of how many users have that card in their collection.

#### Scenario: First user requests an uncached image
- **WHEN** any authenticated user requests an image for a card whose `scryfall_id` is not in `card_image_cache`
- **THEN** the system SHALL fetch the image from Scryfall, insert it into `card_image_cache`, and return it

#### Scenario: Subsequent user requests the same image
- **WHEN** any authenticated user requests an image for a card whose `scryfall_id` is already in `card_image_cache`
- **THEN** the system SHALL return the cached image without contacting Scryfall

### Requirement: scryfall_id column on cards
The `cards` table SHALL have a `scryfall_id TEXT` column (nullable) that stores the Scryfall UUID for the card printing. This value is populated lazily on first image request.

#### Scenario: scryfall_id populated on first image fetch
- **WHEN** a card row has `scryfall_id = NULL` and an image is requested
- **THEN** after fetching from Scryfall the system SHALL update that card row with the `scryfall_id` returned by Scryfall

#### Scenario: scryfall_id already populated skips Scryfall lookup
- **WHEN** a card row already has a non-null `scryfall_id` and the image is in `card_image_cache`
- **THEN** the system SHALL return the image from cache without calling the Scryfall API
