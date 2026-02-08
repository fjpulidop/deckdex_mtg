## Why

The web dashboard has three critical bugs discovered during user testing that prevent accurate collection tracking and degrade user experience:

1. **Total Value calculation is incorrect** - Shows €2,888 instead of actual €3,294.74 from Google Sheets (~€407 missing). Price parsing fails for cards with values over €1,000 due to European number formatting with thousands separator (e.g., "1.234,56").

2. **Job tracking breaks on page refresh** - When users refresh the browser while background jobs (Process Cards, Update Prices) are running, the job disappears from the UI even though the backend is still processing. Users lose visibility into long-running operations.

3. **Stats UI is cluttered** - The "Last Updated" card displays non-persistent timestamps that reset on refresh, providing no real value. The useful average price metric is buried in the third card instead of being integrated with Total Value.

These bugs must be fixed before wider deployment to ensure data accuracy and reliable job monitoring.

## What Changes

- **Fix price parsing logic** to correctly handle European number format with thousands separator ("1.234,56" → 1234.56)
- **Restore active jobs on dashboard load** by fetching from backend's existing `/api/jobs` endpoint
- **Simplify stats card layout** from 3-column to 2-column grid, removing "Last Updated" and integrating average price as a subtitle under Total Value
- **Relocate active jobs panel** from floating bottom-right pills to a fixed bottom bar for better UX alignment with action buttons

## Capabilities

### New Capabilities
<!-- None - all changes are bug fixes to existing capabilities -->

### Modified Capabilities

- `web-dashboard-ui`: Update stats card layout (3→2 columns), remove "Last Updated", integrate average price display, restore jobs from backend on mount, reposition jobs panel to fixed bottom bar
- `web-api-backend`: Fix price parsing in stats calculation and collection caching to handle European format with thousands separators (mixed dot/comma formats)

## Impact

**Backend**:
- `backend/api/routes/stats.py` - Enhanced price parsing in `calculate_stats()` function
- `backend/api/dependencies.py` - Enhanced price parsing in `safe_float()` helper

**Frontend**:
- `frontend/src/components/StatsCards.tsx` - Layout change: 3→2 columns, remove date formatting, integrate average price
- `frontend/src/pages/Dashboard.tsx` - Add `useEffect` to restore jobs from `/api/jobs` on mount
- `frontend/src/components/ActiveJobs.tsx` - Repositioned from floating pills to fixed bottom bar

**Google Sheets**: No schema changes required. Issue is caused by Google Sheets auto-formatting prices with thousands separator which existing code doesn't handle.

**No breaking changes** - All API contracts remain unchanged. This is purely bug fixes to existing functionality.
