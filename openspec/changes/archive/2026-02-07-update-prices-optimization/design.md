## Context

The current price update implementation in `MagicCardProcessor.update_prices_data()` follows this flow:
1. Read all cards and current prices from Google Sheets
2. Verify prices via Scryfall API in parallel batches (20 cards per batch, 4 workers)
3. Accumulate ALL price changes in memory during verification
4. Write ALL changes to Google Sheets at the end in large batches (200 cells per batch)

This approach is efficient for API quota management but creates a single point of failure at the write phase. If the process crashes, is interrupted, or encounters an error after verification but before/during writes, all progress is lost.

The codebase already has retry logic with exponential backoff for Google Sheets API quota issues, and `--resume-from` support for restarting from a specific row. However, `--resume-from` only helps if the failure occurs during verification, not during the final write phase.

## Goals / Non-Goals

**Goals:**
- Enable incremental writes to Google Sheets during price verification
- Provide visible progress as prices are written (not just verified)
- Minimize data loss window from "all changes" to "one buffer's worth of changes"
- Maintain existing API rate limiting and retry logic
- Keep backward compatibility with current CLI arguments and behavior

**Non-Goals:**
- Persistent checkpoint file system (out of scope for this change)
- Auto-resume functionality (manual `--resume-from` remains)
- Optimizing Scryfall API verification speed (already well-tuned)
- Changes to error handling strategy (continue on error vs abort)

## Decisions

### Decision 1: Buffered Write Strategy (Strategy B)

**Choice:** Write to Google Sheets every N verification batches (buffer approach)

**Rationale:**
- **Strategy A (write after each batch)**: Too many Google Sheets API calls, higher quota risk
- **Strategy B (buffer N batches)**: Balance between visibility and API efficiency ✓
- **Strategy C (checkpoint file)**: Too complex for the current need

Buffer size of 3 batches = 60 cards provides good balance:
- Write frequency: Every 60 cards verified (~6 seconds of work)
- API impact: 17 writes for 1000 cards vs 5 (current) or 50 (Strategy A)
- Data loss window: Max 60 cards if process crashes mid-buffer

**Alternatives Considered:**
- Larger buffer (5-10 batches): Less frequent writes but wider loss window
- Smaller buffer (1-2 batches): More frequent writes, higher quota pressure

### Decision 2: Configuration Approach

**Choice:** Add `write_buffer_batches` parameter to `ProcessorConfig` with default value of 3

**Rationale:**
- Configuration object already exists and is well-structured
- Default value (3) provides sensible behavior without user intervention
- Can be exposed as CLI argument later if needed (`--write-buffer N`)
- No environment variable needed (internal optimization parameter)

**Location:** `deckdex/config.py`

```python
write_buffer_batches: int = 3  # Write every N verification batches
```

**Alternatives Considered:**
- CLI argument immediately: Premature - let users validate default first
- Hardcoded constant: Less flexible if we want to tune later

### Decision 3: Progress Reporting Enhancement

**Choice:** Augment existing tqdm progress bar with inline write notifications

**Format:**
```
Verifying prices: 100% |████████| 1000/1000 [1:45<00:00]
✓ Write #1 (60 cards): 18 updates
✓ Write #2 (60 cards): 22 updates
...
```

**Rationale:**
- Minimal disruption to existing progress bar
- Clear indication that writes are happening incrementally
- Shows write frequency and impact (how many actual price changes per buffer)

**Alternatives Considered:**
- Replace progress bar: Too disruptive, loses time estimates
- No additional output: Defeats purpose of making writes visible

### Decision 4: Error Handling Strategy

**Choice:** Maintain existing "retry and continue" approach

**Current behavior:** If a Google Sheets write fails after retries, log error and continue processing

**Rationale:**
- Already proven in production with the current implementation
- Partial success is better than complete failure for large datasets
- User can manually review Google Sheets and use `--resume-from` for failed sections

**Alternatives Considered:**
- Abort on write failure: Too strict, loses all progress
- Save failed writes to file: Adds complexity, out of scope

### Decision 5: Backward Compatibility

**Choice:** Preserve all existing behavior as defaults

- Verification batch size: 20 cards (unchanged)
- Workers: 4 (unchanged)
- API delays and retries: unchanged
- CLI arguments: no changes required
- Write batch size to Google Sheets: 200 cells (unchanged)

**Only change:** WHEN writes happen (incrementally vs at end)

## Risks / Trade-offs

### Risk: Increased Google Sheets API calls
**Impact:** 17 writes instead of 5 for 1000 cards

**Mitigation:**
- Existing exponential backoff retry logic handles quota issues
- Buffer size tunable if needed (increase to 5 for fewer writes)
- Delay between writes (1.5s) already in place

### Risk: Slightly longer execution time
**Impact:** ~25 seconds added for 1000 cards (105s → 130s)

