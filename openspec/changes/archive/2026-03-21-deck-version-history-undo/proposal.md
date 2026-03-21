## Why

Commander players iterate on decks constantly — swapping cards to tune a strategy, pivoting after a bad night, experimenting with a new combo. There is currently no way to recover from a bad edit. Once a card is removed from a deck, or a batch import overwrites an existing configuration, that state is gone. This is a High-severity pain point: users lose deck configurations, which undermines trust in the tool and discourages experimentation.

The feature solves this by persisting a full snapshot of the deck's card state on every save mutation. A timeline UI lets users see what changed and revert to any prior state with a single click — comparable to how Moxfield handles version history and how git handles project history.

## What Changes

- New `deck_snapshots` PostgreSQL table storing a JSONB snapshot of the full deck card state after each mutating operation (add card, remove card, set commander, batch add, deck import)
- Two new API endpoints: `GET /api/decks/{id}/history` (paginated list of snapshots with computed diffs) and `POST /api/decks/{id}/revert/{snapshot_id}` (restore deck to snapshot state)
- New snapshot creation is triggered inside `DeckRepository` mutations — it is transparent to route handlers
- Frontend: a "History" button in `DeckDetailModal` opens a `DeckHistoryModal` showing a `DeckHistoryTimeline` with per-snapshot `SnapshotDiff` rows and a `RevertButton`
- `api/client.ts` gains two new typed functions: `getDeckHistory` and `revertDeck`
- i18n keys added to `en.json` and `es.json`

## Non-goals

- No real-time sync of snapshots across browser tabs (existing TanStack Query invalidation handles this)
- No branching/forking (linear history only)
- No snapshot pruning or retention limits in v1 (left for a future housekeeping task)
- No export of diff as text
- Google Sheets mode: not applicable — decks require Postgres already; no new constraint added

## User Story

As a **Commander player**, I want to **see all changes made to a deck over time and revert to previous versions** so that **I never lose a deck config and can experiment fearlessly**.

## Acceptance Criteria

1. Every card mutation on a deck (add, remove, batch add, set commander, import) persists a snapshot row in `deck_snapshots` before or after the mutation
2. `GET /api/decks/{id}/history` returns a list of snapshots ordered newest-first, each with: `id`, `created_at`, `change_summary` (human-readable string), and a `diff` object (cards added, removed, quantity changed)
3. `POST /api/decks/{id}/revert/{snapshot_id}` replaces all `deck_cards` rows for the deck with the cards from the snapshot and creates a new snapshot recording the revert
4. The frontend shows a "History" button in the `DeckDetailModal` header bar
5. Clicking "History" opens a timeline modal; each row shows timestamp, change summary, and a "Revert to this version" button
6. Clicking "Revert" on a snapshot calls the revert endpoint, closes the history modal, and refreshes the deck detail view
7. The migration runs idempotently via `CREATE TABLE IF NOT EXISTS`
8. All new API endpoints require authentication via `get_current_user_id`
9. Endpoints return 501 when Postgres is not configured (consistent with existing deck endpoints)
10. Endpoints return 404 when the deck does not exist or does not belong to the authenticated user
11. All user-facing strings are i18n-keyed in both `en.json` and `es.json`

## Capabilities

### New Capabilities

- `deck-version-history-undo`: Full capability spec for deck snapshot persistence, history retrieval, diff computation, and revert.

### Modified Capabilities

- `decks`: Snapshot creation is wired into existing mutation operations; no route-level changes to existing endpoints, but repository now emits snapshots as a side effect.
