## 1. Global jobs context and app layout

- [x] 1.1 Create ActiveJobsContext with state (jobs list), addJob(jobId, jobType), removeJob(jobId), and provider component
- [x] 1.2 In provider: on mount call GET /api/jobs, filter running/pending, populate state; on error log and continue
- [x] 1.3 Render ActiveJobs once inside provider (or app layout) reading jobs and removeJob from context
- [x] 1.4 Add layout wrapper that applies bottom padding (e.g. 24 + jobs.length * 72) to main content when jobs exist, so bar does not cover content on any route
- [x] 1.5 In App.tsx wrap Routes with ActiveJobsProvider and use layout that includes Routes + padding wrapper + ActiveJobs

## 2. Dashboard: remove actions and local job state

- [x] 2.1 Remove ActionButtons from Dashboard
- [x] 2.2 Remove backgroundJobs state, handleJobStarted, handleJobCompleted, and restore-jobs useEffect from Dashboard
- [x] 2.3 Ensure Dashboard content is inside the layout that receives bottom padding (or Dashboard uses padding from context) so table and pagination are not covered when jobs bar is visible

## 3. Settings: add Deck Actions section

- [x] 3.1 Add "Deck Actions" section at the end of Settings page (after Import from file), same card style as existing sections
- [x] 3.2 Inside section render ActionButtons with onJobStarted wired to context addJob
- [x] 3.3 Ensure Settings main content is inside the layout that receives bottom padding when jobs bar is visible

## 4. Verification

- [x] 4.1 Verify jobs bar appears on Dashboard and Settings when at least one job is active; single bar instance when navigating
- [x] 4.2 Verify starting Process Cards or Update Prices from Settings adds job to bar and bar remains visible on both routes
- [x] 4.3 Verify bottom padding prevents bar from covering table (Dashboard) and Settings sections (Settings)
