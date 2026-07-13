import { Inject, Injectable } from '@nestjs/common';
import { Pool } from 'pg';

import { PG_POOL } from '../pg/pg.module';

export interface UserWithRoles {
  id: string;
  tenantId: string;
  email: string;
  passwordHash: string;
  roles: string[];
}

@Injectable()
export class UsersRepository {
  constructor(@Inject(PG_POOL) private readonly pool: Pool) {}

  async findByEmail(email: string): Promise<UserWithRoles | undefined> {
    const result = await this.pool.query(
      `SELECT u.id, u.tenant_id, u.email, u.password_hash,
              COALESCE(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), '{}') AS roles
         FROM users u
         LEFT JOIN user_roles ur ON ur.user_id = u.id
         LEFT JOIN roles r ON r.id = ur.role_id
        WHERE lower(u.email) = lower($1)
        GROUP BY u.id`,
      [email],
    );
    const row:
      | { id: string; tenant_id: string; email: string; password_hash: string; roles: string[] }
      | undefined = result.rows[0];
    if (!row) {
      return undefined;
    }
    return {
      id: row.id,
      tenantId: row.tenant_id,
      email: row.email,
      passwordHash: row.password_hash,
      roles: row.roles,
    };
  }
}
