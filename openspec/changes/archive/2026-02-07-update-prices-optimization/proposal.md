## Why

The current `update_prices` mode fetches prices for all cards from Scryfall API but only writes updates to Google Sheets at the very end of the process. This creates several problems: no intermediate visibility into progress, inability to resume from a specific point if the process fails during the write phase, and potential loss of all verified price data if the final batch write fails. For large collections (1000+ cards), this means waiting 2-3 minutes with no feedback, and any failure requires starting over from scratch.

## What Changes

- Implement buffered batch writes during price update verification instead of accumulating all changes in memory
- Write price updates to Google Sheets every N verification batches (configurable buffer size)
- Add progress indicators showing intermediate write operations and their results
- Maintain compatibility with existing `--resume-from` functionality for interrupted processes
- Add configuration parameter for write buffer size with sensible default (3-5 batches)

## Capabilities

### New Capabilities
- `buffered-price-updates`: Incremental writing of price changes to Google Sheets during verification phase, with configurable buffer size and progress tracking

### Modified Capabilities
- `price-updates`: Enhanced the existing price update workflow to support incremental writes while maintaining backward compatibility with current behavior

## Impact

**Affected Code:**
- `deckdex/magic_card_processor.py`: `update_prices_data()` method requires refactoring to write incrementally
- `deckdex/config.py`: New configuration parameter `write_buffer_batches` (default: 3)
- Progress reporting: Enhanced feedback during write operations

**User Experience:**
- Users will see price updates appearing in Google Sheets progressively during execution
- Failed processes can be resumed with minimal data loss (max 60-100 cards depending on buffer size)
- Slightly longer total execution time (~25 seconds for 1000 cards) due to more frequent API calls to Google Sheets

**No Breaking Changes:**
- Existing CLI arguments remain unchanged
- Default behavior maintains same verification batch size (20 cards)
- `--resume-from` continues to work as before
