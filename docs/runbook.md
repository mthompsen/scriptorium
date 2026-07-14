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

First start pulls the local models (~2.3 GB: `nomic-embed-text` +
`llama3.2:3b`) into the ollama volume via the `ollama-init` one-shot;
subsequent starts are instant. Answers run on CPU and can take up to a
minute. `scripts/run-eval.ps1` reproduces the numbers in `docs/eval.md`.

Graph extraction (M4) runs per chunk during ingestion on the local model and
adds minutes per document on CPU; set `GRAPH_EXTRACTION=off` to skip it.
The explorer lives at http://localhost:3000/graph; the Neo4j browser at
http://localhost:7474 (neo4j / scriptorium-dev).

An end-to-end API smoke test lives at `scripts/e2e-smoke.ps1`
(login → upload → status → chat → authz check).

### Browser e2e (Playwright, M7)

The journey suite lives in `e2e/` and runs against the started compose
stack (not in CI — ADR-0009):

```sh
cd e2e
npm install && npx playwright install chromium   # first time
npm test
```

Eight tests: login → upload → cited chat answer (slow: CPU inference),
graph explorer, legacy console (auth, JSP render, jQuery refresh), and an
axe-core accessibility gate on every modern page. README screenshots can be
regenerated with `SCREENSHOTS=1 npx playwright test tests/screenshots.spec.ts`.

### Legacy admin console (M7)

http://localhost:8080/legacy/admin/ — HTTP Basic, dev defaults
`admin` / `scriptorium-dev` (`LEGACY_ADMIN_USER` / `LEGACY_ADMIN_PASSWORD`
in `.env`). Read-only per-tenant corpus and graph statistics served as JSP
by the retrieval service. In Kubernetes the service is ClusterIP-only;
reach the console via `kubectl port-forward svc/retrieval 8080:8080`.

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

## Cloud (`infra/terraform`)

The AWS stack (VPC, EKS, RDS Postgres, OpenSearch, S3/SQS/Lambda serverless
ingestion, Bedrock IAM) is **authored and validated but not deployed** — no
`terraform apply` has run against real AWS (ADR-0008). Costs are not incurred
until someone runs a cost-approved apply.

### What is validated vs deployed

| Check | How | Status |
|---|---|---|
| `terraform fmt` / `validate` | whole stack | ✅ clean |
| Checkov IaC security scan | whole stack | ✅ 140 passed, 0 failed, 19 justified skips (`docs/security-findings.md`) |
| Serverless path (S3 → Lambda → SQS) | **LocalStack apply + real S3 upload → SQS message** | ✅ proven end to end, zero cost |
| `terraform apply`/`destroy` lifecycle | LocalStack (ingestion module) | ✅ 15 added / 16 destroyed |
| EKS / RDS / OpenSearch live behavior | — | ⛔ never applied; awaits a cost-approved AWS apply |

### Costless serverless proof (LocalStack)

```sh
docker run -d --name ls -p 4566:4566 -v /var/run/docker.sock:/var/run/docker.sock localstack/localstack:3.8
cd infra/terraform/localstack
docker run --rm --network host -v "$PWD/..:/tf" -w /tf/localstack hashicorp/terraform:latest init
docker run --rm --network host -v "$PWD/..:/tf" -w /tf/localstack hashicorp/terraform:latest apply -auto-approve
# upload to the raw bucket → the Lambda enqueues a job to the ingestion SQS queue
docker run --rm --network host -v "$PWD/..:/tf" -w /tf/localstack hashicorp/terraform:latest destroy -auto-approve
```

### Real AWS apply (⚠️ billable — do not run without cost approval)

```sh
cd infra/terraform
export TF_VAR_rds_password="$(aws secretsmanager get-secret-value ... )"  # never commit
terraform init
terraform plan            # review the plan first
terraform apply           # provisions billable resources (EKS, RDS, OpenSearch, NAT)
# teardown:
terraform destroy         # empty the raw-uploads bucket first (force_destroy is off by design)
```

**Rough monthly cost of a live apply** (us-east-1, on-demand, always-on):
EKS control plane ~$73 + 2× t3.large nodes ~$120 + RDS db.t3.medium Multi-AZ
~$120 + OpenSearch 2× t3.medium.search ~$100 + 1 NAT gateway ~$32 + storage/
data ≈ **$450–550/month**. Destroy when idle; the stack is designed to be
fully `terraform destroy`-able.
