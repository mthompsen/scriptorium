import { expect, it } from 'vitest';

import { GET } from './route';

it('health route returns 200 with the service name', async () => {
  const response = GET();

  expect(response.status).toBe(200);
  expect(await response.json()).toEqual({ status: 'ok', service: 'frontend' });
});
