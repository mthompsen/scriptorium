import { expect, test } from '@playwright/test';

import {
  LEGACY_ADMIN_PASSWORD,
  LEGACY_ADMIN_URL,
  LEGACY_ADMIN_USER,
  login,
} from './helpers';

/**
 * README screenshot capture — not a test of behavior. Run explicitly with:
 *   SCREENSHOTS=1 npx playwright test tests/screenshots.spec.ts
 * Writes into docs/screenshots/ at the repo root.
 */
const OUT = '../docs/screenshots';

test.describe('README screenshots', () => {
  test.skip(!process.env.SCREENSHOTS, 'set SCREENSHOTS=1 to capture');
  test.setTimeout(600_000);

  test('chat with cited answer', async ({ page }) => {
    await login(page);
    await page.goto('/chat');
    await page.getByLabel('Message').fill(
      'How many days of paid time off do employees get, and how does it accrue?',
    );
    await page.getByRole('button', { name: 'Send' }).click();
    const conversation = page.getByRole('log', { name: 'Conversation' });
    const sources = conversation.getByText(/\d+ sources?/);
    await expect(sources.first()).toBeVisible({ timeout: 400_000 });
    // Open the tool trace and the citations so the screenshot shows both.
    const activity = conversation.getByText(/Agent activity/);
    if (await activity.count()) {
      await activity.first().click();
    }
    await sources.first().click();
    await page.screenshot({ path: `${OUT}/chat-cited-answer.png`, fullPage: true });
  });

  test('library', async ({ page }) => {
    await login(page);
    await page.goto('/library');
    await expect(page.getByRole('table')).toBeVisible();
    await page.screenshot({ path: `${OUT}/library.png`, fullPage: true });
  });

  test('graph explorer', async ({ page }) => {
    await login(page);
    await page.goto('/graph');
    await page.getByLabel('Entity search').fill('Aurelia');
    await page.getByRole('button', { name: 'Search' }).click();
    const chip = page.getByRole('button', { name: /Aurelia/i }).first();
    await chip.click();
    await expect(page.locator('canvas').first()).toBeVisible();
    await page.waitForTimeout(2_500); // let the force layout settle
    await page.screenshot({ path: `${OUT}/graph-explorer.png`, fullPage: true });
  });

  test('admin and legacy console', async ({ browser, page }) => {
    await login(page);
    await page.goto('/admin');
    await expect(page.getByRole('link', { name: /Open legacy console/ })).toBeVisible();
    await page.screenshot({ path: `${OUT}/admin.png`, fullPage: true });

    const context = await browser.newContext({
      httpCredentials: { username: LEGACY_ADMIN_USER, password: LEGACY_ADMIN_PASSWORD },
    });
    const legacy = await context.newPage();
    await legacy.goto(LEGACY_ADMIN_URL);
    await expect(legacy.getByRole('heading', { name: 'Tenant corpora' })).toBeVisible();
    await legacy.screenshot({ path: `${OUT}/legacy-admin-console.png`, fullPage: true });
    await context.close();
  });
});
