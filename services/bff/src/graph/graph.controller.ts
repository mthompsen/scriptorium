import { Controller, Get, Param, Query, UseGuards } from '@nestjs/common';

import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { TenantContext } from '../auth/tenant-context';
import { EntityHit, Neighborhood, RetrievalGraphClient } from './retrieval-graph.client';

/**
 * Graph proxy (Section 7.1): the tenant scope comes from the JWT via
 * TenantContext — never from the client.
 */
@Controller('graph')
@UseGuards(JwtAuthGuard)
export class GraphController {
  constructor(
    private readonly tenant: TenantContext,
    private readonly retrieval: RetrievalGraphClient,
  ) {}

  @Get('search')
  search(@Query('q') query = ''): Promise<{ entities: EntityHit[] }> {
    const trimmed = query.trim().slice(0, 200);
    if (!trimmed) {
      return Promise.resolve({ entities: [] });
    }
    return this.retrieval.searchEntities(this.tenant.tenantId, trimmed);
  }

  @Get('entity/:id/neighborhood')
  neighborhood(@Param('id') entityId: string): Promise<Neighborhood> {
    return this.retrieval.neighborhood(this.tenant.tenantId, entityId);
  }
}
