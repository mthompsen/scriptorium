# M5 security findings ledger

Every finding from the initial DevSecOps scan pass (2026-07-14), how it was
triaged, and the outcome. The standing rule for M5: findings are fixed or
explicitly waived with recorded reasoning — never suppressed to make the gate
pass. **Outcome: every finding was a real fix. Zero waivers.**

Scanners: Trivy (dependency + image, HIGH/CRITICAL, `--ignore-unfixed`),
Semgrep (`p/default` community + custom `.semgrep.yml`), gitleaks (full
history).

## Secret scan — gitleaks

| Result | 63 commits scanned, **no leaks**. |

The only credential-shaped strings are the dev-only compose defaults in
`.env.example`, allowlisted in `.gitleaks.toml` with justification.

## SAST — Semgrep

Community `p/default` at ERROR severity: **0 findings**. At WARNING (below the
gate, reviewed anyway): 8, all fixed rather than left:

| Finding | Count | Handling |
|---|---|---|
| `insecure-hash-algorithm-sha1` — `graph_store.py` entity id | 1 | **Fixed** — switched to SHA-256 (truncated). It's a content-address, not a security hash, but the deprecated primitive is avoided; ids regenerate per-ingest. |
| `github-actions-mutable-action-tag` — `ci.yml` | 7 | **Fixed** — pinned all GitHub Actions to full commit SHAs (supply-chain hardening). |

Custom rules (`.semgrep.yml`): parameterized-Cypher-only and
no-tenant-from-request-body. **0 findings** — the codebase already complies.

## Dependency scan — Trivy (source)

`frontend` and `services/bff` lockfiles: **0 HIGH/CRITICAL**.

## Image scan — Trivy (before → after)

| Image | Before | After | Handling |
|---|---|---|---|
| agent | 0 | 0 | — |
| ingestion | 0 | 0 | — |
| retrieval | **29** | **0** | See below |
| bff | **2** | **0** | See below |
| frontend | **2** | **0** | See below |

### retrieval (29 → 0)

- **22 Java findings** (Tomcat criticals CVE-2026-41293/43512/43515,
  plus tomcat/netty/jackson/spring HIGH). **Fixed** by bumping Spring Boot
  `3.4.5 → 3.5.16`; the Boot BOM pulled patched Tomcat, Netty, Jackson, and
  Spring versions. (Minor-version deviation from the Section 5 baseline of
  Boot 3.4.x, taken for security per Section 5's allowance — noted here and
  in `docs/security.md`.) All 14 retrieval tests, incl. Pact verification,
  still pass.
- **7 Go-stdlib findings in `/usr/bin/pebble`** — a Let's Encrypt ACME
  **test server** binary shipped in the `eclipse-temurin:21-jre` base image
  that this Java service never invokes. **Fixed** by `rm -f /usr/bin/pebble`
  in the Dockerfile: removes unused attack surface, not just the finding.

### bff and frontend (2 → 0 each)

- `picomatch@4.0.3` (CVE-2026-33671) and `sigstore@3.1.0` (CVE-2026-48815)
  were **not application dependencies** — they live in
  `/usr/local/lib/node_modules/npm/`, i.e. npm's own vendored transitive
  deps bundled inside the `node:22-alpine` base image. The runtime containers
  run `node dist/main.js` / `node server.js` and never invoke npm.
  **Fixed** by removing the npm CLI from the runtime stage
  (`rm -rf /usr/local/lib/node_modules/npm …`): unused attack surface gone,
  same rationale as pebble.

## IaC scan — Checkov (M6 Terraform)

Initial scan: **77 passed, 26 failed**. After honest triage: **140 passed,
0 failed, 19 skips — every skip carries an inline `#checkov:skip=…:reason`.**

Fixed (real hardening): RDS IAM auth + Performance Insights (CMK) + CloudWatch
log exports + enhanced monitoring + copy-tags + query logging + `rds.force_ssl`;
OpenSearch audit/slow logs + fine-grained access control + CMK at-rest;
a customer-managed KMS key for RDS PI / log group / OpenSearch; Lambda DLQ +
X-Ray tracing + reserved concurrency; S3 access-logging bucket + lifecycle +
abort-incomplete-uploads on both buckets; security-group rule descriptions +
scoped egress.

Waived with inline justification (not gamed):

