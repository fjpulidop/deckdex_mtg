## 1. Backend: Fix Price Parsing

- [x] 1.1 Create smart price parser function in `backend/api/routes/stats.py` that detects format by last separator position
- [x] 1.2 Update `calculate_stats()` to use new parser for European/US formats with thousands separators
- [x] 1.3 Update `safe_float()` in `backend/api/dependencies.py` to use same parsing logic
- [x] 1.4 Test parser with example prices: "1.234,56", "1234,56", "1,234.56", "123.45", "N/A"

## 2. Frontend: Simplify Stats UI

- [x] 2.1 Change `StatsCards.tsx` grid from `grid-cols-3` to `grid-cols-2`
- [x] 2.2 Remove third "Last Updated" card and `formatDate()` function
- [x] 2.3 Add average price as subtitle under Total Value (format: `text-sm text-gray-500 mt-2`)
- [x] 2.4 Verify responsive layout works correctly with 2 columns

## 3. Frontend: Restore Jobs on Dashboard Load

- [x] 3.1 Add `useEffect` hook in `Dashboard.tsx` that calls `api.getJobs()` on component mount
- [x] 3.2 Map backend response to `backgroundJobs` state format (job_id → jobId, job_type → type, start_time → startedAt)
- [x] 3.3 Handle empty response and API errors gracefully (log but don't block dashboard load)
- [x] 3.4 Test job restoration by starting a job, refreshing page, and verifying job reappears

## 4. Frontend: Reposition Jobs Panel to Fixed Bottom Bar

- [x] 4.1 Change `ActiveJobs.tsx` container from `fixed bottom-4 right-4` to `fixed bottom-0 left-0 right-0`
- [x] 4.2 Add white background, top border shadow, and full-width styling
- [x] 4.3 Update job entry layout to stack vertically instead of floating pills
- [x] 4.4 Ensure bottom bar only renders when `jobs.length > 0` (conditional rendering)
- [x] 4.5 Test with multiple jobs running simultaneously to verify vertical stacking

## 5. Additional Bug Fixes (discovered during implementation)

- [x] 5.1 Fix job restoration filtering to exclude completed/cancelled jobs
- [x] 5.2 Add `_cleanup_old_jobs()` call in `/api/process` endpoint to prevent blocking after cancellation

## 6. UX Enhancement: Unified Bottom Bar

- [x] 6.1 Completely rewrite `ActiveJobs.tsx` to integrate all ProcessModal functionality
- [x] 6.2 Add WebSocket connection status indicator to each job
- [x] 6.3 Add integrated Stop button with "Stopping..." state
- [x] 6.4 Add expandable/collapsible errors section with "Show errors" button
- [x] 6.5 Add live timer with adaptive format (s/m/h)
- [x] 6.6 Remove ProcessModal component and all modal-related logic from Dashboard
- [x] 6.7 Delete unused `ProcessModal.tsx` file

## 7. Testing and Verification

- [x] 7.1 Test price calculation with Google Sheets data containing prices >€1,000
- [x] 7.2 Verify Total Value matches Google Sheets SUM formula
- [x] 7.3 Test job restoration: start job, refresh page, verify job visible and progress updates
- [x] 7.4 Test UI layout on desktop and mobile to verify 2-column stats and bottom bar responsiveness
- [x] 7.5 Verify WebSocket progress updates work in unified bottom bar
- [x] 7.6 Test job cancellation and immediate re-launch
- [x] 7.7 Test errors display with Show/Hide toggle
