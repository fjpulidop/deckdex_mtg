# Session: Parallel Sprint #2 — i18n, a11y, WebSocket

**Date:** 2026-03-07
**Branch:** `feat/i18n-a11y-websocket-polish`
**PR:** https://github.com/fjpulidop/deckdex_mtg/pull/60
**CI:** Both backend and frontend jobs passed on first push

---

## What was done

Three features implemented in parallel using the `/parallel-implement` pipeline:

### 1. i18n Complete Coverage Sweep
- **Change:** `i18n-complete-coverage`
- **Scope:** 12 hardcoded English strings replaced with `t()` calls across 8 files
- **Key decision:** ErrorBoundary (class component) can't use hooks — extracted functional `ErrorFallback` component in a separate file to satisfy `react-refresh/only-export-components` ESLint rule
- **Files:** ErrorBoundary.tsx, ErrorFallback.tsx (new), 3 insight renderers, Admin.tsx, Settings.tsx, DeckImportModal.tsx, SettingsModal.tsx, en.json, es.json
- **13 new i18n keys** across namespaces: `insights.list.*`, `insights.timeline.*`, `insights.comparison.*`, `errorBoundary.*`, `admin.*`, `deckImport.*`, `settings.errors.*`

### 2. Accessibility Pass on Modals & Tables
- **Change:** `a11y-modals-tables-pass`
- **Scope:** 6 accessibility gaps fixed in 5 components
- **Key decisions:**
  - Image lightboxes in CardDetailModal and DeckDetailModal replaced raw `<div role="button">` with `<AccessibleModal>` — proper focus trap, ESC, dialog semantics
  - ProfileModal crop sub-modal: capture-phase ESC handler to prevent double-close with outer modal
  - DeckCardPickerModal: `aria-label` wired to existing i18n key
  - DeckImportModal: visible `<label>` for textarea
  - SettingsModal: sr-only `<label>` elements for file inputs
- **Files:** CardDetailModal.tsx, DeckDetailModal.tsx, DeckCardPickerModal.tsx, ProfileModal.tsx, DeckImportModal.tsx, SettingsModal.tsx, a11y-modals.test.tsx (new, 10 tests)

### 3. WebSocket Reconnection Polish
- **Change:** `websocket-reconnection-polish`
- **Scope:** Bug fix + new reactive state + test coverage
- **Bug found:** `fetchRestState()` was called at the top of `connect()`, firing on initial connection AND every retry. Server already delivers progress in the `connected` ack, causing redundant REST calls and state flicker
- **Fix:** Added `hasConnectedOnce` flag — REST fallback only fires on reconnect (after a successful re-open following a drop)
- **New:** `retryAttempt` reactive state in hook return value for UI feedback
- **Files:** useApi.ts, useWebSocket.test.ts (8 new tests: clean close, backoff schedule 1s->2s, max retries, REST timing, job-complete-during-disconnect, retryAttempt lifecycle)

---

## Pipeline execution

| Phase | Agents | Duration | Notes |
|-------|--------|----------|-------|
| Backlog analysis | 1 explorer | ~1.5 min | Analyzed all 8 areas, produced prioritized backlog |
| Architect | 3 parallel | ~4-6 min | All completed successfully, created OpenSpec artifacts |
| Developer | 3 parallel worktrees | ~5-8 min | All CI-verified before completion |
| Reviewer | 1 | ~2 min | All 6 checks passed on first run, 0 fixes needed |
| Merge + PR | orchestrator | ~2 min | 4 commits, pushed, PR created, CI green |

**Total wall-clock time:** ~20 min for 3 features

---

## Shared file handling

| File | Owner | Strategy |
|------|-------|----------|
| `en.json`, `es.json` | i18n developer | Added both i18n AND a11y keys |
| `DeckImportModal.tsx` | Split | a11y added label/id, i18n replaced string — merged by orchestrator (non-overlapping changes) |
| `SettingsModal.tsx` | Split | a11y added labels/ids, i18n replaced 4 strings — merged by orchestrator |

**Merge approach:** Copied a11y version as base (structural changes), then applied i18n string replacements on top with Edit tool. No conflicts.

---

## Lessons learned

### Shared file ownership works well
Assigning `en.json`/`es.json` ownership to the i18n developer (who also added a11y keys) completely avoided locale file merge issues. The a11y developer skipped its Task 2.

### Worktree Bash permission still an issue
WebSocket developer couldn't commit (no Bash permission). Orchestrator committed manually. This matches the known issue from PR #59.

### Reviewer found nothing to fix
First time the reviewer had zero issues. Contributing factors:
- Each developer ran full CI locally before completing
- Shared file ownership prevented conflicts
- No backend changes (all frontend-only) reduced cross-layer issues

### Non-overlapping shared files merge cleanly
When two developers modify the same file but in different locations (DeckImportModal: a11y adds label at line 51, i18n replaces string at line 70), copying one version and applying the other's changes via Edit is fast and reliable.

---

## Test coverage after this PR

- Backend: 502 tests passing
- Frontend: 46 tests passing (10 new a11y + 8 new WebSocket reconnection)
