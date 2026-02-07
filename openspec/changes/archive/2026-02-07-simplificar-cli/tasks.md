## 1. Create New Modules

- [x] 1.1 Create `deckdex/config.py` with `ProcessorConfig` dataclass
- [x] 1.2 Add type hints for all configuration fields (bool, int, float, Optional[str], Optional[int])
- [x] 1.3 Implement `__post_init__` validation for all constraints
- [x] 1.4 Add `ClientFactory.create_spreadsheet_client()` static method in config.py
- [x] 1.5 Create `deckdex/dry_run_client.py` with `DryRunClient` class
- [x] 1.6 Implement `DryRunClient` interface methods (get_cards, get_all_cards_prices, update_column, update_cells)
- [x] 1.7 Add operation logging in DryRunClient with "DRY RUN:" prefix
- [x] 1.8 Implement statistics collection in DryRunClient (operation counts)
- [x] 1.9 Create `deckdex/logger_config.py` with `configure_logging(verbose)` function
- [x] 1.10 Implement normal mode logging (INFO level) in logger_config
- [x] 1.11 Implement verbose mode logging (DEBUG level) in logger_config

## 2. Refactor MagicCardProcessor

- [x] 2.1 Update `MagicCardProcessor.__init__` to accept `ProcessorConfig` parameter
- [x] 2.2 Replace class constants with instance attributes from config (batch_size, max_workers, api_delay, max_retries)
- [x] 2.3 Store dry_run flag from config
- [x] 2.4 Update ThreadPoolExecutor calls to use self.max_workers instead of hardcoded 4
- [x] 2.5 Update batch size references to use self.batch_size instead of BATCH_SIZE
- [x] 2.6 Update API delay references to use self.api_delay instead of API_RATE_LIMIT_DELAY
- [x] 2.7 Update max retries references to use self.max_retries instead of MAX_RETRIES
- [x] 2.8 Use ClientFactory to create spreadsheet_client based on config
- [x] 2.9 Add support for config.limit to process only N cards
- [x] 2.10 Add support for config.resume_from to skip initial rows

## 3. Refactor CardFetcher

- [x] 3.1 Update CardFetcher to accept max_retries parameter
- [x] 3.2 Update CardFetcher to accept retry_delay parameter
- [x] 3.3 Replace hardcoded MAX_RETRIES constant with instance attribute
- [x] 3.4 Replace hardcoded RETRY_DELAY constant with instance attribute

## 4. Refactor SpreadsheetClient

- [x] 4.1 Ensure SpreadsheetClient constructor accepts credentials_path parameter
- [x] 4.2 Ensure SpreadsheetClient constructor accepts spreadsheet_name parameter
- [x] 4.3 Ensure SpreadsheetClient constructor accepts worksheet_name parameter
- [x] 4.4 Verify existing parameter handling is compatible with config

## 5. Enhance main.py CLI

- [x] 5.1 Update argparse description to "DeckDex MTG - Magic card data processor"
- [x] 5.2 Set formatter_class to RawDescriptionHelpFormatter
- [x] 5.3 Add epilog with usage examples (basic, performance tuning, testing, resume, custom config)
- [x] 5.4 Keep existing --use_openai flag (backwards compatibility)
- [x] 5.5 Keep existing --update_prices flag (backwards compatibility)
- [x] 5.6 Add --dry-run flag (action=store_true)
- [x] 5.7 Add -v / --verbose flag (action=store_true)
- [x] 5.8 Add --batch-size argument (type=int, default=20)
- [x] 5.9 Add --workers argument (type=int, default=4)
- [x] 5.10 Add --api-delay argument (type=float, default=0.1)
- [x] 5.11 Add --max-retries argument (type=int, default=5)
- [x] 5.12 Add --credentials-path argument (type=str, optional)
- [x] 5.13 Add --sheet-name argument (type=str, default="magic")
- [x] 5.14 Add --worksheet-name argument (type=str, default="cards")
- [x] 5.15 Add --limit argument (type=int, optional)
- [x] 5.16 Add --resume-from argument (type=int, optional)
- [x] 5.17 Create ProcessorConfig from parsed arguments
- [x] 5.18 Handle config validation errors with clear error messages
- [x] 5.19 Call configure_logging(args.verbose) before processing
- [x] 5.20 Display dry-run banner if args.dry_run is True
- [x] 5.21 Create MagicCardProcessor with config instead of individual parameters
- [x] 5.22 Display dry-run summary after processing completes

