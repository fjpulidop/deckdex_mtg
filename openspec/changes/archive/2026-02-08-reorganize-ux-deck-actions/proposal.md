# Proposal: Reorganize UX — Deck Actions in Settings

## Why

The main dashboard currently gives prominent space to "Process Cards" and "Update Prices". These are important but operational actions that fit better under Settings, so the dashboard can focus on viewing and managing the collection. Moving them into a dedicated "Deck Actions" section in Settings reduces visual weight on the dashboard and keeps configuration and batch actions in one place. The active jobs bar should remain visible across the whole app (Dashboard and Settings) so users can start a job from Settings and still see progress without switching pages.

## What Changes

- **Dashboard**: Remove the "Actions" block (Process Cards, Update Prices) from the main dashboard. The dashboard will show header, stats, filters, and card table only.
- **Settings**: Add a new section **"Deck Actions"** at the end of the Settings page (after Scryfall credentials and Import from file). Same card style as existing Settings sections. Inside: Process Cards (with dropdown: new only / all) and Update Prices.
- **Active Jobs bar**: Show the same jobs bar (launched jobs, progress, cancel, log) on all app screens (Dashboard and Settings). State for active jobs is global (e.g. via context or app-level layout) so that jobs started from Settings appear in the bar and persist when navigating.
- **Padding / layout**: Reserve bottom space for the jobs bar on every screen that uses the app layout so the bar never covers content.

## Capabilities

### New Capabilities

- **global-jobs-ui**: The active jobs bar is rendered once at app/layout level and receives job state from a shared source (e.g. context). It is visible on Dashboard and Settings (and any future top-level views). Restore of running jobs from the API happens once on app load.

### Modified Capabilities

- **web-dashboard-ui**: Dashboard no longer shows the Actions block. Settings gains a "Deck Actions" section (last section, same card style as others) containing Process Cards and Update Prices. Requirements for where these actions live and where the jobs bar appears are updated accordingly.

## Impact

- **Frontend**: `App.tsx` or a new layout component will hold (or provide via context) active jobs state and render `ActiveJobs`. `Dashboard.tsx` loses `ActionButtons`, job state, and local `ActiveJobs`; it may consume job context only for padding. `Settings.tsx` gains a "Deck Actions" section reusing the same actions (e.g. `ActionButtons` or equivalent) and uses the shared job context to register new jobs. `ActionButtons` component can be reused in Settings with a section title "Deck Actions" and same styling as other Settings sections.
- **No backend or API changes**: Endpoints for process, price update, jobs, and WebSockets remain unchanged.
