import type { TenantContext } from '../auth/tenant-context';
import { GraphController } from './graph.controller';
import type { RetrievalGraphClient } from './retrieval-graph.client';

const tenant = { tenantId: 'tenant-1', userId: 'user-1' } as TenantContext;

const build = () => {
  const client = {
    searchEntities: jest.fn().mockResolvedValue({
      entities: [{ id: 'e1', name: 'Aurelia Corp', type: 'organization', mention_count: 4 }],
    }),
    neighborhood: jest.fn().mockResolvedValue({
      nodes: [{ id: 'e1', name: 'Aurelia Corp', type: 'organization' }],
      edges: [],
    }),
  };
  return {
    client,
    controller: new GraphController(tenant, client as unknown as RetrievalGraphClient),
  };
};

describe('GraphController', () => {
  it('injects the tenant scope server-side into entity search', async () => {
    const { controller, client } = build();

    const result = await controller.search('aurelia');

    expect(client.searchEntities).toHaveBeenCalledWith('tenant-1', 'aurelia');
    expect(result.entities[0].name).toBe('Aurelia Corp');
  });

  it('returns empty results for a blank query without calling retrieval', async () => {
    const { controller, client } = build();

    const result = await controller.search('   ');

    expect(result.entities).toEqual([]);
    expect(client.searchEntities).not.toHaveBeenCalled();
  });

  it('proxies neighborhood lookups tenant-scoped', async () => {
    const { controller, client } = build();

    await controller.neighborhood('e1');

    expect(client.neighborhood).toHaveBeenCalledWith('tenant-1', 'e1');
  });
});
