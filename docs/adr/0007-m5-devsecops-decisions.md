# ADR-0007: M5 DevSecOps — signing, registries, scanner gates, and honest limits

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

M5 (DESIGN.md Sections 12, 14, 15) adds the security pipeline with a
findings gate, Kubernetes manifests, and GitOps. Several mechanics are
unspecified, and two spec items collide with the realities of a private
repository and a single-developer environment. The standing triage rule for
this milestone: findings are fixed or explicitly waived with recorded
reasoning — the gate is never made green by disabling scans, lowering
thresholds, or blanket ignores.

## Decision

1. **Registry and signing:** images push to GHCR (`ghcr.io/mthompsen/
   scriptorium-*`) on `main`, signed with **cosign keyless** (GitHub OIDC
   `id-token`). Keyless avoids key custody entirely; the tradeoff is that
   signature metadata (image digest, workflow identity) lands in the public
   Rekor transparency log, which is acceptable for this project.
2. **Findings gate severities:** Trivy gates on **HIGH and CRITICAL**
   (dependency and image scans, `--exit-code 1`); Semgrep gates on **ERROR**
   severity with the `p/default` community ruleset plus custom rules in
   `.semgrep.yml`; gitleaks gates on any finding. Waivers live in
   `.trivyignore` / rule-level ignores with an inline justification and, for
   anything non-trivial, a paragraph here or in `docs/security.md`.
3. **CodeQL** requires GitHub Advanced Security on private repositories.
   The workflow is committed but gated on repository visibility
   (`github.event.repository.private == false`), so it activates the moment
   the repo goes public instead of failing red or being silently omitted.
   Semgrep carries SAST until then. This is a documented limitation, not a
   waiver of SAST.
4. **Azure DevOps mirror:** `azure-pipelines.yml` is authored to mirror the
   GitHub Actions stages, but there is no ADO organization to execute it.
   "Green" for the mirror therefore means authored and schema-valid;
   the executed pipeline of record is GitHub Actions. Recorded in the
   backlog as an environment gap, not silently glossed.
5. **Signed-image admission:** a Kyverno `ClusterPolicy` in
   `infra/k8s/policy/` verifies cosign signatures for staging/prod
   namespaces. The dev overlay uses locally built images (no registry pull,
   no signature) — enforcing admission there would only test the mock.
6. **GitOps loop:** on `main`, CI bumps the image tags in
   `overlays/staging` via `kustomize edit set image` and commits with
   `[skip ci]`; Argo CD `Application` manifests reconcile from Git. Argo CD
   itself is exercised against a local cluster when one is available;
   otherwise the manifests are validated with `kustomize build` and
   documented as awaiting a cluster.

## Consequences

Keyless signing binds trust to the GitHub workflow identity — appropriate
here; an enterprise deployment would likely pin to an internal OIDC issuer
or managed keys. Visibility-gating CodeQL means SAST depth is Semgrep-bound
while private. The ADO mirror risks drifting from the Actions pipeline; the
mirror is one file and reviewed whenever the Actions workflow changes.
