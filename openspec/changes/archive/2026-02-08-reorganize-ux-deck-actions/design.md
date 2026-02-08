# Design: Reorganize UX — Deck Actions in Settings

## Context

The frontend is a React (Vite, TypeScript) SPA with two main routes: Dashboard (`/`) and Settings (`/settings`). The Dashboard currently holds: header, stats, an "Actions" block (ActionButtons: Process Cards with dropdown, Update Prices), filters, and card table. Active jobs state (`backgroundJobs`, restore from API on mount, `handleJobStarted` / `handleJobCompleted`) and the `ActiveJobs` bar component live only in `Dashboard.tsx`. Settings has Scryfall credentials and Import from file sections; it does not show actions or the jobs bar. `App.tsx` only defines routes with no shared layout or global state.

## Goals / Non-Goals

**Goals:**

- Move Process Cards and Update Prices from Dashboard to Settings under a "Deck Actions" section (last section, same card style as others).
- Make the active jobs bar visible on all app screens (Dashboard and Settings) with a single source of truth for job state.
- Restore running jobs from the API once on app load so they appear regardless of which page the user lands on.
- Reserve bottom padding for the jobs bar on every screen so it never covers content.

**Non-Goals:**

- Changing backend APIs, job types, or WebSocket behavior.
- Adding new job types or new Settings sections beyond Deck Actions.

## Decisions

### 1. Global job state via React Context

**Choice:** Introduce an `ActiveJobsContext` (or similar) that holds `jobs`, `addJob`, and `removeJob`. The provider runs job restore from the API once on mount and renders `ActiveJobs` in a single place (e.g. inside the provider, or in App after the provider).

**Rationale:** Keeps job state and restore logic in one place; any screen (Dashboard, Settings, future views) can trigger jobs via `addJob` without prop drilling. Alternative of lifting state into App and passing callbacks through routes would require a shared layout and passing props to every route—context is cleaner for this cross-cutting concern.

**Alternatives considered:** Layout component with local state and render-props (more verbose, same effect). Redux/Zustand (overkill for this single slice).

### 2. Where to render ActiveJobs and apply bottom padding

**Choice:** Render `ActiveJobs` once inside the same tree that provides the job context (e.g. the context provider wraps the router, and the provider’s children are the Routes; we add a wrapper that includes Routes + ActiveJobs, or render ActiveJobs inside the provider and use a layout that includes it). Bottom padding for the bar is computed from `jobs.length` and applied by a small layout wrapper (or a hook that returns the padding and is used by Dashboard and Settings) so both pages get the same reserved space.

**Rationale:** One bar instance, one place that knows bar height. Padding can live in a wrapper that reads context and applies `paddingBottom` to the main content area, or each page uses a hook like `useJobsBarPadding()` and applies it—either is fine; prefer a single layout wrapper that wraps route content so we don’t forget new pages.

**Alternatives considered:** Rendering ActiveJobs in each page (duplicated DOM and logic—rejected). Applying padding only on Dashboard (would leave Settings content covered when jobs run—rejected).

### 3. Reuse ActionButtons in Settings

**Choice:** Reuse the existing `ActionButtons` component in Settings. It accepts `onJobStarted`; in Settings we pass the context’s `addJob`. The section title "Deck Actions" is the section heading in Settings (same pattern as "Scryfall API credentials" and "Import from file"); the card can wrap ActionButtons so the visual style matches other Settings sections (same `section` + card classes).

**Rationale:** No duplication of process/price-update logic or UI. Section title and placement (last section) are decided in Settings layout, not inside ActionButtons.

**Alternatives considered:** Copying the buttons into a Settings-only component (rejected—duplication). Making ActionButtons accept an optional `title` prop (optional refinement; not required if the section heading is enough).

### 4. No new route or layout file required

**Choice:** Implement using existing `App.tsx` and existing page components. Add the context provider in `App.tsx` wrapping `BrowserRouter` (or wrap `Routes` so the provider is inside the router). Render `ActiveJobs` and the padding wrapper as part of that structure (e.g. a fragment or a thin layout component that renders `{children}` plus `ActiveJobs`, and uses context to compute padding on the container).

**Rationale:** Change is contained to frontend; no new route. A single `AppLayout` or inline structure in App is enough.

**Alternatives considered:** A separate `Layout.tsx` that wraps all routes (acceptable if it keeps App.tsx simpler; not strictly required).

## Risks / Trade-offs

- **Context re-renders:** Any consumer of the jobs context re-renders when jobs change. Mitigation: only Dashboard and Settings (and the bar) consume it; job list is small; acceptable.
- **Restore on every mount:** If the provider remounts, we restore jobs again. Mitigation: provider is at app root and does not remount on navigation.
- **Padding and narrow viewports:** Fixed bar height calculation (e.g. 24 + jobs.length * 72) may need tuning for very small screens. Mitigation: keep current formula; adjust later if UX demands.
