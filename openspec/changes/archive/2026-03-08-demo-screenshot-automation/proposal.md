## Why

The landing page hero section displays a `dashboard-preview.png` that shows the DeckDex
dashboard in action. This image must be regenerated whenever the UI changes, but there
was no automated, reproducible way to capture it — requiring a manual browser screenshot
workflow that is error-prone and undocumented. The screenshot tooling requirement is the
final deliverable in the demo-mode capability (5 of 6 previously completed).

## What Changes

- `frontend/scripts/screenshot-demo.mjs` — Playwright-based Node script that launches
  Chromium headless, navigates to `/demo`, waits for card table rows to render, then
  saves a 1280×800 viewport screenshot to `frontend/public/dashboard-preview.png`.
- `frontend/package.json` — adds `"screenshot:demo": "node scripts/screenshot-demo.mjs"`
  to the `scripts` section so developers can run `npm run screenshot:demo`.
- `frontend/public/dashboard-preview.png` — the output artifact committed to the repo as
  the initial baseline image (regenerated whenever the UI changes meaningfully).

No breaking changes. No API changes. No backend changes.

## Non-goals

- CI automation: the script requires the Vite dev server to be running and is not wired
  into any GitHub Actions workflow.
- Multi-browser or multi-resolution screenshots.
- Automated re-generation on every build.

## Capabilities

### New Capabilities

- none

### Modified Capabilities

- `demo-mode`: adds the screenshot tooling scenario (was the only unimplemented
  requirement in the existing `openspec/specs/demo-mode/spec.md`).

## Impact

- `frontend/scripts/screenshot-demo.mjs` — new file (Node ESM, Playwright)
- `frontend/package.json` — one new `scripts` entry
- `frontend/public/dashboard-preview.png` — binary output committed to repo
- `@playwright/test` — already a devDependency; Chromium browser must be installed
  (`npx playwright install chromium`)
