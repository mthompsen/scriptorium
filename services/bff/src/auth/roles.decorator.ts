import { SetMetadata } from '@nestjs/common';

/** Roles that satisfy a gate; a principal holding any one of them passes. */
export const ROLES_KEY = 'roles';

/**
 * Coarse role gate at the BFF (ARCHITECTURE.md Section 11). Section 11 names
 * owner/admin/member/viewer without per-role semantics, so the conventional
 * read applies: viewer is read-only. Annotate a handler with the roles
 * allowed to invoke it; handlers without @Roles are open to any
 * authenticated user. Enforced by RolesGuard.
 */
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);
