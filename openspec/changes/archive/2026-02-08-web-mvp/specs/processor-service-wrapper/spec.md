## ADDED Requirements

### Requirement: Wrapper SHALL encapsulate MagicCardProcessor for API usage

The system SHALL provide a `ProcessorService` class that wraps existing `MagicCardProcessor` to enable async callbacks without modifying core logic.

#### Scenario: Initialize wrapper with configuration
- **WHEN** ProcessorService is instantiated
- **THEN** it creates internal `MagicCardProcessor` instance using provided `ProcessorConfig`

#### Scenario: Initialize wrapper with progress callback
- **WHEN** ProcessorService is instantiated with optional `progress_callback` parameter
- **THEN** it stores callback for invocation during processing

#### Scenario: Wrapper does not modify processor behavior
- **WHEN** ProcessorService processes cards
- **THEN** it delegates to `MagicCardProcessor.process_cards()` without altering logic flow

### Requirement: Wrapper SHALL provide async process execution method

The system SHALL expose an async method for processing cards from API context.

#### Scenario: Execute card processing asynchronously
- **WHEN** caller invokes `process_cards_async()` method
- **THEN** system runs processor in thread pool executor and returns awaitable

#### Scenario: Pass configuration to processor
- **WHEN** executing process with custom config parameters
- **THEN** ProcessorService creates processor with those parameters (batch_size, workers, etc.)

### Requirement: Wrapper SHALL emit progress callbacks

The system SHALL invoke progress callback at key points during processing.

#### Scenario: Callback after each batch completion
- **WHEN** processor completes processing a batch of cards
- **THEN** system invokes callback with `{"type": "progress", "current": n, "total": total, "batch_size": size}`

#### Scenario: Callback on card error
- **WHEN** processor encounters card not found or API error
- **THEN** system invokes callback with `{"type": "error", "card_name": name, "error_message": msg}`

#### Scenario: Callback on process completion
- **WHEN** processor finishes all cards
- **THEN** system invokes callback with `{"type": "complete", "summary": {...}}`

#### Scenario: Callback is optional
- **WHEN** ProcessorService instantiated without callback
- **THEN** it processes normally without attempting to invoke callback

### Requirement: Wrapper SHALL intercept processor progress via tqdm capture

The system SHALL intercept tqdm output to extract real-time progress without modifying core processor code.

#### Scenario: Intercept stderr/stdout for tqdm output
- **WHEN** processor runs (uses tqdm which writes to stderr)
- **THEN** wrapper temporarily replaces sys.stderr and sys.stdout with `ProgressCapture` instances
- **AND** restores original streams in a finally block to prevent corruption

#### Scenario: Extract progress from tqdm output
- **WHEN** ProgressCapture receives text matching tqdm pattern (e.g., "45%|███| 450/1000")
- **THEN** it extracts percentage, current, and total using regex
- **AND** invokes the progress callback with extracted values

#### Scenario: Cross-thread progress emission
- **WHEN** progress is captured in the processor thread (ThreadPoolExecutor)
- **THEN** wrapper uses `asyncio.run_coroutine_threadsafe` to schedule async callback on the event loop

#### Scenario: Capture error count increments
- **WHEN** processor increments `error_count` attribute
- **THEN** wrapper captures error count in the final result summary

### Requirement: Wrapper SHALL support both process types

The system SHALL handle both card processing and price update operations.

#### Scenario: Execute price update operation
- **WHEN** caller invokes `update_prices_async()` method
- **THEN** system delegates to `processor.update_prices_data()` with progress tracking

#### Scenario: Execute card processing operation
- **WHEN** caller invokes `process_cards_async()` method
- **THEN** system delegates to `processor.process_cards()` with progress tracking

### Requirement: Wrapper SHALL handle cancellation via stream injection

The system SHALL allow graceful cancellation of long-running processes by raising an exception inside the processor's own thread via the intercepted output streams.

#### Scenario: Cancel flag propagated to ProgressCapture
- **WHEN** `cancel_async()` is invoked on ProcessorService
- **THEN** system sets `_cancel_flag` (threading.Event)
- **AND** `ProgressCapture` instances receive reference to this event at construction time

