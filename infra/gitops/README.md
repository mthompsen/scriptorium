# infra/gitops

Argo CD `Application` manifests (DESIGN.md Section 14.4).

- `app-staging.yaml` — auto-synced (prune + self-heal) from
  `infra/k8s/overlays/staging`. The `gitops-bump` CI job rewrites that
  overlay's image tags to each `main` commit's signed images and commits
  back `[skip ci]`; Argo CD reconciles the cluster to match — deployment as
  a Git operation.
- `app-prod.yaml` — manual sync; prod is a deliberate promotion.

Apply these to a cluster running Argo CD (`kubectl apply -f infra/gitops`).
The signed-image admission policy is `infra/k8s/policy/`. Live Argo CD
reconciliation awaits a persistent cluster (ADR-0007); the Kustomize sources
Argo CD points at are validated against a real API server (kind) in M5.

