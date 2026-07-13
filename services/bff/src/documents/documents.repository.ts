import { Inject, Injectable } from '@nestjs/common';
import { Pool } from 'pg';

import { PG_POOL } from '../pg/pg.module';

export interface DocumentRow {
  id: string;
  tenant_id: string;
  title: string;
  mime_type: string;
  version: number;
  status: string;
  checksum: string;
  created_at: string;
  indexed_at: string | null;
}

@Injectable()
export class DocumentsRepository {
  constructor(@Inject(PG_POOL) private readonly pool: Pool) {}

  async insert(
    tenantId: string,
    title: string,
    mimeType: string,
    checksum: string,
  ): Promise<DocumentRow> {
    const result = await this.pool.query(
      `INSERT INTO documents (tenant_id, title, mime_type, checksum)
       VALUES ($1, $2, $3, $4)
       RETURNING *`,
      [tenantId, title, mimeType, checksum],
    );
    return result.rows[0] as DocumentRow;
  }

  async list(tenantId: string, limit: number, offset: number): Promise<DocumentRow[]> {
    const result = await this.pool.query(
      `SELECT * FROM documents
        WHERE tenant_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3`,
      [tenantId, limit, offset],
    );
    return result.rows as DocumentRow[];
  }

  async findById(tenantId: string, id: string): Promise<DocumentRow | undefined> {
    const result = await this.pool.query(
      `SELECT * FROM documents WHERE tenant_id = $1 AND id = $2`,
      [tenantId, id],
    );
    return result.rows[0] as DocumentRow | undefined;
  }

  async setStatus(tenantId: string, id: string, status: string): Promise<void> {
    await this.pool.query(`UPDATE documents SET status = $3 WHERE tenant_id = $1 AND id = $2`, [
      tenantId,
      id,
      status,
    ]);
  }
}
