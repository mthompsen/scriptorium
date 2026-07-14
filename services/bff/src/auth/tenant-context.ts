import { Inject, Injectable, Scope } from '@nestjs/common';
import { REQUEST } from '@nestjs/core';

import type { AuthenticatedRequest } from './principal';

/**
 * Request-scoped carrier of the tenant scope derived from the JWT
 * (ARCHITECTURE.md Section 7.1). Downstream services read tenant/user identity
 * from here, never from client-supplied values.
 */
@Injectable({ scope: Scope.REQUEST })
export class TenantContext {
  constructor(@Inject(REQUEST) private readonly request: AuthenticatedRequest) {}

  get tenantId(): string {
    return this.request.principal.tenantId;
  }

  get userId(): string {
    return this.request.principal.userId;
  }

  get roles(): string[] {
    return this.request.principal.roles;
  }
}
