## Context

Three bugs discovered during testing of the web dashboard MVP:

1. **Price parsing bug**: Google Sheets auto-formats prices >€1,000 with thousands separator (e.g., "1.234,56"). Current parser does naive `replace(',', '.')` → "1.234.56" → `float()` error → card excluded from total.

2. **Job persistence bug**: Background jobs stored only in React state. Page refresh → state lost → jobs invisible despite backend still processing. Backend already has `/api/jobs` endpoint that persists in-memory, but frontend doesn't call it on mount.

3. **UI clutter**: 3-column stats grid with "Last Updated" card showing non-persistent timestamps (resets on refresh). Average price buried as small text in third card instead of integrated with Total Value.

Current codebase:
- Backend: FastAPI with in-memory job tracking (`_active_jobs`, `_job_results` dicts)
- Frontend: React + TanStack Query + Tailwind v4
- Price parsing: Simple `str.replace(',', '.')` in `stats.py` and `dependencies.py`
- Job tracking: `ActiveJobs` component renders floating pills (`fixed bottom-4 right-4`)

## Goals / Non-Goals

**Goals:**
- Fix price calculation accuracy for European format with thousands separators
- Restore job visibility after page refresh without requiring backend changes
- Simplify stats UI to 2-column layout with integrated average price
- Reposition jobs panel to fixed bottom bar for better visual flow

**Non-Goals:**
- Persistent job storage beyond backend restart (in-memory is acceptable for MVP)
- Historical price tracking or last modified timestamp from Drive API (removed from scope)
- Changes to job cancellation, WebSocket progress, or modal behavior (working correctly)
- Support for other number formats beyond European/US conventions

## Decisions

### Decision 1: Smart price parser that detects format by last separator

**Chosen approach**: Detect format by finding last occurrence of comma vs dot. If comma comes last (European), remove dots and replace comma with dot. If dot comes last (US), remove commas. If only one separator, assume European decimal.

**Rationale**:
- Handles all observed formats: "1.234,56", "1234,56", "1,234.56", "123.45"
- Single function can be reused in `stats.py` and `dependencies.py`
- No regex needed, simple string operations
- Fails gracefully: unparseable values logged and skipped

**Alternatives considered**:
- **Locale-based parsing**: Requires knowing Google Sheets locale setting. Too brittle if user changes regional settings.
- **Try multiple parsers**: Try US format, catch error, try European format. More expensive (exceptions) and harder to debug.
- **Regex extraction**: Overkill for this problem, harder to maintain.

### Decision 2: Restore jobs via useEffect on Dashboard mount

**Chosen approach**: Add `useEffect(() => { api.getJobs().then(restoreJobs); }, [])` to Dashboard component. Map backend response to `backgroundJobs` state format.

**Rationale**:
- Minimal change to existing code (one useEffect hook)
- Reuses existing `/api/jobs` endpoint (no backend changes)
- Compatible with existing job tracking flow (modal open/close, minimize, polling)
- Jobs restored with original `start_time` from backend

**Alternatives considered**:
- **LocalStorage persistence**: Could store jobs in browser storage, but doesn't help if backend restarts. Backend is source of truth.
- **URL query params**: Could encode active job_id in URL. Complex to sync with multiple jobs, breaks on copy/paste.

### Decision 3: 2-column grid with average price as subtitle in Total Value card

**Chosen approach**: Change `grid-cols-3` to `grid-cols-2`, remove third card entirely, add average price as `<div className="text-sm text-gray-500 mt-2">` below Total Value amount.

**Rationale**:
- Cleaner visual hierarchy: left card = count, right card = money (with breakdown)
- Average price more discoverable (no longer in third card)
- Responsive layout simpler (2 columns easier to stack on mobile than 3)
- Removes "Last Updated" which was misleading (showed cache time, not Sheet modification time)

**Alternatives considered**:
- **Tooltip on hover**: Hide average price behind interaction. Less discoverable, fails on mobile.
- **Fetch real lastUpdateTime from Drive API**: Adds API call overhead, consumes Drive quota, only shows Sheet modification (not price update time).

### Decision 4: Fixed bottom bar instead of floating pills

**Chosen approach**: Replace `fixed bottom-4 right-4` with `fixed bottom-0 left-0 right-0`, full-width bar with white background and top border shadow. Stack jobs vertically.

**Rationale**:
- Visual alignment: action buttons at top, jobs panel at bottom bracket the main content
- More space for job info (full width vs constrained pill)
- Better mobile UX (floating pills can obscure content, bottom bar is standard pattern)
- Easier to scan multiple jobs (vertical stack vs horizontal overflow)

**Alternatives considered**:
- **Top notification bar**: Would push content down, bad UX when jobs are long-running.
- **Sidebar panel**: Too heavy for what's essentially a status indicator. Would require layout restructure.

## Risks / Trade-offs

**Risk**: Price parser might fail on exotic formats (e.g., Indian lakhs "1,23,456.78")
→ **Mitigation**: Log unparseable values, exclude from total, continue processing. Users can report if critical cards are missing.

**Risk**: Job restoration on mount adds slight delay to dashboard load
→ **Mitigation**: Request runs in parallel with stats/cards fetch (TanStack Query). Non-blocking. If it fails, dashboard still loads.

**Trade-off**: Fixed bottom bar takes vertical space even when collapsed
→ **Accepted**: Only shown when jobs exist. Auto-removes after 5s of completion. Most users won't have long-running jobs frequently.

**Trade-off**: Removing "Last Updated" loses any temporal information
→ **Accepted**: Timestamp was misleading (showed cache time). Users can see job history in bottom bar for recent operations. If needed later, can add Drive API integration.

## Migration Plan

**Deployment steps**:
1. Deploy backend changes first (price parser is backward compatible, just fixes bugs)
2. Deploy frontend changes (useEffect and UI updates are additive, no breaking changes)
3. Test with fresh page load while jobs are running to verify restoration

**Rollback strategy**:
- Backend: Revert `stats.py` and `dependencies.py` changes. Old parser will still work for prices <€1,000.
- Frontend: Revert component changes. Old UI will render, jobs won't restore on refresh (existing bug returns).

**No data migration needed**: All changes are in presentation/parsing logic, no schema or API contract changes.

## Open Questions

None. All technical decisions resolved during exploration phase.
