# Global Jobs UI

App-level job visibility: one fixed bottom bar on all main views (Dashboard, Settings). Restore once on app load.

### Requirements (compact)

- **Restore:** On app (or global provider) mount, GET /api/jobs once; populate global list with active/pending jobs. Not route-specific; runs regardless of initial route. On API error: log, continue without blocking.
- **Bar:** Single bar at app level when jobs exist; list jobs vertically; open modal per job; auto-remove completed after ~5s; cancelled → orange + "Cancelled". Progress via WebSocket or GET /api/jobs/{id}. Same bar across navigation.
- **Layout:** Main content on all views reserves bottom space so bar doesn’t overlap (Dashboard table/pagination, Settings sections fully visible).
