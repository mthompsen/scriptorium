import { expect, test } from '@playwright/test';

import {
  LEGACY_ADMIN_PASSWORD,
  LEGACY_ADMIN_URL,
  LEGACY_ADMIN_USER,
  login,
} from './helpers';

/**
 * Legacy console journey (Section 15 M7, RP5): linked from the modern admin
 * page, guarded by HTTP Basic, server-rendered JSP with a jQuery-driven
 * refresh and corpus drill-down.
 */
test.describe('legacy admin console', () => {
  test('is linked from the modern admin page and labeled legacy', async ({ page }) => {
    await login(page);
    await page.goto('/admin');
    const link = page.getByRole('link', { name: /Open legacy console/ });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('href', LEGACY_ADMIN_URL);
    await expect(page.getByText('legacy', { exact: true })).toBeVisible();
  });

  test('rejects anonymous access', async ({ browser }) => {
    const context = await browser.newContext();
    const response = await context.request.get(LEGACY_ADMIN_URL);
    expect(response.status()).toBe(401);
    await context.close();
  });

  test('serves the JSP dashboard and corpus drill-down over Basic auth', async ({
    browser,
  }) => {
    const context = await browser.newContext({
      httpCredentials: { username: LEGACY_ADMIN_USER, password: LEGACY_ADMIN_PASSWORD },
    });
    const page = await context.newPage();
    await page.goto(LEGACY_ADMIN_URL);

    await expect(page).toHaveTitle(/Legacy Admin Console/);
    await expect(page.getByRole('heading', { name: 'Tenant corpora' })).toBeVisible();

    // The demo tenant row, rendered server-side by JSTL.
    const tenantRow = page.getByRole('row', { name: /11111111-1111-4111-8111/ });
    await expect(tenantRow).toBeVisible();

    // jQuery-driven refresh re-renders the table from the JSON API.
    await page.getByRole('button', { name: 'Refresh' }).click();
    await expect(page.getByRole('row', { name: /11111111-1111-4111-8111/ })).toBeVisible();

    // Corpus drill-down.
    await tenantRow.getByRole('link', { name: 'View corpus' }).click();
    await expect(page.getByRole('heading', { name: /Corpus for tenant/ })).toBeVisible();
    await expect(page.getByRole('table', { name: '' })).toBeVisible();

    await context.close();
  });
});
