# Security — threat model and control list

Scope and intent are defined in `docs/ARCHITECTURE.md` Section 12. This document
grows with the system; the full threat model and DevSecOps pipeline land in M5.

## Controls in place (M5) — DevSecOps pipeline

- SAST: Semgrep (`p/default` community + custom `.semgrep.yml` rules —
  parameterized-Cypher-only, no-tenant-from-request-body); CodeQL wired but
  visibility-gated (private-repo GHAS limit, ADR-0007).
- Dependency + container scanning: Trivy (HIGH/CRITICAL, `--ignore-unfixed`,
  gating) on lockfiles and every built image; Dependabot for update PRs.
- Secret scanning: gitleaks in CI and as a pre-commit hook.
- SBOM: Syft per image, published as a build artifact.
- Image signing: cosign keyless (GitHub OIDC); Kyverno admission policy
  verifies signatures for staging/prod.
- Findings gate fails CI on any HIGH/CRITICAL (Trivy), ERROR (Semgrep), or
  secret (gitleaks). The full triage of the first scan pass — every finding
  fixed, zero waivers — is in `docs/security-findings.md`.
- Note: retrieval runs Spring Boot 3.5.16 (minor bump from the Section 5
  baseline of 3.4.x), taken to clear Tomcat/Netty/Jackson CVEs.

## Controls in place (M4) — graph layer

- All Cypher is parameterized with explicit `tenant_id` parameters on both
  the Python (ingestion) and Java (retrieval) sides — no string-built
  queries (Section 8.5).
- The `query_knowledge_graph` tool takes an entity name only; graph queries
  are fixed templates, never model-supplied Cypher (Section 9.2).
- Graph outages degrade retrieval to hybrid-only with an explicit mode flag
  rather than failing (Section 11).

## Controls in place (M3) — GenAI guardrails (Section 9.2)

- Bounded agent loop: hard step budget (`AGENT_MAX_STEPS`) and wall-clock
  timeout (`AGENT_TIMEOUT_S`); breaching either forces a refusal recorded as
  a `refused` run.
- Tool allowlist: four typed tools; inputs validated against JSON Schemas
  (`additionalProperties: false`) before execution; unknown tools rejected.
- Tenant scope injected server-side into every tool call — the model cannot
  name or widen a tenant.
- Prompt-injection posture: retrieved content is delimited and framed as
  data; tools take no free-form executable input.
- Output validation: citations must resolve to chunks surfaced in the same
  run; unresolved citations are stripped and counted; runs that retrieved
  nothing refuse rather than answer from parametric memory.
- Pluggable PII filter on the answer path (`PII_FILTER=basic|off`).
- Observability: every run and step traced to `agent_runs`/`agent_steps`
  with token counts and latency (Section 9.5).

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
