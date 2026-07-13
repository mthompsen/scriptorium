# Runbook — local and cloud operations

## Local (laptop mode)

Prerequisites: Docker Desktop running. No cloud account needed.

```sh
# from the repo root — starts all 5 services + 6 data/AI containers
docker compose -f infra/docker/docker-compose.yml up -d --build

# check health (all should report healthy once started)
docker compose -f infra/docker/docker-compose.yml ps
```

On hosts with `make`, `make up` / `make down` wrap the same commands. On
native Windows, invoke `docker compose` directly as above.

Demo login (dev-only, seeded by migration 0004): `demo@scriptorium.local` /
`scriptorium-demo` at http://localhost:3000/login.

An end-to-end API smoke test lives at `scripts/e2e-smoke.ps1`
(login → upload → status → chat → authz check).

Service endpoints once up:

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 (health: `/api/health`) |
| BFF | http://localhost:3001/health |
| Ingestion | http://localhost:8001/health |
| Agent | http://localhost:8002/health |
| Retrieval | http://localhost:8080/health |

Data stores: Postgres :5432, MongoDB :27017, Redis :6379, OpenSearch :9200,
Neo4j :7474 (browser) / :7687 (bolt), Ollama :11434.

Tear down (removes containers, keeps volumes): `docker compose -f
infra/docker/docker-compose.yml down`. Add `-v` to drop data volumes.

## Cloud

Arrives in M6 (Terraform apply/destroy for the AWS stack). This section will
document the full lifecycle then.
