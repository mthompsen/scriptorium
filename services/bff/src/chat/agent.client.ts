import { BadGatewayException, Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

export interface AgentCitation {
  chunk_id: string;
  document_id: string;
  snippet: string;
}

export interface AgentAnswer {
  answer: string;
  citations: AgentCitation[];
  grounded: boolean;
}

/** Internal client for the agent service's /answer (reason path). */
@Injectable()
export class AgentClient {
  private readonly baseUrl: string;

  constructor(config: ConfigService) {
    this.baseUrl = config.get<string>('AGENT_URL', 'http://localhost:8002');
  }

  async answer(tenantId: string, question: string): Promise<AgentAnswer> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId, question }),
        // Local CPU inference is slow (ADR-0004); generous but bounded.
        signal: AbortSignal.timeout(180_000),
      });
    } catch {
      throw new BadGatewayException('Agent service unavailable');
    }
    if (!response.ok) {
      throw new BadGatewayException(`Agent service responded ${response.status}`);
    }
    return (await response.json()) as AgentAnswer;
  }
}
