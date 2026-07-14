import { CanActivate, ExecutionContext, ForbiddenException, Injectable } from '@nestjs/common';
import { Reflector } from '@nestjs/core';

import { ROLES_KEY } from './roles.decorator';
import { TenantContext } from './tenant-context';

/**
 * Enforces @Roles metadata against the roles the JWT carried, read via the
 * request-scoped TenantContext that JwtAuthGuard populates.
 *
 * MUST run after JwtAuthGuard — apply as `@UseGuards(JwtAuthGuard,
 * RolesGuard)` in that order, never as an APP_GUARD: global guards execute
 * before controller guards, so the principal (and thus the role list) would
 * not yet be populated.
 *
 * A handler with no @Roles metadata is unrestricted for any authenticated
 * user, so this guard gates only the endpoints that opt in.
 */
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly tenant: TenantContext,
  ) {}

  canActivate(context: ExecutionContext): boolean {
    const required = this.reflector.getAllAndOverride<string[] | undefined>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (!required || required.length === 0) {
      return true;
    }
    if (this.tenant.roles.some((role) => required.includes(role))) {
      return true;
    }
    throw new ForbiddenException('Insufficient role for this action');
  }
}
