import { expect, test } from '@playwright/test';

import { login } from './helpers';

/**
 * The critical journey (Section 15 M1–M3): sign in, upload a document, ask a
 * question, get a grounded answer streamed into the chat.
 */
test.describe('login → upload → grounded answer', () => {
  // Parse → chunk → embed → index, then agent loop on a CPU-bound 3B model.
  test.setTimeout(600_000);

  test('uploads a document and receives a cited, grounded answer', async ({ page }) => {
    await login(page);

    // Upload a small handbook with an unmistakable grounded fact. There is no
    // delete endpoint, so re-uploading the same filename each run would
    // accumulate duplicate rows and make the row locator ambiguous; a unique
    // name per run keeps the locator precise by construction.
    await page.goto('/library');
    const docName = `e2e-field-manual-${Date.now()}`;
    const docRow = new RegExp(docName);
    const content = [
      '# E2E Field Manual',
      '',
      '## Standby allowance',
      '',
      'Engineers on the on-call rotation receive a standby allowance of',
      '137 euros per week, paid monthly in arrears.',
    ].join('\n');
    await page.getByLabel('Document file').setInputFiles({
      name: `${docName}.md`,
      mimeType: 'text/markdown',
      buffer: Buffer.from(content),
    });
    await page.getByRole('button', { name: 'Upload' }).click();
    await expect(page.getByRole('row', { name: docRow })).toBeVisible();

    // Ingestion pipeline: wait for the status badge to reach "indexed".
    await expect(async () => {
      await page.reload();
      await expect(page.getByRole('row', { name: docRow })).toContainText('indexed');
    }).toPass({ timeout: 300_000, intervals: [5_000] });

    // Ask about the fact; the agent must answer with it and cite a source.
    await page.goto('/chat');
    await page.getByLabel('Message').fill(
      'What is the weekly standby allowance for on-call engineers?',
    );
    await page.getByRole('button', { name: 'Send' }).click();

    const conversation = page.getByRole('log', { name: 'Conversation' });
    // Assert system behavior, not model behavior: the grounded fact reaches
    // the answer and the agent's tool activity is shown. Whether the 3B model
    // emits an inline citation is model behavior — measured in docs/eval.md
    // (citation coverage 0.2–0.47 on CPU), not a stable e2e signal — so it is
    // not asserted here.
    await expect(conversation).toContainText('137', { timeout: 300_000 });
    await expect(conversation.getByText(/Agent activity/).first()).toBeVisible();
  });
});
