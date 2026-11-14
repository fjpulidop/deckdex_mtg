# backend-docker-startup Specification

## Purpose
Ensure local backend Docker images migrate and serve a PostgreSQL-connected API with compatible installed dependencies, with reproducible evidence and verification isolated from existing user data.

## Requirements

### Requirement: Compatible fresh-image PostgreSQL startup
The backend SHALL complete database migrations and start the API from a freshly built image using the unchanged Compose `postgresql://` connection URL and the retained PostgreSQL driver, without requiring psycopg v3.

#### Scenario: Fresh backend image starts successfully
- **WHEN** dependencies are installed by a fresh uncached build and the backend starts through its shipped entrypoint against ready PostgreSQL
- **THEN** migrations SHALL complete without `ModuleNotFoundError` for psycopg
- **AND** the API process SHALL remain running
- **AND** repeated GET /api/health requests SHALL return HTTP 200 with `status` equal to `healthy` and `database` equal to `connected`

### Requirement: Reproducible dependency incompatibility evidence
The automated Docker check SHALL report actual installed database dependency versions and the selected dialect driver for the Compose URL, explain the import incompatibility, and distinguish diagnostic reproduction from successful final-image startup. Historical versions SHALL NOT be reported as measurements.

#### Scenario: Default-driver incompatibility is reproduced
- **WHEN** the incompatible dependency series is installed in a separate disposable diagnostic container with the retained driver and no psycopg v3
- **THEN** the check SHALL report the actual installed versions and selected driver
- **AND** SHALL confirm the exact missing psycopg module error from engine construction while the retained driver imports successfully
- **AND** SHALL keep this diagnostic container separate from the unchanged final-image startup check

#### Scenario: Compatible image reports its driver
- **WHEN** the freshly built image completes actual startup
- **THEN** the check SHALL report its installed database dependency versions and selected dialect driver
- **AND** SHALL confirm successful PostgreSQL connectivity with the retained driver

### Requirement: Data-preserving isolated startup verification
The Docker check SHALL leave existing PostgreSQL data and volumes untouched and require no `.env` or secret changes. It SHALL exercise repeated real startup against retained test data in its own isolated PostgreSQL instance.

#### Scenario: Existing data survives repeated startup
- **WHEN** a representative committed card exists in the isolated database and the backend is restarted through its normal entrypoint
- **THEN** migrations SHALL complete again and health SHALL return HTTP 200 with healthy/connected values
- **AND** the card identity and stored field values SHALL remain unchanged

#### Scenario: Verification coexists with an existing local installation
- **WHEN** the Docker check runs while existing project containers or PostgreSQL volumes are present
- **THEN** it SHALL use invocation-owned resources without mounting, changing or deleting existing data volumes
- **AND** SHALL not publish competing host ports, load or edit local secrets, or change `.env`
- **AND** cleanup SHALL affect only invocation-owned resources

### Requirement: Executable failure evidence
The Docker check SHALL produce machine-readable results and return nonzero on build, dependency, migration, startup, connectivity or data-preservation failure. Timeouts and unavailable environment dependencies SHALL be explicit failures rather than skipped success.

#### Scenario: Startup fails or never becomes ready
- **WHEN** migrations fail, the backend exits, readiness times out, or health lacks the required HTTP status or JSON values
- **THEN** the check SHALL fail with the failing stage and available owned-container logs
- **AND** SHALL clean up its own resources without hiding the original failure

#### Scenario: Docker or dependency retrieval is unavailable
- **WHEN** Docker cannot be reached or an image/package operation fails or exceeds its deadline
- **THEN** the check SHALL return nonzero and identify that environmental failure in its output
