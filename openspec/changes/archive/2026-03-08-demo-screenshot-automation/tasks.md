# Tasks: demo-screenshot-automation

> All tasks are in the `[frontend]` layer. No backend, core, or database changes required.
> Tasks are ordered sequentially; each depends on the previous.

---

## Task 1 [frontend] — Install Playwright Chromium browser

**Why:** `@playwright/test` is already a devDependency in `frontend/package.json`, but
the Chromium binary must be downloaded separately before the script can run. This is a
one-time machine setup step.

**Files involved:** none (installs to Playwright's system cache)

**Steps:**
```bash
cd frontend
npx playwright install chromium
```

**Done when:** `npx playwright install chromium` exits with code 0 and prints
`Chromium ... is already installed` or `Downloading Chromium`.

**Dependencies:** none

---

## Task 2 [frontend] — Create `frontend/scripts/screenshot-demo.mjs`

**Why:** This is the core deliverable — the script that automates screenshot capture.

**File:** `frontend/scripts/screenshot-demo.mjs` (create new)

**Implementation:**

```js
/**
 * Captures a screenshot of /demo and saves it to public/dashboard-preview.png.
 * Run with: node scripts/screenshot-demo.mjs
 * Requires the dev server to be running on http://localhost:5173
 */
import { chromium } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const OUTPUT = resolve(__dirname, '../public/dashboard-preview.png');

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

await page.setViewportSize({ width: 1280, height: 800 });
await page.goto('http://localhost:5173/demo', { waitUntil: 'networkidle' });

// Wait until card table rows are visible (demo data is rendered synchronously,
// but give React a moment to paint)
await page.waitForSelector('table tbody tr', { timeout: 10_000 });
await page.waitForTimeout(500);

await page.screenshot({ path: OUTPUT, fullPage: false });
await browser.close();

console.log(`Screenshot saved to ${OUTPUT}`);
```

**Key decisions captured in code:**
- `import.meta.url` → `__dirname` pattern: required for ESM modules (no native `__dirname`)
- `waitUntil: 'networkidle'`: ensures React render is complete; demo makes zero API calls
  so this is fast
- `waitForSelector('table tbody tr')`: spec requirement — must wait for card table rows
- `waitForTimeout(500)`: buffer for framer-motion fade-in transitions
- `fullPage: false`: captures viewport only (1280×800), not full scroll height

**Done when:**
- File exists at `frontend/scripts/screenshot-demo.mjs`
- Running `node scripts/screenshot-demo.mjs` (with dev server running) produces
  `frontend/public/dashboard-preview.png`
- Script exits with code 0 and logs the output path

**Dependencies:** Task 1

---

## Task 3 [frontend] — Add `screenshot:demo` npm script to `package.json`

**Why:** Provides the standardized `npm run screenshot:demo` invocation documented in the spec.

**File:** `frontend/package.json`

**Change:** Add one entry to the `"scripts"` object:

```json
"screenshot:demo": "node scripts/screenshot-demo.mjs"
```

The full scripts block after the change:

```json
"scripts": {
  "dev": "NODE_OPTIONS='--max-http-header-size=32768' vite",
  "build": "tsc -b && vite build",
  "lint": "eslint .",
  "preview": "vite preview",
  "test": "vitest run",
  "test:watch": "vitest",
  "screenshot:demo": "node scripts/screenshot-demo.mjs"
},
```

**Done when:** `npm run screenshot:demo` (from `frontend/`) executes the script without
`npm ERR! Missing script: screenshot:demo`.

**Dependencies:** Task 2

---

## Task 4 [frontend] — Run the script and commit `dashboard-preview.png`

**Why:** The spec requires the PNG to exist at `frontend/public/dashboard-preview.png`
so the landing page hero image loads correctly on first `git clone`.

**Steps:**
1. Start the dev server: `cd frontend && npm run dev`
2. In a second terminal: `cd frontend && npm run screenshot:demo`
3. Verify the file was written: `ls -lh public/dashboard-preview.png` (expect ~70-100 KB)
4. Open `http://localhost:5173/` and confirm the hero section shows the dashboard preview image
5. Stage and commit the PNG: `git add frontend/public/dashboard-preview.png && git commit -m "chore: add dashboard-preview.png baseline screenshot"`

**Done when:**
- `frontend/public/dashboard-preview.png` exists and is a valid PNG at 1280×800
- Opening the landing page (`/`) shows the hero image (not the gradient fallback)
- File is committed to git

**Dependencies:** Task 3

---

## Task 5 [frontend] — Add E2E smoke test for `/demo` page

**Why:** The existing `frontend/e2e/smoke.spec.ts` tests the landing and login pages
but does not cover `/demo`. The spec requires that card table rows are visible and the
demo banner is present. Adding a smoke test ensures regressions in demo mode are caught.

**File:** `frontend/e2e/smoke.spec.ts` (modify)

**Add these tests** at the end of the file:

```ts
// ---------------------------------------------------------------------------
// Smoke 6: /demo renders the card table
// ---------------------------------------------------------------------------
test('/demo renders card table with data', async ({ page }) => {
  await page.goto('/demo');
  // Card table rows must be present (demo data is synchronous)
  await expect(page.locator('table tbody tr').first()).toBeVisible({ timeout: 10_000 });
});

// ---------------------------------------------------------------------------
// Smoke 7: /demo shows the demo banner
// ---------------------------------------------------------------------------
test('/demo shows demo banner', async ({ page }) => {
  await page.goto('/demo');
  // Banner contains a sign-in link
  await expect(page.getByRole('button', { name: /sign in/i }).first()).toBeVisible();
});
```

**Done when:**
- `npm run test` (vitest) continues to pass (no unit test regressions)
- `npx playwright test` passes for the new smoke tests (requires dev server + backend or
  `SKIP_E2E=1` to skip in environments without the stack)

**Dependencies:** Task 2 (needs `/demo` to be reachable)

---

## Verification checklist

After all tasks are complete, verify:

- [ ] `frontend/scripts/screenshot-demo.mjs` exists and is syntactically valid ESM
- [ ] `npm run screenshot:demo` (with dev server running) produces `public/dashboard-preview.png`
- [ ] The generated PNG is 1280×800 and shows the card table with populated rows
- [ ] The landing page hero (`/`) shows the image (not the gradient fallback)
- [ ] `dashboard-preview.png` is committed to git
- [ ] E2E smoke tests for `/demo` pass
- [ ] `npm run lint` passes (no lint errors in the new script or test additions)
