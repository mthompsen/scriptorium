import { Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { compare } from 'bcryptjs';

import type { JwtPayload } from './principal';
import { UsersRepository } from './users.repository';

export interface LoginResult {
  accessToken: string;
  user: { id: string; email: string; tenantId: string; roles: string[] };
}

@Injectable()
export class AuthService {
  constructor(
    private readonly users: UsersRepository,
    private readonly jwtService: JwtService,
  ) {}

  async login(email: string, password: string): Promise<LoginResult> {
    const user = await this.users.findByEmail(email);
    // Same error for unknown user and wrong password — no account enumeration.
    if (!user || !(await compare(password, user.passwordHash))) {
      throw new UnauthorizedException('Invalid credentials');
    }
    const payload: JwtPayload = {
      sub: user.id,
      tenant_id: user.tenantId,
      email: user.email,
      roles: user.roles,
    };
    return {
      accessToken: await this.jwtService.signAsync(payload),
      user: { id: user.id, email: user.email, tenantId: user.tenantId, roles: user.roles },
    };
  }
}
