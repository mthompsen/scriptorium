import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

import { login } from './helpers';

/**
 * Accessibility gate (Section 10: semantic HTML5, keyboard nav, ARIA).
 * Fails on serious/critical axe-core violations on every modern page.
 */
const SEVERITIES = ['serious', 'critical'];

async function expectNoSeriousViolations(page: import('@playwright/test').Page) {
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter((violation) =>
    SEVERITIES.includes(violation.impact ?? ''),
  );
  expect(
    serious.map((violation) => `${violation.id}: ${violation.description}`),
  ).toEqual([]);
}

test('home and login pages pass axe', async ({ page }) => {
  await page.goto('/');
  await expectNoSeriousViolations(page);
  await page.goto('/login');
  await expectNoSeriousViolations(page);
});

test('authenticated pages pass axe', async ({ page }) => {
  await login(page);
  for (const path of ['/chat', '/library', '/graph', '/admin']) {
    await page.goto(path);
    await expectNoSeriousViolations(page);
  }
});

test('keyboard: skip link jumps to main content', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  const skip = page.getByRole('link', { name: 'Skip to main content' });
  await expect(skip).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/#main$/);
});
