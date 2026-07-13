import { BadGatewayException, BadRequestException, NotFoundException } from '@nestjs/common';

import type { TenantContext } from '../auth/tenant-context';
import type { DocumentsRepository } from './documents.repository';
import { DocumentsService, UploadedFile } from './documents.service';
import type { IngestionClient } from './ingestion.client';

const tenant = { tenantId: 'tenant-1', userId: 'user-1' } as TenantContext;

const mdFile = (): UploadedFile => ({
  originalname: 'handbook.md',
  mimetype: 'text/markdown',
  buffer: Buffer.from('# Hello'),
});

const row = { id: 'doc-1', tenant_id: 'tenant-1', status: 'uploaded', indexed_at: null };

interface Mocks {
  repository: jest.Mocked<Pick<DocumentsRepository, 'insert' | 'list' | 'findById' | 'setStatus'>>;
  ingestion: { ingest: jest.Mock };
}

const build = (): { service: DocumentsService } & Mocks => {
  const repository = {
    insert: jest.fn().mockResolvedValue(row),
    list: jest.fn().mockResolvedValue([row]),
    findById: jest.fn().mockResolvedValue({ ...row, status: 'stored' }),
    setStatus: jest.fn().mockResolvedValue(undefined),
  };
  const ingestion = { ingest: jest.fn().mockResolvedValue(undefined) };
  const service = new DocumentsService(
    tenant,
    repository as unknown as DocumentsRepository,
    ingestion as unknown as IngestionClient,
  );
  return { service, repository: repository as Mocks['repository'], ingestion };
};

describe('DocumentsService', () => {
  it('stores the registry row and hands the file to ingestion', async () => {
    const { service, repository, ingestion } = build();

    const result = await service.upload(mdFile());

    expect(repository.insert).toHaveBeenCalledWith(
      'tenant-1',
      'handbook.md',
      'text/markdown',
      expect.stringMatching(/^[0-9a-f]{64}$/), // sha256 checksum
    );
    expect(ingestion.ingest).toHaveBeenCalledWith(
      expect.objectContaining({ documentId: 'doc-1', tenantId: 'tenant-1' }),
    );
    expect(result.status).toBe('stored');
  });

  it('resolves generic octet-stream uploads by extension (browsers vary for .md)', async () => {
    const { service, repository } = build();

    await service.upload({ ...mdFile(), mimetype: 'application/octet-stream' });

    expect(repository.insert).toHaveBeenCalledWith(
      'tenant-1',
      'handbook.md',
      'text/markdown',
      expect.any(String),
    );
  });

  it('rejects unsupported types before touching storage', async () => {
    const { service, repository } = build();

    await expect(
      service.upload({
        ...mdFile(),
        originalname: 'setup.exe',
        mimetype: 'application/x-msdownload',
      }),
    ).rejects.toThrow(BadRequestException);
    expect(repository.insert).not.toHaveBeenCalled();
  });

  it('marks the document failed when ingestion is down', async () => {
    const { service, repository, ingestion } = build();
    ingestion.ingest.mockRejectedValue(new Error('connect ECONNREFUSED'));

    await expect(service.upload(mdFile())).rejects.toThrow(BadGatewayException);
    expect(repository.setStatus).toHaveBeenCalledWith('tenant-1', 'doc-1', 'failed');
  });

  it('scopes status lookups to the tenant and 404s on a miss', async () => {
    const { service, repository } = build();
    repository.findById.mockResolvedValue(undefined);

    await expect(service.status('doc-9')).rejects.toThrow(NotFoundException);
    expect(repository.findById).toHaveBeenCalledWith('tenant-1', 'doc-9');
  });
});
