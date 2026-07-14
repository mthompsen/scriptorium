import { ExecutionContext, ForbiddenException } from '@nestjs/common';
import { Reflector } from '@nestjs/core';

import { ROLES_KEY } from './roles.decorator';
import { RolesGuard } from './roles.guard';
import { TenantContext } from './tenant-context';

function contextWith(): ExecutionContext {
  return {
    getHandler: () => () => undefined,
    getClass: () => class {},
  } as unknown as ExecutionContext;
}

function guardWith(required: string[] | undefined, held: string[]): RolesGuard {
  const reflector = {
    getAllAndOverride: () => required,
  } as unknown as Reflector;
  const tenant = { roles: held } as unknown as TenantContext;
  return new RolesGuard(reflector, tenant);
}

describe('RolesGuard', () => {
  it('allows any authenticated user when a handler has no @Roles metadata', () => {
    expect(guardWith(undefined, ['viewer']).canActivate(contextWith())).toBe(true);
    expect(guardWith([], ['viewer']).canActivate(contextWith())).toBe(true);
  });

  it('allows when the principal holds one of the required roles', () => {
    expect(guardWith(['owner', 'admin', 'member'], ['member']).canActivate(contextWith())).toBe(
      true,
    );
  });

  it('forbids when the principal holds none of the required roles', () => {
    expect(() =>
      guardWith(['owner', 'admin', 'member'], ['viewer']).canActivate(contextWith()),
    ).toThrow(ForbiddenException);
  });

  it('keys off ROLES_KEY metadata', () => {
    expect(ROLES_KEY).toBe('roles');
  });
});
