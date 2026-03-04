import { chromium } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
page.on('pageerror', e => console.error('[pageerror]', e.message));
await page.setViewportSize({ width: 1280, height: 800 });

// Check landing page
await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
const hasHeroImage = await page.$('img[alt="DeckDex dashboard preview"]');
const hasLiveDemo = await page.$('a[href="/demo"]');
console.log('Landing - Hero image present:', !!hasHeroImage);
console.log('Landing - Try live demo link:', !!hasLiveDemo);
await page.screenshot({ path: resolve(__dirname, '../public/debug-landing.png') });

// Check /demo
await page.goto('http://localhost:5173/demo', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
const hasTable = await page.$('table tbody tr');
console.log('/demo URL:', page.url());
console.log('/demo - Has table rows:', !!hasTable);
await page.screenshot({ path: resolve(__dirname, '../public/debug-demo.png') });

await browser.close();
