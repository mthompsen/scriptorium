import { expect, test } from '@playwright/test';

import {
  BFF_BASE_URL,
  DEMO_EMAIL,
  DEMO_PASSWORD,
  VIEWER_EMAIL,
  VIEWER_PASSWORD,
} from './helpers';

/**
 * The RBAC gate (ARCHITECTURE.md Section 11): the BFF's RolesGuard restricts
 * document upload to owner/admin/member. A viewer can read the corpus but is
 * denied the write. This is the negative test that proves the guard gates
 * something — without it, the guard is indistinguishable from scaffolding.
 */
test.describe('BFF role gate on document upload', () => {
  const smallDoc = {
    name: 'rbac-probe.md',
    mimeType: 'text/markdown',
    buffer: Buffer.from('# RBAC probe\n\nUpload should be role-gated.'),
  };

  test('viewer: 200 on GET /documents, 403 on POST /documents', async ({ playwright }) => {
    const ctx = await playwright.request.newContext({ baseURL: BFF_BASE_URL });
    const login = await ctx.post('/api/v1/auth/login', {
      data: { email: VIEWER_EMAIL, password: VIEWER_PASSWORD },
    });
    expect(login.status(), 'viewer login succeeds').toBe(201);

    const list = await ctx.get('/api/v1/documents');
    expect(list.status(), 'viewer can read the corpus').toBe(200);

    const upload = await ctx.post('/api/v1/documents', { multipart: { file: smallDoc } });
    expect(upload.status(), 'viewer is denied upload').toBe(403);

    await ctx.dispose();
  });

  test('owner: upload is allowed (control)', async ({ playwright }) => {
    const ctx = await playwright.request.newContext({ baseURL: BFF_BASE_URL });
    const login = await ctx.post('/api/v1/auth/login', {
      data: { email: DEMO_EMAIL, password: DEMO_PASSWORD },
    });
    expect(login.status()).toBe(201);

    const upload = await ctx.post('/api/v1/documents', { multipart: { file: smallDoc } });
    expect(upload.ok(), 'owner upload is not blocked by the role gate').toBeTruthy();
    expect(upload.status()).not.toBe(403);

    await ctx.dispose();
  });
});