## 6. Implement Dry-Run Display Logic

- [x] 6.1 Create dry-run banner function (display config summary)
- [x] 6.2 Create dry-run summary function (display statistics, sample output)
- [x] 6.3 Add sample row display (first 3-5 rows that would be written)
- [x] 6.4 Add estimated write time calculation
- [x] 6.5 Add instruction to run without --dry-run to execute for real

## 7. Delete Broken Code

- [x] 7.1 Delete run_cli.py file

## 8. Update Documentation

- [x] 8.1 Remove README.md lines 85-98 (Interactive Command Line Interface section)
- [x] 8.2 Remove README.md line 122 mention of interactive CLI
- [x] 8.3 Add CLI options table to README with all new arguments
- [x] 8.4 Add usage examples for common workflows (testing, performance tuning, custom sheets)
- [x] 8.5 Update "Running the Project" section with new options
- [x] 8.6 Add note about run_cli.py removal and migration path

## 9. Update Tests

- [x] 9.1 Rename tests/test_cli.py to tests/test_main.py
- [x] 9.2 Add test for ProcessorConfig creation with defaults
- [x] 9.3 Add test for ProcessorConfig creation with custom values
- [x] 9.4 Add test for ProcessorConfig validation (invalid batch_size)
- [x] 9.5 Add test for ProcessorConfig validation (invalid max_workers)
- [x] 9.6 Add test for ProcessorConfig validation (invalid api_delay)
- [x] 9.7 Add test for ProcessorConfig validation (invalid max_retries)
- [x] 9.8 Add test for ProcessorConfig validation (invalid limit)
- [x] 9.9 Add test for ProcessorConfig validation (invalid resume_from)
- [x] 9.10 Add test for ClientFactory returning SpreadsheetClient when dry_run=False
- [x] 9.11 Add test for ClientFactory returning DryRunClient when dry_run=True
- [x] 9.12 Add test for DryRunClient logging operations without executing
- [x] 9.13 Add test for MagicCardProcessor using config values
- [x] 9.14 Add test for backwards compatibility (no args still works)
- [x] 9.15 Add test for backwards compatibility (--use_openai still works)
- [x] 9.16 Add test for backwards compatibility (--update_prices still works)

## 10. Integration Testing

- [x] 10.1 Test `python main.py --help` displays all options
- [x] 10.2 Test `python main.py` with no args (backwards compatibility)
- [x] 10.3 Test `python main.py --use_openai` (backwards compatibility)
- [x] 10.4 Test `python main.py --update_prices` (backwards compatibility)
- [ ] 10.5 Test `python main.py --dry-run --limit 5` on real data
- [ ] 10.6 Test `python main.py --dry-run --verbose --limit 5` displays detailed logs
- [ ] 10.7 Test `python main.py --batch-size 50 --workers 8` applies config
- [ ] 10.8 Test `python main.py --sheet-name "test" --worksheet-name "cards"` connects to correct sheet
- [ ] 10.9 Test `python main.py --limit 10` processes only 10 cards
- [ ] 10.10 Test `python main.py --resume-from 50` skips first 49 rows
- [x] 10.11 Test `python main.py --batch-size 0` shows validation error
- [x] 10.12 Test `python main.py --workers 15` shows validation error
- [x] 10.13 Verify run_cli.py no longer exists
- [x] 10.14 Verify README no longer mentions interactive CLI
- [x] 10.15 Run full test suite with pytest or unittest

## 11. Verification

- [ ] 11.1 Verify no linter errors in new modules
- [ ] 11.2 Verify all type hints are correct
- [ ] 11.3 Verify dry-run mode makes no writes to Google Sheets
- [ ] 11.4 Verify verbose logging shows expected details
- [ ] 11.5 Verify normal logging is concise
- [x] 11.6 Verify default api_delay is 0.1s (not 0.05s)
- [x] 11.7 Verify all CLI options work as documented
- [x] 11.8 Verify backwards compatibility maintained
