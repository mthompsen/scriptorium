# ADR-0010: RBAC — one coarse role gate at the BFF, not fine-grained service checks

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

ARCHITECTURE.md Section 11 promises "RBAC with roles owner/admin/member/
viewer. Coarse checks at the BFF, fine-grained checks in services where
needed." The roles existed as data — seeded in Postgres (`roles`,
`user_roles`) and carried as JWT claims — but nothing enforced them: every
authenticated user had identical access within their tenant. A guard that
gates nothing is scaffolding, so either RBAC gets enforced or the claim gets
cut. This ADR records enforcing it, and the honest scope of that enforcement.

Section 11 names the four roles without defining per-role semantics, so a
reading has to be chosen and stated.

## Decision

1. **Conventional role semantics.** owner ⊇ admin ⊇ member ⊇ viewer, with
   **viewer = read-only**. Recorded here because the spec only names the
   roles; this is an interpretation, not a spec quote.

2. **One coarse gate at the BFF: document upload.** `POST /documents` is
   restricted to owner/admin/member via `@Roles(...)` + `RolesGuard`; viewer
   is denied (403). Every other authenticated endpoint is unchanged — a
   viewer reading the corpus, listing documents, and asking questions is
   reading. This is the smallest gate that makes "coarse checks at the BFF"
   true against a real endpoint, and it is the only BFF mutation that isn't
   itself a read.

3. **No fine-grained service checks — and the doc claim is scoped to match.**
   The internal services (ingestion, agent, retrieval) perform no per-role
   checks; they are trusted on the cluster network with tenant scope injected
   by the BFF. Section 11's "fine-grained checks in services where needed"
   was cut rather than left as an aspiration dressed as a control.

4. **Guard ordering, never global.** Applied as `@UseGuards(JwtAuthGuard,
   RolesGuard)` in that order. `RolesGuard` reads roles from the
   request-scoped `TenantContext` that `JwtAuthGuard` populates. It is
   deliberately **not** an `APP_GUARD`: global guards run before controller
   guards in Nest, so the principal (and thus the role list) would not yet be
   populated, and the gate would read an empty list. A handler with no
   `@Roles` metadata is unrestricted for any authenticated user, so the guard
   gates only endpoints that opt in.

5. **Proven, not asserted.** A viewer user is seeded in the demo tenant
   (migration 0007, `viewer@scriptorium.local`). An e2e test proves the
   discriminating behavior — viewer gets 403 on `POST /documents` and 200 on
   `GET /documents`, with an owner control that upload is not blocked — plus
   guard unit tests. Without the negative test, nobody could tell the guard
   does anything.

## Consequences

The RBAC claim is now true and narrowly scoped: role-based access control
exists and is enforced at exactly one coarse gate. Extending it (admin-only
management endpoints, per-role read scoping) is future work and would want
its own gates and lower-privilege seed users to be meaningful — a `RolesGuard`
with nothing to gate would be scaffolding again. The conventional role
semantics are an interpretation; if the product later defines different
semantics, this ADR is superseded rather than silently contradicted.
