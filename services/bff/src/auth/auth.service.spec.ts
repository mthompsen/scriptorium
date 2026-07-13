import { UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { hash } from 'bcryptjs';

import { AuthService } from './auth.service';
import type { UsersRepository, UserWithRoles } from './users.repository';

const jwtService = new JwtService({ secret: 'test-secret', signOptions: { expiresIn: '5m' } });

const demoUser = async (): Promise<UserWithRoles> => ({
  id: 'user-1',
  tenantId: 'tenant-1',
  email: 'demo@scriptorium.local',
  passwordHash: await hash('correct-password', 4),
  roles: ['owner'],
});

describe('AuthService', () => {
  it('returns a signed token and the user on valid credentials', async () => {
    const user = await demoUser();
    const users = { findByEmail: jest.fn().mockResolvedValue(user) };
    const service = new AuthService(users as unknown as UsersRepository, jwtService);

    const result = await service.login('demo@scriptorium.local', 'correct-password');

    expect(result.user).toEqual({
      id: 'user-1',
      email: 'demo@scriptorium.local',
      tenantId: 'tenant-1',
      roles: ['owner'],
    });
    const payload = await jwtService.verifyAsync<{ sub: string; tenant_id: string }>(
      result.accessToken,
    );
    expect(payload.sub).toBe('user-1');
    expect(payload.tenant_id).toBe('tenant-1');
  });

  it('rejects a wrong password', async () => {
    const users = { findByEmail: jest.fn().mockResolvedValue(await demoUser()) };
    const service = new AuthService(users as unknown as UsersRepository, jwtService);

    await expect(service.login('demo@scriptorium.local', 'wrong-password')).rejects.toThrow(
      UnauthorizedException,
    );
  });

  it('rejects an unknown email with the same error (no account enumeration)', async () => {
    const users = { findByEmail: jest.fn().mockResolvedValue(undefined) };
    const service = new AuthService(users as unknown as UsersRepository, jwtService);

    await expect(service.login('nobody@scriptorium.local', 'whatever-password')).rejects.toThrow(
      'Invalid credentials',
    );
  });
});
