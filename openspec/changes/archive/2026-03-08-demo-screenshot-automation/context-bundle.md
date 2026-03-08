# Context Bundle — demo-screenshot-automation

Compact reference for the developer implementing this change. Read this instead of
re-reading every file from scratch.

---

## Files to create

### `frontend/scripts/screenshot-demo.mjs` (NEW)

Complete implementation — copy this verbatim:

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

await page.waitForSelector('table tbody tr', { timeout: 10_000 });
await page.waitForTimeout(500);

await page.screenshot({ path: OUTPUT, fullPage: false });
await browser.close();

console.log(`Screenshot saved to ${OUTPUT}`);
```

**Why ESM pattern for `__dirname`:** `frontend/package.json` has `"type": "module"`, so
`.js`/`.mjs` files are ESM. ESM has no native `__dirname` — derive it from `import.meta.url`.

---

## Files to modify

### `frontend/package.json` — add one script entry

Current `scripts` block (lines 6–13):

```json
"scripts": {
  "dev": "NODE_OPTIONS='--max-http-header-size=32768' vite",
  "build": "tsc -b && vite build",
  "lint": "eslint .",
  "preview": "vite preview",
  "test": "vitest run",
  "test:watch": "vitest"
},
```

Add `"screenshot:demo"` entry:

```json
"screenshot:demo": "node scripts/screenshot-demo.mjs"
```

---

### `frontend/e2e/smoke.spec.ts` — add two tests at end of file

Current file ends at line 66 after the login smoke test. Append:

```ts
test('/demo renders card table with data', async ({ page }) => {
  await page.goto('/demo');
  await expect(page.locator('table tbody tr').first()).toBeVisible({ timeout: 10_000 });
});

test('/demo shows demo banner', async ({ page }) => {
  await page.goto('/demo');
  await expect(page.getByRole('button', { name: /sign in/i }).first()).toBeVisible();
});
```

---

## Key context: why the script works without backend

`/demo` renders `Demo.tsx` which wraps `Dashboard` in `DemoProvider`. The
`useDemoMode()` hook returns `isDemoMode: true`, which causes `useApi.ts` hooks to return
mock data from `frontend/src/data/demoData.ts` instead of making API calls. This means:

- No backend needs to be running for the screenshot
- `waitUntil: 'networkidle'` resolves quickly (zero network requests)
- `waitForSelector('table tbody tr')` resolves in <200ms (data is synchronous)

---

## Prerequisites before running

```bash
# One-time: install Chromium (if not already done)
cd frontend && npx playwright install chromium

# Each time: dev server must be running first
npm run dev   # terminal 1

# Then run the script
npm run screenshot:demo   # terminal 2
```

---

## Selector used for wait

`table tbody tr` — matches rendered rows in `CardTable.tsx`. The component renders a
standard HTML `<table>` with `<tbody>` containing one `<tr>` per card. The demo has 35
cards so this selector always matches after React renders.

---

## Output file location

`frontend/public/dashboard-preview.png` → served by Vite as `/dashboard-preview.png`
→ consumed by `Hero.tsx` at `src="/dashboard-preview.png"` (line 90).

The `<img>` has an `onError` fallback that hides it and shows a gradient placeholder,
so the page never breaks if the file is absent — but the image is committed to git so
it's always present after clone.