**Mitigation:**
- Acceptable trade-off for progress visibility and resilience
- Time increase is predictable (number of buffers × 1.5s delay)
- Can be communicated in documentation

### Risk: Data loss window still exists
**Impact:** Up to 60 cards of progress can be lost if process crashes mid-buffer

**Mitigation:**
- Significantly better than current "all or nothing" (1000 cards)
- `--resume-from` still works for manual recovery
- Could implement Strategy C (checkpoint file) in future if needed

### Risk: Progress bar noise
**Impact:** More output lines from write notifications

**Mitigation:**
- Write notifications only appear every 60 cards (not per card)
- Provides valuable feedback about what's happening
- Minimal compared to value of progress visibility

## Implementation Approach

### Code Changes

**1. Modify `deckdex/config.py`:**
```python
@dataclass
class ProcessorConfig:
    # ... existing fields ...
    write_buffer_batches: int = 3  # Write every N verification batches
```

**2. Refactor `deckdex/magic_card_processor.py`:**

In `update_prices_data()` method:
- Change loop structure from "accumulate then write all" to "accumulate and write periodically"
- Track `batches_processed` counter
- Track `pending_changes` buffer
- When `batches_processed >= write_buffer_batches`:
  - Call `_write_buffered_prices(pending_changes)`
  - Reset `pending_changes` and `batches_processed`
  - Print progress notification
- After loop: write remaining pending changes

**3. Add helper method:**
```python
def _write_buffered_prices(self, changes: List[Tuple[int, str, str]]) -> int:
    """Write buffered price changes to Google Sheets.
    
    Args:
        changes: List of (row_index, card_name, new_price)
        
    Returns:
        Number of prices actually written
    """
    # Same logic as current batch write, but extracted and reusable
```

### Migration Plan

**Deployment:**
1. Update `config.py` with new parameter
2. Update `magic_card_processor.py` with buffered write logic
3. Test with `--dry-run` mode first
4. Test with small dataset (`--limit 100`)
5. Deploy to production

**Rollback:**
- No database migrations or persistent state changes
- Simple git revert restores original behavior
- No data corruption risk (writes are additive updates)

**Testing:**
- Unit test: verify buffer logic triggers at correct intervals
- Integration test: verify writes happen incrementally with `--dry-run`
- Manual test: interrupt process mid-execution and verify partial writes in Google Sheets

## Open Questions

1. Should `write_buffer_batches` be exposed as a CLI argument in v1?
   - **Recommendation:** No, start with default (3) and gather feedback
   - Can add `--write-buffer N` later if users need tuning

2. Should we add a summary message at the end with resume-from hint?
   - **Recommendation:** Yes, helpful for users
   - Format: `💡 To resume from here: --resume-from 1000`

3. Should write notifications show number of changes or number of cards?
   - **Recommendation:** Both
   - Format: `✓ Write #1 (60 cards): 18 price updates`

## Additional Enhancements (Post-Implementation)

### Decision 6: Error Reporting Improvements

**Choice:** Improve error reporting with single-line counter updates and CSV error log

**Changes:**
1. Replace multiple "Cards not found" messages with a single refreshing counter line
2. Generate CSV report of failed cards at `output/failed_cards_{timestamp}.csv`
3. CSV includes: card name, error type, timestamp

**Rationale:**
- Cleaner terminal output (no spam of error messages)
- Persistent error log for review and correction
- Easier to track which cards failed and why

### Decision 7: Use English Names for Scryfall Lookup

**Choice:** Change column used for price lookup from "Name" to "English name"

**Rationale:**
- Scryfall API has better coverage for English card names
- More likely to find price data for English cards
- Reduces "card not found" errors for non-English name entries
- User already has English names column populated in their sheet

**Implementation:**
- Update `get_all_cards_prices()` in SpreadsheetClient to read "English name" column
- Fallback to "Name" column if "English name" is empty
- Update error messages to show which column was used

### Decision 8: Write Prices as Numeric Values

**Choice:** Ensure price values are written to Google Sheets as numbers, not text

**Changes:**
1. Convert price strings to numeric format before writing to sheets
2. Replace comma decimal separator with period (e.g., "1,50" → 1.50)
3. Keep "N/A" as text for missing prices (Google Sheets handles this in SUM formulas)
4. Use numeric cell format in batch updates

**Rationale:**
- Enables mathematical operations (SUM, AVERAGE, etc.) in Google Sheets
- Prevents "numbers stored as text" warnings
- Maintains spreadsheet usability for financial calculations
- "N/A" text values are automatically ignored by SUM functions

**Implementation Details:**
- In `_write_buffered_prices()`: convert price string to float before writing
- Handle edge cases: empty strings, "N/A", invalid formats
- Use proper numeric format in gspread batch updates
