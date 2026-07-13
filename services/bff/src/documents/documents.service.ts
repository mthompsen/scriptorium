import {
  BadGatewayException,
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { createHash } from 'node:crypto';

import { TenantContext } from '../auth/tenant-context';
import { DocumentRow, DocumentsRepository } from './documents.repository';
import { IngestionClient } from './ingestion.client';

// Supported formats per DESIGN.md Section 3.2 (non-goals bound the list).
const ALLOWED_MIME_TYPES = new Set([
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/markdown',
  'text/html',
  'text/plain',
]);

// Client-supplied MIME is unreliable (e.g. .md often arrives as
// octet-stream); fall back to the extension for the supported formats.
const EXTENSION_MIME_TYPES: Record<string, string> = {
  '.pdf': 'application/pdf',
  '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  '.md': 'text/markdown',
  '.markdown': 'text/markdown',
  '.html': 'text/html',
  '.htm': 'text/html',
  '.txt': 'text/plain',
};

const resolveMimeType = (filename: string, reported: string): string | undefined => {
  if (ALLOWED_MIME_TYPES.has(reported)) {
    return reported;
  }
  const extension = filename.slice(filename.lastIndexOf('.')).toLowerCase();
  return EXTENSION_MIME_TYPES[extension];
};

export interface UploadedFile {
  originalname: string;
  mimetype: string;
  buffer: Buffer;
}

@Injectable()
export class DocumentsService {
  constructor(
    private readonly tenant: TenantContext,
    private readonly repository: DocumentsRepository,
    private readonly ingestion: IngestionClient,
  ) {}

  async upload(file: UploadedFile): Promise<DocumentRow> {
    const mimeType = resolveMimeType(file.originalname, file.mimetype);
    if (!mimeType) {
      throw new BadRequestException(
        `Unsupported type ${file.mimetype}; allowed: PDF, DOCX, Markdown, HTML, plain text`,
      );
    }
    const checksum = createHash('sha256').update(file.buffer).digest('hex');
    const row = await this.repository.insert(
      this.tenant.tenantId,
      file.originalname,
      mimeType,
      checksum,
    );
    try {
      await this.ingestion.ingest({
        documentId: row.id,
        tenantId: this.tenant.tenantId,
        filename: file.originalname,
        mimeType,
        bytes: file.buffer,
      });
    } catch {
      await this.repository.setStatus(this.tenant.tenantId, row.id, 'failed');
      throw new BadGatewayException('Ingestion service unavailable; document marked failed');
    }
    return (await this.repository.findById(this.tenant.tenantId, row.id)) ?? row;
  }

  async list(limit = 20, offset = 0): Promise<DocumentRow[]> {
    return this.repository.list(this.tenant.tenantId, Math.min(limit, 100), offset);
  }

  async status(id: string): Promise<{ id: string; status: string; indexedAt: string | null }> {
    const row = await this.repository.findById(this.tenant.tenantId, id);
    if (!row) {
      throw new NotFoundException('Document not found');
    }
    return { id: row.id, status: row.status, indexedAt: row.indexed_at };
  }
}
