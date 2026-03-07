# Delta Spec: Image Store — Key Validation and Path Access

Base spec: `openspec/specs/image-store/spec.md`

## Changes

### Updated Requirement: Key validation prevents path traversal

Replaces the existing "Key validation prevents path traversal" scenario in the base spec.

#### Scenario: Key with embedded slash is rejected
- **WHEN** any `ImageStore` method is called with a key containing `/` anywhere in the string (not just at position 0)
- **THEN** the method SHALL raise `ValueError`
- **SO** path traversal via subdirectory creation is prevented

#### Scenario: Keys that were already rejected remain rejected
- The following key patterns SHALL continue to raise `ValueError`:
  - Empty string `""`
  - Keys containing `..`
  - Keys starting with `/` (now subsumed by the "containing `/`" rule)
  - Keys containing null bytes `\x00`

### New Requirement: Filesystem path access

The `ImageStore` ABC SHALL provide a `get_path` method for callers that need to serve files directly (e.g., via HTTP `FileResponse`).

#### Scenario: `get_path` returns path for stored image
- **GIVEN** an image stored via `put(key, data, content_type)`
- **WHEN** `get_path(key)` is called
- **THEN** it SHALL return an absolute `Path` pointing to the image file on disk
- **AND** the returned path SHALL exist and be readable

#### Scenario: `get_path` returns None for missing image
- **WHEN** `get_path(key)` is called for a key that has no stored image
- **THEN** it SHALL return `None`

#### Scenario: `get_path` raises ValueError for invalid key
- **WHEN** `get_path` is called with an invalid key (containing `/`, `..`, or null bytes)
- **THEN** it SHALL raise `ValueError` (same as `get`, `put`, `exists`, `delete`)

### New Requirement: Content-type metadata access

`FilesystemImageStore` SHALL provide a `get_content_type(key)` method that reads content type from the metadata sidecar without loading image bytes.

#### Scenario: `get_content_type` reads from sidecar
- **GIVEN** an image stored via `put(key, data, "image/webp")`
- **WHEN** `get_content_type(key)` is called
- **THEN** it SHALL return `"image/webp"` without reading the image file

#### Scenario: `get_content_type` falls back to extension
- **GIVEN** an image file exists for `key` but no `.meta` sidecar
- **WHEN** `get_content_type(key)` is called
- **THEN** it SHALL infer the content type from the file extension (`_EXT_TO_CONTENT_TYPE`)

#### Scenario: `get_content_type` returns None for missing image
- **WHEN** `get_content_type(key)` is called and no image file exists
- **THEN** it SHALL return `None`
