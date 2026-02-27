## Context

Card images are fetched from Scryfall and stored in a `card_images` table keyed by the surrogate `card_id`. Because `card_id` is per-user/per-import, the same MTG card can be stored multiple times — once per user who has it in their collection. The `GET /api/cards/{id}/image` endpoint verifies that the requesting user owns the card before returning the image, which is unnecessary since card images are public data.

The Scryfall API returns a UUID (`id` field) for each card printing. This `scryfall_id` is the natural global key for a card image — stable, unique per printing, and already present in Scryfall's API response. It is not currently persisted in the `cards` table.

## Goals / Non-Goals

**Goals:**
- One copy of each card image stored globally, shared across all users
- `scryfall_id` persisted on `cards` rows for future use
- Image endpoint only requires authentication, not card ownership
- No frontend changes required

**Non-Goals:**
- Eager backfill of `scryfall_id` for existing cards (deferred to a future script)
- Multiple image resolutions or formats
- CDN or filesystem-based image serving
- Pre-warming the cache for all known cards

## Decisions

### 1. Global cache table keyed by `scryfall_id`

Replace `card_images` (keyed by `card_id`) with `card_image_cache` (keyed by `scryfall_id TEXT PRIMARY KEY`).

**Why**: `scryfall_id` is the canonical, stable identifier for a card printing across all users. Using it as the cache key guarantees at most one stored image per card printing regardless of how many users have it.

**Alternative considered**: Keep `card_images` and add a `scryfall_id` column + unique index. Rejected — two tables with overlapping purpose; cleaner to replace.

### 2. Lazy `scryfall_id` population on `cards`

Add `scryfall_id TEXT` column to `cards` (nullable). When a user first requests an image for a card that has no `scryfall_id`, the service fetches from Scryfall, extracts the `id` field, and writes it back to the `cards` row.

**Why**: No downtime migration needed, no Scryfall rate-limit pressure, no complexity. The value propagates naturally as users interact with the system.

**Alternative considered**: Eager backfill migration script. Useful later as an optimization but not required for correctness.

### 3. Drop existing `card_images` data

On migration, drop the `card_images` table entirely rather than attempting to convert it.

**Why**: `card_images` is a pure cache — all data is re-fetchable from Scryfall on demand. A conversion would require calling Scryfall per row to get the `scryfall_id`, which is slow and rate-limited. The lazy approach recovers the cache organically as users request images.

### 4. Image endpoint: auth-only, no ownership check

`GET /api/cards/{id}/image` will verify the user is authenticated but will not check that `card_id` belongs to the requesting user.

**Why**: Card images are public data (Scryfall distributes them openly). Ownership check adds latency and complexity with zero security benefit. An authenticated user who guesses a `card_id` can only retrieve a card image — a public asset.

### 5. Lookup flow: card_id → scryfall_id → global cache

```
GET /api/cards/{id}/image
  → lookup cards row by card_id (get name + scryfall_id)
  → if scryfall_id known:
      → check card_image_cache → HIT → return
  → if scryfall_id unknown OR cache miss:
      → fetch from Scryfall by name → get scryfall_card (includes id)
      → if scryfall_id was unknown: UPDATE cards SET scryfall_id=...
      → check cache again (another user may have just populated it)
      → HIT → return  |  MISS → download → INSERT cache → return
```

The double-check after Scryfall lookup prevents a small race condition where two concurrent first-requesters both fetch from Scryfall — the second one will hit the cache after the first inserts.

## Risks / Trade-offs

- **First-request latency unchanged**: Images still incur Scryfall round-trip on cache miss. Acceptable — same as before, and improves over time as cache fills.
- **Different printings per user**: Two users with "Black Lotus" from different sets may resolve different `scryfall_id`s via name lookup. Both get cached independently. Correct behavior — different printings, different images.
- **Scryfall name ambiguity**: Name-based lookup can return unexpected printings. Pre-existing issue, not introduced here.
- **card_id enumeration**: Removing ownership check means any authenticated user can request any `card_id`. No security impact since images are public, but worth documenting.

## Migration Plan

1. Apply migration: add `scryfall_id` to `cards`, drop `card_images`, create `card_image_cache`
2. Deploy new backend code
3. Cache warms lazily as users request images (no downtime, no data loss that matters)

**Rollback**: Revert code deploy + apply reverse migration (drop `scryfall_id` from `cards`, recreate `card_images` empty, drop `card_image_cache`). Cache starts empty — same as a fresh install.

## Open Questions

- None blocking implementation. Future work: backfill script to pre-warm cache for all cards in the DB.
