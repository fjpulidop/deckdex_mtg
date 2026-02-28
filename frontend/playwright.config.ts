import { defineConfig, devices } from '@playwright/test';

const skipE2E = process.env.SKIP_E2E === '1';

export default defineConfig({
  testDir: './e2e',
  timeout: 10_000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // Start the Vite dev server before running tests.
  // Set SKIP_E2E=1 to skip tests when the stack is unavailable.
  ...(skipE2E
    ? {}
    : {
        webServer: {
          command: 'npm run dev',
          url: 'http://localhost:5173',
          reuseExistingServer: true,
          timeout: 30_000,
        },
      }),
});
