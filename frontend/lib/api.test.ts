import { afterEach, expect, it, vi } from 'vitest';

import { api, ApiError } from './api';

afterEach(() => {
  vi.unstubAllGlobals();
});

it('returns parsed JSON on success', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(Response.json({ id: 'doc-1' })),
  );

  await expect(api<{ id: string }>('/documents')).resolves.toEqual({ id: 'doc-1' });
});

it('throws ApiError carrying status and server message', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(Response.json({ message: 'Invalid credentials' }, { status: 401 })),
  );

  const error = await api('/auth/me').catch((e: unknown) => e);

  expect(error).toBeInstanceOf(ApiError);
  expect((error as ApiError).status).toBe(401);
  expect((error as ApiError).message).toBe('Invalid credentials');
});

it('sends credentials so the HttpOnly cookie travels', async () => {
  const fetchMock = vi.fn().mockResolvedValue(Response.json({}));
  vi.stubGlobal('fetch', fetchMock);

  await api('/documents');

  expect(fetchMock).toHaveBeenCalledWith(
    expect.stringContaining('/api/v1/documents'),
    expect.objectContaining({ credentials: 'include' }),
  );
});
