# ADR-0008: M6 cloud — Terraform structure, LocalStack proof, no live apply

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

M6 (ARCHITECTURE.md Sections 14.5, 15) provisions the AWS target — VPC, EKS, RDS
Postgres, OpenSearch, S3, SQS, Lambda, IAM, Bedrock access — with the
serverless ingestion path (S3 → Lambda → SQS → ingestion worker) as the R4
deliverable. The standing constraint for this milestone: author and validate
the infrastructure, but **do not run `terraform apply` against real AWS or
provision billable resources** without explicit approval and a cost estimate.
The spec itself anticipates this — "or LocalStack for a costless proof."

## Decision

1. **Two-tier structure.** The serverless ingestion path (S3, SQS, Lambda,
   IAM, bucket notification) lives in a self-contained
   `modules/ingestion/` module. The root stack composes it with the heavy
   managed infrastructure (VPC + EKS via community modules, RDS, OpenSearch,
   Bedrock IAM). A separate `localstack/` root instantiates **only** the
   ingestion module against LocalStack endpoints.

   Rationale: LocalStack (community) faithfully emulates S3/SQS/Lambda/IAM
   but not EKS/RDS/OpenSearch. Isolating the serverless path lets us
   **actually deploy and exercise it costlessly** — a real S3 upload firing
   the real Lambda enqueuing a real SQS message — while the managed tiers are
   validated statically.

2. **Validation tiers, stated honestly.**
   - `terraform fmt -check`, `terraform validate`, and a Checkov security
     scan run over the **entire** stack (no AWS creds needed).
   - `terraform plan` and `apply` run against **LocalStack** for the
     ingestion module — this is executed and asserted, not just planned.
   - EKS/RDS/OpenSearch are **validated but never applied** anywhere; a live
     `plan`/`apply` against AWS is deferred to an explicit, cost-approved
     decision. Every doc distinguishes "validated" from "deployed."

3. **Tooling via Docker** — `hashicorp/terraform`, `localstack/localstack`,
   `bridgecrew/checkov` images; no host installs, no ambient AWS credentials.
   The LocalStack root sets `access_key`/`secret_key` to `test` and points
   the provider at `http://localhost:4566`, with `skip_credentials_validation`
   so it can never reach real AWS.

4. **Bedrock** is access-not-provisioning: an IAM policy granting
   `bedrock:InvokeModel` on the Titan-embeddings and Claude model ARNs, which
   the EKS pods assume via IRSA. The `packages/llm` Bedrock adapter (M2)
   already speaks this API; M6 only wires the permission.

## Consequences

The serverless requirement (R4) is demonstrated end to end at zero cost.
The managed-infra HCL is real and reviewable but its live behavior is
unproven until someone runs a cost-approved apply — called out wherever it
matters. Community Terraform modules (VPC, EKS, RDS) keep the stack concise
and idiomatic at the cost of a module-download step during `init`.
