# infra/k8s

Kustomize `base/` plus `overlays/{dev,staging,prod}/` (ARCHITECTURE.md Section 14.3),
and a `policy/` Kyverno signed-image admission policy.

```sh
kubectl apply -k infra/k8s/overlays/dev      # or staging / prod
```

Base carries all 5 services + 6 stores with readiness/liveness probes,
resource requests+limits, non-root/read-only security contexts, and a
default-deny-plus-scoped-allow NetworkPolicy set. Overlays patch replicas,
resources, namespace, and image tags per environment. Every overlay is
validated against a real Kubernetes API server (kind) in M5 — all objects
admitted. Running the full workload set live awaits a persistent cluster
(ADR-0007).

