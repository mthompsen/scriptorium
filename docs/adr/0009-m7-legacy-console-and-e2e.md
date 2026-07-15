# ADR-0009: M7 — legacy console packaging, console security, and the e2e gate

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

M7 (ARCHITECTURE.md Section 15) adds the JSP + jQuery + Bootstrap legacy admin
console to the Spring Boot retrieval service, an accessibility and
responsive pass, Playwright end-to-end journeys, and the reviewer-facing
README. The spec fixes the console's location (`src/main/webapp/`, Section 6)
and its intent (honest mixed-technology integration, Section 10) but leaves
packaging, authentication, scope, and where e2e executes unspecified.

## Decision

1. **War packaging (`bootWar`), not the executable-jar JSP workaround.**
   JSP does not work from an executable jar; the two options were the
   undocumented `META-INF/resources` trick or Spring Boot's documented
   war path. War packaging follows the spec's `src/main/webapp/` layout and
   the supported route. Two non-obvious mechanics, recorded because they cost
   real debugging: the deployed artifact **must keep the `.war` extension**
   (Boot only exposes the archive's webapp content as the servlet document
   root for `*.war` files — renamed to `app.jar` the console 404s), and
   Tomcat 10.1's EL 5.0 cannot resolve Java record components as bean
   properties, so the JSPs call record accessors explicitly
   (`${t.tenantId()}`).

2. **Console scope: read-only corpus and tenant statistics.** The retrieval
   service owns no data; mutations (document delete, re-ingest, user
   management) belong to the services that own those stores (ingestion, BFF).
   The console surfaces per-tenant chunk counts (OpenSearch), entity/relation
   counts (Neo4j), and a per-document drill-down — real administration
   visibility without inventing a second write path. New read-only ports
   (`CorpusAdminPort`, `GraphAdminPort`) keep the retrieval-path interfaces
   segregated.

3. **Security split (Section 12).** The console is human-facing, so
   `/legacy/admin/**` requires HTTP Basic (credentials via
   `LEGACY_ADMIN_USER`/`LEGACY_ADMIN_PASSWORD`, BCrypt-encoded in memory)
   under a dedicated Spring Security filter chain. The internal REST API
   keeps its pre-M7 posture — unauthenticated inside the cluster network,
   tenant scope enforced upstream by the BFF — via a second `permitAll`
   chain with CSRF disabled, which is correct for a cookie-less
   service-to-service API and keeps the BFF's `POST /retrieve` working.
   In Kubernetes the service stays ClusterIP; the console is reachable only
   via port-forward (or the compose port in laptop mode).

4. **Assets via WebJars (Bootstrap 5.3, jQuery 3.7), not a CDN.** Laptop
   mode must work offline and CSP-clean. Bootstrap 5 + jQuery is a deliberate
   pair: 3.x/4.x would be more period-accurate but carry open XSS CVEs
   (e.g. CVE-2024-6531) that would trip the Trivy gate; jQuery remains
   genuinely load-bearing (AJAX refresh against the console's JSON API,
   client-side table filter), so the legacy-integration capability is genuine without shipping known-bad
   dependencies.

5. **E2e lives in `/e2e` and runs against the compose stack, not in CI.**
   Playwright journeys (login → upload → cited chat answer; graph explorer;
   legacy console; an axe-core accessibility gate failing on serious/critical
   violations) execute on a workstation against `make up`, like the eval.
   CI does not run them: the full stack needs a ~2.3 GB model pull and
   CPU LLM inference that a hosted runner cannot complete inside sane
   timeouts. This is the same honesty rule as ADR-0007/0008 — the suite is
   real and executed locally; where it runs is documented, not glossed.

## Consequences

The retrieval artifact is a war; anyone deploying it elsewhere must preserve
the extension. Console credentials are a single in-memory user — fine for a
demo surface, and stated as such; an enterprise deployment would put the
console behind SSO or drop it entirely. The e2e suite's chat journey is
hardware-bound (minutes, not seconds) and sized accordingly with long
timeouts. Record-accessor EL syntax is mildly unusual JSP; the alternative
(hand-written view beans) was more code for no reader benefit.
