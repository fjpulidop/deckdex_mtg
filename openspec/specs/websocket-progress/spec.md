## ADDED Requirements

### Requirement: WebSocket SHALL provide real-time progress updates

The system SHALL establish WebSocket connection for bidirectional communication of process progress.

#### Scenario: Client connects to WebSocket endpoint
- **WHEN** client sends WebSocket connection request to `/ws/progress/{job_id}`
- **THEN** system accepts connection and sends initial acknowledgment message

#### Scenario: Connection requires valid job ID
- **WHEN** client attempts connection with non-existent job_id
- **THEN** system rejects connection with close code 4004 and reason "Job not found"

#### Scenario: Multiple clients can connect to same job
- **WHEN** multiple browser tabs connect to same job_id
- **THEN** system broadcasts progress events to all connected clients

### Requirement: WebSocket SHALL emit progress events

The system SHALL send structured JSON events to connected clients as process progresses.

#### Scenario: Send progress event after each batch
- **WHEN** processor completes a batch of cards
- **THEN** system sends message `{"type": "progress", "current": 50, "total": 200, "percentage": 25, "batch_size": 10}`

#### Scenario: Progress events include timing information
- **WHEN** sending progress event
- **THEN** message includes "elapsed_seconds" and "estimated_remaining_seconds" fields

### Requirement: WebSocket SHALL emit error events

The system SHALL notify clients when individual card processing fails.

#### Scenario: Send error event for card not found
- **WHEN** processor fails to find card in Scryfall
- **THEN** system sends message `{"type": "error", "card_name": "Invalid Card", "error_type": "not_found", "message": "Card not found in Scryfall"}`

#### Scenario: Error events do not terminate connection
- **WHEN** error event is sent
- **THEN** WebSocket connection remains open and processing continues

#### Scenario: Limit error events to prevent flooding
- **WHEN** more than 100 errors occur
- **THEN** system sends summary message instead of individual error events

### Requirement: WebSocket SHALL emit completion event

The system SHALL send final summary when process completes.

#### Scenario: Send complete event on successful finish
- **WHEN** processor finishes all cards without interruption
- **THEN** system sends message `{"type": "complete", "status": "success", "total_processed": 200, "success_count": 195, "error_count": 5, "duration_seconds": 45}`

#### Scenario: Send complete event on cancellation
- **WHEN** user cancels process
- **THEN** system sends message with `"status": "cancelled"` and partial results

#### Scenario: Connection closes after completion event
- **WHEN** complete event is sent
- **THEN** system closes WebSocket connection with code 1000 (normal closure)

### Requirement: WebSocket SHALL handle connection lifecycle

The system SHALL manage connection states and cleanup appropriately.

#### Scenario: Client disconnects mid-process
- **WHEN** client closes WebSocket connection while process is active
- **THEN** system continues processing in background (process not cancelled)

#### Scenario: Server closes connection on backend error
- **WHEN** backend encounters unhandled exception during processing
- **THEN** system sends error event, then closes connection with code 1011 (internal error)

#### Scenario: Heartbeat to detect stale connections
- **WHEN** no events sent for 30 seconds
- **THEN** system sends ping frame to verify connection is alive

#### Scenario: Cleanup job state after connection closes
- **WHEN** all clients disconnect and job is complete
- **THEN** system removes job from in-memory state after 5 minutes

### Requirement: WebSocket SHALL send current progress on reconnect

The system SHALL send the current progress snapshot when a client (re)connects to a running job, so clients that disconnect and reconnect do not see stale/zero progress.

#### Scenario: Send current progress on connect for running job
- **WHEN** client connects to WebSocket for a job that is already `running` and has progress > 0
- **THEN** system reads `progress_data` from the active `ProcessorService` instance
- **AND** immediately sends a `progress` event with current/total/percentage after the `connected` ack

#### Scenario: Send complete event on connect for finished job
- **WHEN** client connects to WebSocket for a job that is already `complete` or `error`
- **THEN** system immediately sends a `complete` event with the job result from `_job_results`

#### Scenario: Include job_status in connected message
- **WHEN** client receives the initial `connected` acknowledgment
- **THEN** message includes `job_status` field (e.g., 'running', 'complete', 'cancelled', 'error')

#### Scenario: No extra progress event for new jobs
- **WHEN** client connects to a job that just started (progress total is 0)
- **THEN** system only sends the `connected` ack, no extra progress event

### Requirement: WebSocket SHALL integrate with ProcessorService

The system SHALL receive callbacks from ProcessorService wrapper to emit events.

#### Scenario: ProcessorService calls progress callback
- **WHEN** processor completes a batch
- **THEN** ProcessorService invokes callback with progress data, and WebSocket broadcasts to connected clients

#### Scenario: Callback is async-safe
- **WHEN** callback is invoked from processor thread
- **THEN** system safely queues event for WebSocket async loop without blocking processor

### Requirement: WebSocket SHALL handle concurrent processes gracefully

The system SHALL support multiple independent processes with separate WebSocket connections.

#### Scenario: Multiple jobs can run simultaneously
- **WHEN** two different job_ids are active
- **THEN** each WebSocket connection receives only events for its job_id

#### Scenario: Job state isolated per job_id
- **WHEN** querying job status
- **THEN** system returns state specific to requested job_id without interference

### Requirement: WebSocket SHALL serialize events as JSON

The system SHALL format all messages as valid JSON for parsing by client.

#### Scenario: All events have type field
- **WHEN** any event is sent
- **THEN** message contains top-level "type" field with value "progress", "error", or "complete"

#### Scenario: Timestamp included in all events
- **WHEN** any event is sent
- **THEN** message includes "timestamp" field with ISO 8601 format (e.g., "2024-02-07T14:30:00Z")

#### Scenario: Numbers represented as JSON numbers not strings
- **WHEN** sending counts or percentages
- **THEN** system uses JSON number types (e.g., `"percentage": 25.5`, not `"percentage": "25.5"`)

### Requirement: WebSocket SHALL log connection events

The system SHALL log WebSocket lifecycle for debugging and monitoring.

#### Scenario: Log connection establishment
- **WHEN** client connects
- **THEN** system logs "WebSocket connected: job_id={id}" at INFO level

#### Scenario: Log disconnection with reason
- **WHEN** client disconnects
- **THEN** system logs "WebSocket disconnected: job_id={id}, code={code}, reason={reason}" at INFO level

#### Scenario: Log errors at ERROR level
- **WHEN** WebSocket exception occurs
- **THEN** system logs full traceback with context (job_id, connection state)
