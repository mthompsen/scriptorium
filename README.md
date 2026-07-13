# Scriptorium

Enterprise knowledge intelligence platform: ingests an organization's
documents, builds a hybrid vector index and a knowledge graph over them, and
answers questions through a tool-using AI agent with grounded, cited answers.
Multi-tenant, role-based, fully audited.

**Authoritative spec:** [docs/DESIGN.md](docs/DESIGN.md) — including the
requirements traceability matrix (Section 2) and the milestone plan
(Section 15). Current status: **M0 (scaffolding)**.

## Quickstart (laptop mode — no cloud account)

Prerequisite: Docker Desktop.

```sh
docker compose -f infra/docker/docker-compose.yml up -d --build
# or, with make:  make up
```

This starts five stub services (frontend :3000, BFF :3001, ingestion :8001,
agent :8002, retrieval :8080) plus Postgres, MongoDB, Redis, OpenSearch,
Neo4j, and Ollama. Every service exposes `/health` (frontend: `/api/health`).
See [docs/runbook.md](docs/runbook.md) for operations.

## Layout

| Path | What |
|---|---|
| `frontend/` | Next.js + React + TS web app |
| `services/bff` | NestJS edge API (auth, tenant scope, SSE) |
| `services/ingestion` | Flask write path (parse → chunk → embed → index) |
| `services/agent` | Flask reason path (tool-using agent loop) |
| `services/retrieval` | Spring Boot read path (hybrid search + graph) |
| `packages/` | Shared LLM adapters, OpenAPI contracts, UI components |
| `infra/` | Docker, Terraform, Kubernetes, GitOps |
| `docs/` | Design, ADRs, backlog, eval, security, runbook |
