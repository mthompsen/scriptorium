import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

export interface IngestRequest {
  documentId: string;
  tenantId: string;
  filename: string;
  mimeType: string;
  bytes: Buffer;
}

/**
 * Internal client for the ingestion service. M1 calls it synchronously
 * (ADR-0003); M2 replaces this with the queue + transactional outbox.
 */
@Injectable()
export class IngestionClient {
  private readonly baseUrl: string;

  constructor(config: ConfigService) {
    this.baseUrl = config.get<string>('INGESTION_URL', 'http://localhost:8001');
  }

  async ingest(request: IngestRequest): Promise<void> {
    const form = new FormData();
    form.append('document_id', request.documentId);
    form.append('tenant_id', request.tenantId);
    form.append(
      'file',
      new Blob([new Uint8Array(request.bytes)], { type: request.mimeType }),
      request.filename,
    );
    const response = await fetch(`${this.baseUrl}/ingest`, {
      method: 'POST',
      body: form,
      signal: AbortSignal.timeout(15_000),
    });
    if (!response.ok) {
      throw new Error(`ingestion responded ${response.status}`);
    }
  }
}
