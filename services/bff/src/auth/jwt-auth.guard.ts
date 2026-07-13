import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';

import type { AuthenticatedRequest, JwtPayload } from './principal';

export const ACCESS_TOKEN_COOKIE = 'st_access';

/**
 * Accepts the JWT from the HttpOnly cookie (browser flow) or the
 * Authorization: Bearer header (API clients) — ADR-0003.
 */
@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(private readonly jwtService: JwtService) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<AuthenticatedRequest>();
    const token = this.extractToken(request);
    if (!token) {
      throw new UnauthorizedException('Missing access token');
    }
    let payload: JwtPayload;
    try {
      payload = await this.jwtService.verifyAsync<JwtPayload>(token);
    } catch {
      throw new UnauthorizedException('Invalid or expired access token');
    }
    request.principal = {
      userId: payload.sub,
      tenantId: payload.tenant_id,
      email: payload.email,
      roles: payload.roles,
    };
    return true;
  }

  private extractToken(request: AuthenticatedRequest): string | undefined {
    const cookies = request.cookies as Record<string, string> | undefined;
    if (cookies?.[ACCESS_TOKEN_COOKIE]) {
      return cookies[ACCESS_TOKEN_COOKIE];
    }
    const header = request.headers.authorization;
    if (header?.startsWith('Bearer ')) {
      return header.slice('Bearer '.length);
    }
    return undefined;
  }
}
