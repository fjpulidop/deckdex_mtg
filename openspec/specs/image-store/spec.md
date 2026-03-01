# Image Store

Abstract image storage interface with filesystem implementation. Replaces PostgreSQL BYTEA storage for card images.

## Requirements

### Requirement: ImageStore abstract interface
The system SHALL define an abstract `ImageStore` interface for image persistence.

#### Scenario: Interface contract
- **GIVEN** the `ImageStore` ABC
- **THEN** it SHALL define methods:
  - `get(key: str) -> Optional[Tuple[bytes, str]]` — returns (data, content_type) or None
  - `put(key: str, data: bytes, content_type: str) -> None` — stores image
  - `exists(key: str) -> bool` — checks if image exists
  - `delete(key: str) -> None` — removes image

### Requirement: FilesystemImageStore implementation
The system SHALL provide a `FilesystemImageStore` that stores images as files on disk.

#### Scenario: Store and retrieve image
- **WHEN** `put("abc-123", jpeg_bytes, "image/jpeg")` is called
- **THEN** the image SHALL be written to `{base_dir}/abc-123.jpg`
- **AND** a metadata sidecar `{base_dir}/abc-123.meta` SHALL store `{"content_type": "image/jpeg"}`
- **AND** `get("abc-123")` SHALL return `(jpeg_bytes, "image/jpeg")`
- **AND** `exists("abc-123")` SHALL return `True`

#### Scenario: Atomic writes
- **WHEN** `put` is called
- **THEN** the image SHALL be written to a temporary file first
- **AND** then atomically renamed to the final path (`os.replace`)
- **SO** concurrent readers never see partial writes

#### Scenario: Content-type to extension mapping
- **GIVEN** the following content types
- **THEN** extensions SHALL map as:
  - `image/jpeg` → `.jpg`
  - `image/png` → `.png`
  - `image/webp` → `.webp`
  - default → `.jpg`

#### Scenario: Missing image returns None
- **WHEN** `get("nonexistent")` is called
- **THEN** it SHALL return `None`

#### Scenario: Base directory auto-created
- **WHEN** `FilesystemImageStore` is initialized with a `base_dir` that doesn't exist
- **THEN** it SHALL create the directory (including parents)
- **AND** `base_dir` SHALL be resolved to an absolute path (`Path.resolve()`)

#### Scenario: Key validation prevents path traversal
- **WHEN** any ImageStore method is called with a key containing `..`, `/`, or null bytes
- **THEN** the method SHALL raise `ValueError`
- **SO** path traversal attacks are prevented

### Requirement: Migrate card_image_service to use ImageStore
The existing `card_image_service.py` SHALL use `ImageStore` instead of PostgreSQL BYTEA for storing and retrieving card images.

#### Scenario: Image read from ImageStore
- **WHEN** `get_card_image(card_id)` finds a `scryfall_id` for the card
- **THEN** it SHALL first check `ImageStore.get(scryfall_id)`
- **AND** if found, return the image without any DB query for image data

#### Scenario: Image stored to ImageStore
- **WHEN** a new image is downloaded from Scryfall
- **THEN** it SHALL be stored via `ImageStore.put(scryfall_id, data, content_type)`
- **AND** NOT inserted into `card_image_cache` table

### Requirement: BYTEA migration to filesystem
The system SHALL provide a migration that moves existing `card_image_cache` data to filesystem.

#### Scenario: Migration reads and writes all cached images
- **WHEN** migration 011 runs
- **THEN** it SHALL iterate all rows in `card_image_cache`
- **AND** write each image to filesystem via `ImageStore.put(scryfall_id, data, content_type)`
- **AND** after all images are written, drop the `card_image_cache` table

#### Scenario: Migration is idempotent
- **WHEN** migration 011 runs and `card_image_cache` table does not exist
- **THEN** it SHALL skip gracefully (no error)