| Check(s) | Reason |
|---|---|
| CKV_TF_1 (×3) | Registry modules pinned by version constraint; integrity via `.terraform.lock.hcl` checksums. |
| CKV_AWS_109/111/356 | KMS key-policy resource **must** be `"*"` (self-referential to the attached key) — canonical AWS pattern, not an unconstrained grant. |
| CKV_AWS_117 | Ingestion Lambda uses only S3/SQS AWS APIs; VPC attachment adds NAT cost for no security benefit. |
| CKV_AWS_144 | Single-region demo; S3 cross-region replication doubles storage cost. |
| CKV_AWS_272 | Lambda code-signing (AWS Signer) out of scope for a demo trigger. |
| CKV_AWS_173 | Only Lambda env var is a non-secret queue URL. |
| CKV2_AWS_59 / CKV_AWS_318 | Dedicated OpenSearch master nodes ~triple cost; non-prod scale. |
| CKV_AWS_18 / CKV2_AWS_61 / CKV2_AWS_62 (log bucket) | It IS the access-log target; self-logging would recurse. |

## SAST — CodeQL (M7, first run after going public)

CodeQL was authored in M5 but gated to public repos (GitHub Advanced
Security is free only on public repos; ADR-0007). The repository went public
on 2026-07-14 and CodeQL ran for the first time on commit `b2ed079`, all
three legs succeeding with `build-mode: none` (buildless extraction) —
java-kotlin 76 rules, javascript-typescript 87, python 43. Unlike the other
scanners, **CodeQL reports to GitHub code scanning and does not gate the
pipeline.** Triage of its alerts:

| # | Alert | Severity | Location | Status |
|---|---|---|---|---|
| 2 | `java/spring-disabled-csrf-protection` | error | `services/retrieval/.../legacyadmin/LegacyAdminSecurityConfig.java:45` | **Dismissed — false positive** |
| 1 | `js/xss-through-exception` | warning | `services/bff/src/chat/chat.controller.ts:67` | **Fixed in code; alert dismissed** |

- **#2 CSRF (dismissed, false positive).** The `csrf.disable()` is on the
  internal service-to-service chain (`@Order(2)`): `permitAll()`, no cookies,
  no sessions. CSRF requires ambient browser authority (a cookie/session the
  browser attaches automatically); an unauthenticated, credential-less
  endpoint has none, and an attacker gains nothing a direct request wouldn't.
  The human-facing console chain (`@Order(1)`, HTTP Basic, GET-only) leaves
  CSRF enabled. Dismissed in code scanning with this reasoning (ADR-0009).
  Revisit if the internal API ever gains authentication.
- **#1 XSS through exception (fixed).** `chat.controller.ts` wrote a caught
  exception's `.message` into an SSE `error` event. The XSS *classification*
  is a CodeQL modeling limitation — it treats `res.write` as an HTML sink,
  whereas the actual response is `Content-Type: text/event-stream` (not
  `text/html`), the payload is JSON-encoded (`JSON.stringify({ message })`),
  and the route is a POST; the browser's stream reader receives it as data,
  not markup. But the underlying pattern was a genuine
  **information-disclosure** risk: the `catch` was unbounded, so beyond our
  own server-authored `HttpException` messages it would also surface library
  internals — e.g. a V8 `JSON.parse` `SyntaxError` whose `.message` embeds a
  snippet of a malformed SSE frame, and those frames carry LLM-generated,
  user-influenced output. **Fixed** rather than dismissed: the catch now
  surfaces `.message` only for our own `instanceof HttpException` (safe
  constants) and falls back to the generic `'stream failed'` for everything
  else, with the original error logged server-side so debuggability is kept.
  **Both facts hold:** the code was fixed (commit `6143072`), *and* the alert
  was dismissed as "won't fix" — CodeQL re-flagged the narrowed path on the
  post-fix commit `dd1d56e` (its taint model still treats `res.write` of any
  exception `.message` as an HTML sink, even though this response is
  `text/event-stream`, JSON-encoded, over POST, and now only carries
  server-authored `HttpException` constants). The dismissal records that the
  remaining match is the modeling limitation, not a live risk.

## Gate configuration

- Trivy: HIGH,CRITICAL, `--ignore-unfixed`, `--exit-code 1`.
- Semgrep: ERROR severity (`p/default` + custom), `--error`.
- gitleaks: any finding fails.
- CodeQL: reports to GitHub code scanning; does not gate CI.

No thresholds were lowered and no scans disabled to reach a green gate. The
`.gitleaks.toml` allowlist (dev-only `.env.example`) is the only suppression,
and it predates M5 with its own justification.
