import type { ExecutionContext } from '@nestjs/common';
import { UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';

import { JwtAuthGuard } from './jwt-auth.guard';
import type { AuthenticatedRequest } from './principal';

const jwtService = new JwtService({ secret: 'test-secret', signOptions: { expiresIn: '5m' } });
const guard = new JwtAuthGuard(jwtService);

const contextFor = (request: Partial<AuthenticatedRequest>): ExecutionContext =>
  ({
    switchToHttp: () => ({ getRequest: () => request }),
  }) as unknown as ExecutionContext;

const validToken = (): Promise<string> =>
  jwtService.signAsync({
    sub: 'user-1',
    tenant_id: 'tenant-1',
    email: 'demo@scriptorium.local',
    roles: ['owner'],
  });

describe('JwtAuthGuard', () => {
  it('accepts a bearer token and attaches the principal', async () => {
    const request: Partial<AuthenticatedRequest> = {
      headers: { authorization: `Bearer ${await validToken()}` },
      cookies: {},
    };

    await expect(guard.canActivate(contextFor(request))).resolves.toBe(true);
    expect(request.principal).toEqual({
      userId: 'user-1',
      tenantId: 'tenant-1',
      email: 'demo@scriptorium.local',
      roles: ['owner'],
    });
  });

  it('accepts the HttpOnly cookie', async () => {
    const request: Partial<AuthenticatedRequest> = {
      headers: {},
      cookies: { st_access: await validToken() },
    };

    await expect(guard.canActivate(contextFor(request))).resolves.toBe(true);
    expect(request.principal?.tenantId).toBe('tenant-1');
  });

  it('rejects a missing token', async () => {
    await expect(guard.canActivate(contextFor({ headers: {}, cookies: {} }))).rejects.toThrow(
      UnauthorizedException,
    );
  });

  it('rejects a tampered token', async () => {
    const request: Partial<AuthenticatedRequest> = {
      headers: { authorization: `Bearer ${await validToken()}x` },
      cookies: {},
    };

    await expect(guard.canActivate(contextFor(request))).rejects.toThrow(UnauthorizedException);
  });
});
