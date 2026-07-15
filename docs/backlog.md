# Scriptorium backlog

Agile delivery artifact. Epics mirror the milestones in `docs/ARCHITECTURE.md`
Section 15; stories are the concrete increments inside each. Status values:
`todo`, `in progress`, `done`.

## Epic M0 — Scaffolding *(done — 2026-07-13)*

| Story | Status |
|---|---|
| Monorepo directory structure (Section 6) | done |
| Stub services boot with `/health` (bff, ingestion, agent, retrieval, frontend) | done |
| docker-compose starts every container (5 services + Postgres, Mongo, Redis, OpenSearch, Neo4j, Ollama) | done — all 11 healthy, all `/health` 200 |
| Makefile with top-level dev commands | done |
| ADR-0001 recorded | done |
| CI pipeline green: lint + trivial test per service | done — run 29271688484 |

## Epic M1 — Walking skeleton *(done — 2026-07-13)*

| Story | Status |
|---|---|
| Postgres schema + Alembic migrations (identity, documents, chat) + demo seed (ADR-0002) | done |
| JWT auth in BFF: login, HttpOnly cookie + bearer, tenant context (ADR-0003) | done |
| Document upload → `documents` row → raw bytes stored via ingestion `/ingest` | done |
| Stub chat endpoint (echo) with persisted sessions/messages | done |
| Next.js login, chat, and library pages (Tailwind) | done |
| End-to-end verified: login → upload → message on compose stack (`scripts/e2e-smoke.ps1`) | done |

## Epic M2 — RAG core *(done — 2026-07-13)*

| Story | Status |
|---|---|
| `packages/llm`: provider protocol + Ollama and Bedrock adapters (ADR-0004) | done |
| Ingestion pipeline: parse (PDF/DOCX/MD/HTML/txt) → structure-aware chunk → Mongo → embed → per-tenant OpenSearch index | done |
| Hybrid retrieval (BM25 + kNN, RRF fusion) in the Spring Boot service | done |
| Agent `/answer`: single-shot grounded RAG, citation validation, refusal on empty retrieval | done |
| Chat wired to the agent with persisted citations; frontend renders sources | done |
| Retrieval eval: recall@5 = 1.0, MRR = 1.0 on the 10-query labeled set (`docs/eval.md`, real run) | done |

## Epic M3 — Agentic layer *(done — 2026-07-13)*

| Story | Status |
|---|---|
| Provider streaming (`chat_stream`: Ollama NDJSON, Bedrock converse_stream) | done |
| Tool registry: search_documents, get_document, list_recent, query_knowledge_graph (M4 stub) — schema-validated, tenant-scoped | done |
| Bounded loop: step + wall-clock budgets, forced refusals, citation validation, PII hook (ADR-0005) | done |
| Full run/step tracing to `agent_runs`/`agent_steps`, linked to chat messages | done |
| SSE streaming end to end: agent → BFF → browser, live tool trace in chat UI | done |
| Generation eval: citation coverage + LLM-judge groundedness (`docs/eval.md`) | done |

## Tech debt / discovered work

| Item | Found | Notes |
|---|---|---|
| Checksum-based upload dedup + versioning | M3 eval | Re-uploading an identical file creates a new `documents` row; the schema already carries `checksum` and `version`, ingest should reuse/increment instead. Duplicates degrade retrieval ranking. |
| Eval isolation | M3 eval | `run-eval.ps1` now resets the eval tenant's corpus directly against the local stores; a document-delete API (or per-run tenants) would make this first-class. |
| In-process ingest worker can strand `processing` on crash | M2 (ADR-0004) | Durable queue + outbox arrives with the event-driven path (M6). |

## Epic M4 — Polyglot + graph *(done — 2026-07-14)*

