import type { Request } from 'express';

/** Authenticated identity derived server-side from the JWT — never from client input. */
export interface Principal {
  userId: string;
  tenantId: string;
  email: string;
  roles: string[];
}

export interface AuthenticatedRequest extends Request {
  principal: Principal;
}

/** Shape of the JWT payload the BFF signs and verifies. */
export interface JwtPayload {
  sub: string;
  tenant_id: string;
  email: string;
  roles: string[];
}
