## Delta spec — demo-mode

Base spec: `openspec/specs/demo-mode/spec.md`

This delta only documents the **screenshot tooling** requirement, which was the sole
unimplemented scenario in the base spec. All other requirements (public demo route, mock
data, filtering) remain unchanged and are already fully implemented.

---

### Requirement: Demo screenshot tooling (IMPLEMENTED)

The system SHALL provide a Playwright script that captures a screenshot of `/demo` for
use as the landing page hero image.

#### Scenario: Script invocation

- **GIVEN** the Vite dev server is running on `http://localhost:5173`
- **WHEN** a developer runs `npm run screenshot:demo` from `frontend/`
- **THEN** `frontend/scripts/screenshot-demo.mjs` is executed via `node`

#### Scenario: Script generates screenshot

- **WHEN** `npm run screenshot:demo` is executed
- **THEN** a PNG file SHALL be saved to `frontend/public/dashboard-preview.png`
  at 1280×800 viewport resolution

#### Scenario: Script waits for content

- **WHEN** the script navigates to `/demo`
- **THEN** it SHALL wait until `table tbody tr` is present in the DOM before
  capturing, ensuring the screenshot shows populated card data

#### Scenario: Script exits cleanly

- **WHEN** the screenshot has been saved
- **THEN** the script SHALL log the output path to stdout and exit with code 0

#### Scenario: Script fails fast on missing dev server

- **WHEN** no server is listening on `http://localhost:5173`
- **THEN** the script SHALL exit with a non-zero code and a connection-refused
  error printed to stderr

---

### Implementation notes (non-normative)

- Script location: `frontend/scripts/screenshot-demo.mjs`
- npm script key: `"screenshot:demo": "node scripts/screenshot-demo.mjs"`
- Playwright import: `import { chromium } from '@playwright/test'`
- Chromium prerequisite: `npx playwright install chromium` (one-time per machine)
- The script does NOT use `playwright.config.ts` — it is a standalone programmatic
  invocation, not a test suite run
- Output PNG is committed to the repository as the baseline hero image
