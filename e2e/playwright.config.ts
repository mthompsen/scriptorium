import { defineConfig, devices } from '@playwright/test';

/**
 * Runs against the already-started compose stack (make up), not a managed
 * dev server. Single worker: the journeys share the demo tenant's corpus.
 * Generous timeouts: local generation runs a 3B model on CPU (ADR-0004).
 */
export default defineConfig({
  testDir: './tests',
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