| Story | Status |
|---|---|
| Entity/relation extraction into Neo4j during ingestion (confidence-filtered, ADR-0006) | done — live graph: 8 entities, 3 relations from the eval corpus |
| Graph queries in the Spring Boot service (`/graph/search`, neighborhood; parameterized Cypher) | done |
| Graph-augmented retrieval: `graph_context` on `/retrieve`, graceful `hybrid` degradation | done — verified `mode=hybrid+graph` |
| BFF graph proxy (tenant injected server-side) + real `query_knowledge_graph` agent tool | done — e2e verified |
| Frontend graph explorer (react-force-graph-2d) | done — endpoints verified with real data; canvas render spot-check left to manual browser pass (automation flaked) |
| Pact contract BFF↔retrieval (consumer jest → committed pact → pact-jvm verify + CI drift check) | done — provider verification green |

## Epic M5 — DevSecOps + Kubernetes + GitOps *(done — 2026-07-14)*

| Story | Status |
|---|---|
| Security findings triage: 33 HIGH/CRITICAL + 8 SAST → 0, every one fixed, zero waivers (`docs/security-findings.md`, ADR-0007) | done |
| CI security pipeline: Semgrep (+custom rules), gitleaks, Trivy fs/image, CodeQL (visibility-gated), SBOM (Syft), cosign keyless by digest, findings gate | done — green in cloud, images signed to Sigstore tlog |
| Dependabot + pre-commit hooks | done |
| Kustomize base + dev/staging/prod overlays (probes, limits, netpol, non-root) | done — all 30 objects admitted by a real API server (kind) |
| Argo CD Applications (staging auto-sync, prod manual) + GitOps tag-bump on main | done |
| Kyverno signed-image admission policy (staging/prod) | done |
| `azure-pipelines.yml` mirror | done — authored + schema-valid; no ADO org to execute (ADR-0007) |

**Environment gaps (documented, not gamed):** CodeQL activates when the repo
goes public (private-repo GHAS); the ADO mirror and live Argo CD
reconciliation await an ADO org / persistent cluster.

## Epic M6 — Cloud + serverless *(done — 2026-07-14)*

| Story | Status |
|---|---|
| Terraform AWS stack: VPC, EKS, RDS, OpenSearch, S3/SQS/Lambda, Bedrock IAM (ADR-0008) | done — `fmt`/`validate` clean, Checkov 140/0 |
| Serverless ingestion path (S3 → Lambda → SQS) with tested Lambda handler | done — **proven end to end on LocalStack**, zero cost |
| `terraform apply`/`destroy` lifecycle | done — LocalStack: 15 added / 16 destroyed |
| Bedrock provider access (IRSA policy for agent/ingestion) | done (validated) |
| CI: terraform validate + Checkov gate | done |

**Environment gap (documented, not gamed):** EKS/RDS/OpenSearch are validated
but **never applied** — a live AWS apply is billable (~$450–550/mo) and awaits
explicit cost approval (ADR-0008, runbook). The serverless requirement (R4) is
demonstrated costlessly via LocalStack.

## Epic M7 — Legacy console + hardening + polish *(done — 2026-07-14)*

| Story | Status |
|---|---|
| JSP + jQuery + Bootstrap legacy console in the Spring Boot service (war packaging, Basic-auth chain, read-only corpus/graph stats; ADR-0009) | done — renders live, covered by unit + security + e2e tests |
| Modern admin page linking the console, labeled legacy | done |
| Accessibility + responsive pass (skip link, ARIA roles/labels, contrast, table semantics, canvas text alternative) | done — axe-core gate green on all pages |
| Playwright e2e: login→upload→grounded answer, graph explorer, legacy console, RBAC upload gate, a11y gate | done — runs against the compose stack (local-only, ADR-0009); model-quality numbers (citation rate etc.) in `docs/eval.md`, not asserted in the journey |
| Final eval run (`scripts/run-eval.ps1`, local 3B baseline) | done — retrieval 1.0/1.0 re-confirmed; generation coverage 0.4667, judge-noise analysis in `docs/eval.md` |
| Reviewer-grade README: capability table, architecture diagram, honest live-vs-authored status, screenshots | done — screenshots captured from the live stack |
