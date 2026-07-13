# Scriptorium backlog

Agile artifact for R5. Epics mirror the milestones in `docs/DESIGN.md`
Section 15; stories are the concrete increments inside each. Status values:
`todo`, `in progress`, `done`.

## Epic M0 — Scaffolding *(in progress)*

| Story | Status |
|---|---|
| Monorepo directory structure (Section 6) | in progress |
| Stub services boot with `/health` (bff, ingestion, agent, retrieval, frontend) | in progress |
| docker-compose starts every container (5 services + Postgres, Mongo, Redis, OpenSearch, Neo4j, Ollama) | in progress |
| Makefile with top-level dev commands | todo |
| ADR-0001 recorded | done |
| CI pipeline green: lint + trivial test per service | todo |

## Epic M1 — Walking skeleton *(todo)*

JWT auth in BFF · Postgres schema + migrations · document upload creating a
`documents` row · stub chat endpoint · minimal Next.js login + chat pages.

## Epic M2 — RAG core *(todo)*

Ingestion pipeline (parse/chunk/embed/index) · hybrid retrieval · grounded
cited answers · LLM layer (Ollama + Bedrock adapters) · retrieval eval
(recall@k in `docs/eval.md`).

## Epic M3 — Agentic layer *(todo)*

Tool-use loop · tool set · guardrails · SSE streaming · full run/step tracing.

## Epic M4 — Polyglot + graph *(todo)*

Spring Boot retrieval over Neo4j · entity/relation extraction · graph explorer
UI · Pact contract tests BFF↔retrieval.

## Epic M5 — DevSecOps + Kubernetes + GitOps *(todo)*

Full security pipeline (SAST, dep/secret/container scans, SBOM, cosign) ·
Kustomize base + overlays · Argo CD · `azure-pipelines.yml` mirror.

## Epic M6 — Cloud + serverless *(todo)*

Terraform AWS stack · S3 → Lambda → SQS ingestion path · Bedrock provider.

## Epic M7 — Legacy console + hardening + polish *(todo)*

JSP/jQuery/Bootstrap legacy console · accessibility + responsive passes ·
Playwright e2e · final eval run · reviewer-grade README.
