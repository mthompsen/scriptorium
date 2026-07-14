import { MatchersV3, PactV3 } from '@pact-foundation/pact';
import { ConfigService } from '@nestjs/config';
import path from 'node:path';

import { RetrievalGraphClient } from './retrieval-graph.client';

const { eachLike, string, integer, decimal } = MatchersV3;

jest.setTimeout(60_000);

const TENANT = '11111111-1111-4111-8111-111111111111';

/**
 * Consumer-driven contract for the BFF -> retrieval graph API (ADR-0006).
 * The generated pact is committed to packages/contracts/pacts and verified
 * by the retrieval service's Gradle build (pact-jvm).
 */
const provider = new PactV3({
  consumer: 'bff',
  provider: 'retrieval',
  dir: path.resolve(__dirname, '..', '..', '..', '..', 'packages', 'contracts', 'pacts'),
});

const clientFor = (baseUrl: string): RetrievalGraphClient =>
  new RetrievalGraphClient({ get: () => baseUrl } as unknown as ConfigService);

describe('BFF -> retrieval graph contract', () => {
  it('searches entities scoped to a tenant', async () => {
    provider
      .given('entities exist for the demo tenant')
      .uponReceiving('an entity search')
      .withRequest({
        method: 'GET',
        path: '/graph/search',
        query: { tenant_id: TENANT, q: 'aurelia' },
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          entities: eachLike({
            id: string('abc123def456'),
            name: string('Aurelia Corp'),
            type: string('organization'),
            mention_count: integer(4),
          }),
        },
      });

    await provider.executeTest(async (mockServer) => {
      const result = await clientFor(mockServer.url).searchEntities(TENANT, 'aurelia');

      expect(result.entities[0].name).toBe('Aurelia Corp');
      expect(result.entities[0].mention_count).toBe(4);
    });
  });

  it('fetches an entity neighborhood', async () => {
    provider
      .given('entity abc123def456 has related entities')
      .uponReceiving('a neighborhood lookup')
      .withRequest({
        method: 'GET',
        path: '/graph/entity/abc123def456/neighborhood',
        query: { tenant_id: TENANT },
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          nodes: eachLike({
            id: string('abc123def456'),
            name: string('Aurelia Corp'),
            type: string('organization'),
          }),
          edges: eachLike({
            source: string('abc123def456'),
            target: string('def456abc123'),
            relation: string('owns'),
            confidence: decimal(0.9),
          }),
        },
      });

    await provider.executeTest(async (mockServer) => {
      const result = await clientFor(mockServer.url).neighborhood(TENANT, 'abc123def456');

      expect(result.nodes.length).toBeGreaterThan(0);
      expect(result.edges[0].relation).toBe('owns');
    });
  });
});
