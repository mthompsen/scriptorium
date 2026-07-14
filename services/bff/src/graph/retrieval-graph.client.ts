import { BadGatewayException, Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

export interface EntityHit {
  id: string;
  name: string;
  type: string;
  mention_count: number;
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  confidence: number;
}

export interface Neighborhood {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/** Internal client for the retrieval service's graph endpoints (Section 7.3). */
@Injectable()
export class RetrievalGraphClient {
  private readonly baseUrl: string;

  constructor(config: ConfigService) {
    this.baseUrl = config.get<string>('RETRIEVAL_URL', 'http://localhost:8080');
  }

  async searchEntities(tenantId: string, query: string): Promise<{ entities: EntityHit[] }> {
    return this.get(
      `/graph/search?tenant_id=${encodeURIComponent(tenantId)}&q=${encodeURIComponent(query)}`,
    );
  }

  async neighborhood(tenantId: string, entityId: string): Promise<Neighborhood> {
    return this.get(
      `/graph/entity/${encodeURIComponent(entityId)}/neighborhood?tenant_id=${encodeURIComponent(tenantId)}`,
    );
  }

  private async get<T>(path: string): Promise<T> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        signal: AbortSignal.timeout(15_000),
      });
    } catch {
      throw new BadGatewayException('Retrieval service unavailable');
    }
    if (!response.ok) {
      throw new BadGatewayException(`Retrieval service responded ${response.status}`);
    }
    return (await response.json()) as T;
  }
}
