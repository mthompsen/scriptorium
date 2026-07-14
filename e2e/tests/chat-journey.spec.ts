import { expect, test } from '@playwright/test';

import { login } from './helpers';

/**
 * The critical journey (Section 15 M1–M3): sign in, upload a document, ask a
 * question, get a grounded, cited answer streamed into the chat.
 */
test.describe('login → upload → cited answer', () => {
  // Parse → chunk → embed → index, then agent loop on a CPU-bound 3B model.
  test.setTimeout(600_000);

  test('uploads a document and receives a cited, grounded answer', async ({ page }) => {
    await login(page);

    // Upload a small handbook with an unmistakable grounded fact.
    await page.goto('/library');
    const content = [
      '# E2E Field Manual',
      '',
      '## Standby allowance',
      '',
      'Engineers on the on-call rotation receive a standby allowance of',
      '137 euros per week, paid monthly in arrears.',
    ].join('\n');
    await page.getByLabel('Document file').setInputFiles({
      name: 'e2e-field-manual.md',
      mimeType: 'text/markdown',
      buffer: Buffer.from(content),
    });
    await page.getByRole('button', { name: 'Upload' }).click();
    const row = page.getByRole('row', { name: /e2e-field-manual/ });
    await expect(row).toBeVisible();

    // Ingestion pipeline: wait for the status badge to reach "indexed".
    await expect(async () => {
      await page.reload();
      await expect(page.getByRole('row', { name: /e2e-field-manual/ }).first())
        .toContainText('indexed');
    }).toPass({ timeout: 300_000, intervals: [5_000] });

    // Ask about the fact; the agent must answer with it and cite a source.
    await page.goto('/chat');
    await page.getByLabel('Message').fill(
      'What is the weekly standby allowance for on-call engineers?',
    );
    await page.getByRole('button', { name: 'Send' }).click();

    const conversation = page.getByRole('log', { name: 'Conversation' });
    await expect(conversation).toContainText('137', { timeout: 300_000 });
    // Citations render as a collapsible "N source(s)" disclosure.
    const sources = conversation.getByText(/\d+ sources?/);
    await expect(sources.first()).toBeVisible();
    await sources.first().click();
    await expect(conversation.getByText(/e2e|standby|137/).first()).toBeVisible();
  });
});
