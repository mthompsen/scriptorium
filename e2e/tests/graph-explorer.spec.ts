import { expect, test } from '@playwright/test';

import { login } from './helpers';

/**
 * Graph explorer journey (Section 10): search an entity extracted from the
 * demo corpus, open its neighborhood, and see the rendered graph plus its
 * text alternative.
 */
test('searches an entity and renders its neighborhood', async ({ page }) => {
  await login(page);
  await page.goto('/graph');

  await page.getByLabel('Entity search').fill('Aurelia');
  await page.getByRole('button', { name: 'Search' }).click();

  // Entity chips come back from Neo4j via the BFF proxy.
  const chip = page.getByRole('button', { name: /Aurelia/i }).first();
  await expect(chip).toBeVisible();
  await chip.click();
  await expect(chip).toHaveAttribute('aria-pressed', 'true');

  // Canvas plus the accessible listing of relations.
  await expect(page.getByRole('img', { name: /Knowledge graph neighborhood/ })).toBeVisible();
  await expect(page.locator('canvas').first()).toBeVisible();
});