#### Scenario: ProgressCapture raises exception on cancelled write
- **WHEN** `ProgressCapture.write()` is called and `cancel_event` is set
- **THEN** system raises `JobCancelledException` (custom exception)
- **AND** exception propagates up through `tqdm.update()` → processor loop → `run_processor()`/`run_update()`

#### Scenario: ProgressCapture raises exception on cancelled flush
- **WHEN** `ProgressCapture.flush()` is called and `cancel_event` is set
- **THEN** system raises `JobCancelledException`

#### Scenario: Processor thread catches cancellation cleanly
- **WHEN** `JobCancelledException` is raised inside the processor thread
- **THEN** `run_processor()`/`run_update()` catches it and returns `{'status': 'cancelled', ...}`
- **AND** original stderr/stdout are restored in the finally block

#### Scenario: cancel_async emits WebSocket complete event
- **WHEN** `cancel_async()` is invoked
- **THEN** system sets cancel flag, updates status to 'cancelled', and emits `{"type": "complete", "status": "cancelled", "summary": {...}}` via progress callback

#### Scenario: No duplicate complete events after cancellation
- **WHEN** processor thread finishes after cancel_async already emitted complete event
- **THEN** `process_cards_async()`/`update_prices_async()` checks cancel flag and skips emitting a second complete event

#### Scenario: Progress events suppressed after cancellation
- **WHEN** `_on_tqdm_progress()` is called after cancel flag is set
- **THEN** system returns immediately without emitting progress events

#### Scenario: Sync cancel method available
- **WHEN** caller invokes `cancel()` (sync version)
- **THEN** system sets cancel flag and status to 'cancelled' without emitting WebSocket events

### Requirement: Wrapper SHALL provide thread-safe state access

The system SHALL protect shared state between processor thread and callback invocations.

#### Scenario: Thread-safe progress updates
- **WHEN** processor thread updates progress state
- **THEN** system uses lock to prevent race conditions with callback reads

#### Scenario: Thread-safe error list access
- **WHEN** errors are captured from processor
- **THEN** system safely appends to error list without data corruption

### Requirement: Wrapper SHALL reuse existing error handling

The system SHALL preserve processor's error handling behavior and retry logic.

#### Scenario: Processor retries are preserved
- **WHEN** Scryfall API returns transient error
- **THEN** processor's existing retry logic executes without wrapper interference

#### Scenario: Error CSV generation still works
- **WHEN** process completes with errors
- **THEN** processor generates error CSV file in `output/` directory as usual

### Requirement: Wrapper SHALL respect dry-run mode

The system SHALL honor dry-run configuration without modifying behavior.

#### Scenario: Dry-run flag passed to processor
- **WHEN** ProcessorService initialized with `dry_run=True` in config
- **THEN** processor executes in dry-run mode (no writes to Google Sheets)

#### Scenario: Dry-run indicated in callbacks
- **WHEN** operating in dry-run mode
- **THEN** callback events include `"dry_run": true` field

### Requirement: Wrapper SHALL provide job metadata

The system SHALL expose metadata about the current processing job.

#### Scenario: Get job start time
- **WHEN** process is running
- **THEN** wrapper provides `start_time` timestamp

#### Scenario: Get job configuration
- **WHEN** querying job state
- **THEN** wrapper provides copy of `ProcessorConfig` used for job

#### Scenario: Get job ID
- **WHEN** process starts
- **THEN** wrapper generates and stores UUID job_id for tracking

### Requirement: Wrapper SHALL handle processor exceptions

The system SHALL catch and report processor exceptions gracefully.

#### Scenario: Processor raises exception
- **WHEN** unhandled exception occurs in processor
- **THEN** wrapper catches exception, invokes callback with error event, and re-raises

#### Scenario: Callback invocation failure
- **WHEN** progress callback raises exception
- **THEN** wrapper logs error and continues processing without crashing

### Requirement: Wrapper SHALL be testable independently

The system SHALL allow testing without real processor or API calls.

#### Scenario: Mock processor for testing
- **WHEN** testing ProcessorService
- **THEN** tests can inject mock MagicCardProcessor instance

#### Scenario: Verify callback invocations
- **WHEN** testing with mock callback
- **THEN** tests can assert callback was invoked with expected arguments

#### Scenario: Test without network dependencies
- **WHEN** running unit tests
- **THEN** ProcessorService can be tested using mocked SpreadsheetClient and CardFetcher
