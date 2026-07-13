# Security — threat model and control list

Scope and intent are defined in `docs/DESIGN.md` Section 12. This document
grows with the system; the full threat model and DevSecOps pipeline land in M5.

## Controls in place (M1)

- AuthN: JWT issued by the BFF (30-min expiry), bcrypt password hashes.
  Browser flow uses an HttpOnly SameSite=Lax cookie; API clients use
  `Authorization: Bearer` (ADR-0003). Login returns the same error for
  unknown user and wrong password (no account enumeration).
- AuthZ/tenancy: tenant scope derived server-side from the JWT via a
  request-scoped `TenantContext`; every SQL query filters by `tenant_id`;
  chat sessions additionally scoped to the owning user.
- Input validation: DTO validation (class-validator, whitelist +
  forbidNonWhitelisted) in the BFF; UUID/form validation in ingestion.
- Parameterized queries only (node-postgres and psycopg placeholders).
- Upload limits: 20 MB request cap; MIME allowlist (PDF, DOCX, MD, HTML, txt).
- CORS restricted to the frontend origin with credentials.

## Controls in place (M0)

- Secrets: no secrets in code; local config via environment with committed
  `.env.example` defaults only (dev-only credentials, clearly labeled).
- Containers: every service image is multi-stage and runs as a non-root user.
- Line of defense placeholders: `.semgrep.yml` and `.gitleaks.toml` exist at
  the root; the scanning gate is wired into CI in M5.

## Planned (per milestone)

- M1: JWT auth, server-side tenant scoping, DTO/schema validation at the edge.
- M3: GenAI guardrails — tool allowlist, prompt-injection handling, citation
  validation, step/time budgets (Section 9.2).
- M5: SAST (Semgrep, CodeQL), dependency + container scanning (Trivy),
  secret scanning (gitleaks), SBOM (Syft), image signing (cosign), findings
  gate failing the pipeline on high severity.
