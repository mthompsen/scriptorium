import { BadGatewayException, Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

export interface AgentCitation {
  chunk_id: string;
  document_id: string;
  snippet: string;
}

export interface AgentFinal {
  run_id: string;
  answer: string;
  citations: AgentCitation[];
  grounded: boolean;
}

export interface AgentStreamEvent {
  event: 'run_start' | 'token' | 'tool' | 'final';
  data: Record<string, unknown>;
}

const STREAM_TIMEOUT_MS = 300_000; // bounded run: loop budgets sit below this

/** Internal client for the agent service's /answer (reason path, SSE). */
@Injectable()
export class AgentClient {
  private readonly baseUrl: string;

  constructor(config: ConfigService) {
    this.baseUrl = config.get<string>('AGENT_URL', 'http://localhost:8002');
  }

  async *answerStream(tenantId: string, question: string): AsyncGenerator<AgentStreamEvent> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId, question, stream: true }),
        signal: AbortSignal.timeout(STREAM_TIMEOUT_MS),
      });
    } catch {
      throw new BadGatewayException('Agent service unavailable');
    }
    if (!response.ok || !response.body) {
      throw new BadGatewayException(`Agent service responded ${response.status}`);
    }

    const decoder = new TextDecoder();
    let buffer = '';
    for await (const chunk of response.body as unknown as AsyncIterable<Uint8Array>) {
      buffer += decoder.decode(chunk, { stream: true });
      let boundary: number;
      while ((boundary = buffer.indexOf('\n\n')) >= 0) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const parsed = parseSseBlock(block);
        if (parsed) {
          yield parsed;
        }
      }
    }
  }
}

function parseSseBlock(block: string): AgentStreamEvent | undefined {
  let event = '';
  let data = '';
  for (const line of block.split('\n')) {
    if (line.startsWith('event: ')) {
      event = line.slice('event: '.length).trim();
    } else if (line.startsWith('data: ')) {
      data = line.slice('data: '.length);
    }
  }
  if (!event || !data) {
    return undefined;
  }
  return { event, data: JSON.parse(data) } as AgentStreamEvent;
}
