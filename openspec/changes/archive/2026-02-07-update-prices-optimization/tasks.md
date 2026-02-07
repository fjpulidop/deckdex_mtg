## 1. Configuration Updates

- [x] 1.1 Add write_buffer_batches parameter to ProcessorConfig in deckdex/config.py with default value of 3
- [x] 1.2 Add validation for write_buffer_batches in ProcessorConfig.__post_init__ (must be >= 1)
- [x] 1.3 Store write_buffer_batches as instance variable in MagicCardProcessor.__init__

## 2. Helper Method Implementation

- [x] 2.1 Create _write_buffered_prices method in MagicCardProcessor that accepts list of (row_index, card_name, new_price) tuples
- [x] 2.2 Implement batch update construction using gspread.utils.rowcol_to_a1 and cached price column index
- [x] 2.3 Call existing _batch_update_prices method for actual write with retry logic
- [x] 2.4 Return count of prices written from _write_buffered_prices
- [x] 2.5 Add error handling to log failures and continue (maintain existing error strategy)

## 3. Refactor update_prices_data Method

- [x] 3.1 Initialize pending_changes list and batches_processed counter at start of method
- [x] 3.2 Initialize write_counter for progress notifications
- [x] 3.3 Modify verification loop to accumulate changes in pending_changes buffer instead of single changed_prices list
- [x] 3.4 Add buffer write trigger logic: when batches_processed >= write_buffer_batches
- [x] 3.5 Call _write_buffered_prices when buffer threshold is reached
- [x] 3.6 Print progress notification after each write with format "✓ Write #N (X cards): Y updates"
- [x] 3.7 Reset pending_changes and batches_processed after each write
- [x] 3.8 Add sleep(1.5) after each incremental write for rate limiting
- [x] 3.9 Write remaining pending_changes after verification loop completes (partial buffer)

## 4. Progress Reporting Enhancements

- [x] 4.1 Keep existing tqdm progress bar for verification phase
- [x] 4.2 Print write notifications below progress bar without disrupting it
- [x] 4.3 Add final summary message showing total cards verified and total prices updated
- [x] 4.4 Add resume-from hint message with format "💡 To resume from here: --resume-from N"

## 5. Testing

- [x] 5.1 Test with --dry-run mode to verify no actual writes occur but logic executes
- [x] 5.2 Test with small dataset (--limit 50) to verify buffer triggers at 60 cards (3 batches × 20)
- [x] 5.3 Test with 150 cards to verify multiple buffer writes occur
- [x] 5.4 Manually interrupt process mid-execution and verify partial writes in Google Sheets
- [x] 5.5 Test --resume-from flag still works correctly with incremental writes
- [x] 5.6 Test error scenario: simulate Google Sheets API failure and verify retry/continue behavior

## 6. Documentation

- [x] 6.1 Update README.md to document incremental write behavior
- [x] 6.2 Add note about expected execution time increase (~25s per 1000 cards)
- [x] 6.3 Document data loss window improvement (60 cards max vs all cards)
- [x] 6.4 Add example of using --resume-from after interruption

## 7. Error Reporting Improvements

- [x] 7.1 Replace multiple "Cards not found" print statements with single-line counter that refreshes in place
- [x] 7.2 Create output/ directory if it doesn't exist
- [x] 7.3 Generate CSV file with failed cards (format: output/failed_cards_YYYYMMDD_HHMMSS.csv)
- [x] 7.4 CSV should include columns: card_name, error_type, timestamp
- [x] 7.5 Print summary at end showing path to error CSV if any cards failed

## 8. Use English Names for Lookup

- [x] 8.1 Update SpreadsheetClient.get_all_cards_prices() to find "English name" column index
- [x] 8.2 Read "English name" column instead of "Name" column for card lookup
- [x] 8.3 Add fallback: if "English name" is empty, use "Name" column value
- [x] 8.4 Update error messages to show which name was used for lookup
- [x] 8.5 Update dry_run_client.py to match new column usage

## 9. Write Prices as Numeric Values

- [x] 9.1 Add helper method to convert price string to numeric value (handle comma/period decimals)
- [x] 9.2 Update _write_buffered_prices to convert prices to float before writing
- [x] 9.3 Handle edge cases: empty strings, "N/A", invalid formats (keep as "N/A")
- [x] 9.4 Ensure batch update uses numeric values for price cells
- [x] 9.5 Test that SUM formulas work correctly with updated numeric prices

## 10. Sync Main Specs with Archived Changes

- [x] 10.1 Update architecture.md to reflect CLI simplification and price update enhancements
- [x] 10.2 Copy processor-configuration spec from archived change to main specs
- [x] 10.3 Copy cli-interface spec from archived change to main specs
- [x] 10.4 Copy verbose-logging spec from archived change to main specs
- [x] 10.5 Copy dry-run-mode spec from archived change to main specs
- [x] 10.6 Update processor-configuration spec with write_buffer_batches parameter
- [x] 10.7 Verify OpenAI integration specs are aligned (already synced)
