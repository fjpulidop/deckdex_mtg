import { test, expect, Page } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helper: collect uncaught JS errors during a page load
// ---------------------------------------------------------------------------
function collectPageErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('pageerror', (err) => {
    // Ignore network-related errors (backend not running is expected in E2E)
    const msg = err.message ?? '';
    if (!msg.includes('NetworkError') && !msg.includes('Failed to fetch') && !msg.includes('Load failed')) {
      errors.push(msg);
    }
  });
  return errors;
}

// ---------------------------------------------------------------------------
// Smoke 1: Landing page loads
// ---------------------------------------------------------------------------
test('landing page loads and has correct title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle('DeckDex MTG');
});

// ---------------------------------------------------------------------------
// Smoke 2: Landing page renders sign-in content
// ---------------------------------------------------------------------------
test('landing page renders sign-in button or dashboard content', async ({ page }) => {
  await page.goto('/');
  // The landing page hero has a "Sign in" button and landing navbar is visible.
  // Accept either the hero sign-in button OR the app navbar (when already logged in).
  const signIn = page.getByRole('button', { name: /sign in/i }).first();
  const nav = page.locator('nav').first();
  // At least one of them must be present
  await expect(signIn.or(nav)).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
// Smoke 3: Navigation element is present
// ---------------------------------------------------------------------------
test('navigation element is rendered on the landing page', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('nav').first()).toBeVisible();
});

// ---------------------------------------------------------------------------
// Smoke 4: No uncaught JS errors on page load
// ---------------------------------------------------------------------------
test('no uncaught JS errors on landing page load', async ({ page }) => {
  const errors = collectPageErrors(page);
  await page.goto('/');
  // Give the app a moment to settle
  await page.waitForTimeout(500);
  expect(errors).toHaveLength(0);
});

// ---------------------------------------------------------------------------
// Smoke 5: Login page renders
// ---------------------------------------------------------------------------
test('login page renders sign-in button', async ({ page }) => {
  await page.goto('/login');
  // The login page has a "Continue with Google" button and a DeckDex heading
  await expect(page.getByText('DeckDex')).toBeVisible();
  await expect(page.getByRole('button', { name: /continue with google/i })).toBeVisible();
});
