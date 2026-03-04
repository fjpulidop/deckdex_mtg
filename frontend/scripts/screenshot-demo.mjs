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
