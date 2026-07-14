# Scriptorium backlog

Agile artifact for R5. Epics mirror the milestones in `docs/DESIGN.md`
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

## Epic M5 — DevSecOps + Kubernetes + GitOps *(todo)*

Full security pipeline (SAST, dep/secret/container scans, SBOM, cosign) ·
Kustomize base + overlays · Argo CD · `azure-pipelines.yml` mirror.

## Epic M6 — Cloud + serverless *(todo)*

Terraform AWS stack · S3 → Lambda → SQS ingestion path · Bedrock provider.

## Epic M7 — Legacy console + hardening + polish *(todo)*

JSP/jQuery/Bootstrap legacy console · accessibility + responsive passes ·
Playwright e2e · final eval run · reviewer-grade README.
