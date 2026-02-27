## Why

Card images are currently cached per surrogate `card_id`, meaning the same MTG card downloaded by two different users is stored twice in the database. The cache is user-scoped by accident, not by design — images are public Scryfall data and should be shared globally across all users.

## What Changes

- Replace the per-user `card_images` table with a global `card_image_cache` table keyed by `scryfall_id`
- Add a `scryfall_id` column to the `cards` table (populated lazily on first image request)
- Remove card-ownership check from the image endpoint — authentication (logged-in) is sufficient
- Existing `card_images` data is dropped (pure cache, always re-fetchable from Scryfall)

## Capabilities

### New Capabilities

- `global-image-cache`: A shared image cache keyed by Scryfall UUID (`scryfall_id`). Any user's image request populates the cache for all subsequent users. Stores `scryfall_id`, `content_type`, and binary image data.

### Modified Capabilities

- `card-image-storage`: Requirements change — cache is now global (keyed by `scryfall_id`) instead of per-card-id. The endpoint contract (`GET /api/cards/{id}/image`) remains the same but no longer requires card ownership, only authentication. `scryfall_id` is populated lazily on the `cards` row when first fetched from Scryfall.

## Impact

- **DB schema**: new `scryfall_id TEXT` column on `cards`; drop `card_images`; new `card_image_cache` table
- **Backend**: `card_image_service.py` — new lookup/store logic; `cards` route — remove ownership check
- **Repository**: new `get_card_image_by_scryfall_id`, `save_card_image_to_global_cache`, `update_card_scryfall_id` methods
- **Migrations**: new migration file for schema changes
- **No frontend changes** — endpoint URL and response format unchanged
