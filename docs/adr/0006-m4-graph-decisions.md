# ADR-0006: M4 graph — extraction, augmentation, contract testing, drivers

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

M4 (ARCHITECTURE.md Section 15) adds the knowledge graph: ingestion extracts
entities/relations into Neo4j (Section 8.5's model), the Spring Boot service
hosts graph queries, the frontend renders an explorer, and contract tests
prove BFF↔retrieval interoperability. The spec leaves open the extraction
mechanics, what "graph-augmented retrieval" concretely returns, how Pact
artifacts move between the Node consumer and the JVM provider, and the
Neo4j access style.

## Decision

1. **Extraction** runs per chunk during the ingestion pipeline using the
   configured LLM with a strict JSON instruction and defensive parsing (the
   provider interface stays unchanged; malformed output degrades to "no
   triples", never a failed document). Each entity carries a type from a
   small controlled set and each relation a confidence; triples below **0.6
   confidence are dropped** (Section 9.1's "low-confidence dropped").
   `GRAPH_EXTRACTION=on|off` gates the stage — laptop-mode CPU extraction
   adds minutes per document, and CI/e2e paths that don't exercise the graph
   can skip it. Entity identity is tenant-scoped `(name, type)` via `MERGE`,
   id = short hash of tenant|name|type.
2. **Graph-augmented retrieval**: `/retrieve` responses gain a
   `graph_context` array — for entities mentioned in the returned chunks,
   their strongest `RELATED_TO` neighbors. This gives the agent and callers
   entity-linked context that pure vector search misses (Section 7.3's
   justification) without inventing an unrequested reranking stage.
3. **Pact without a broker**: the BFF's jest consumer tests generate the
   pact file into `packages/contracts/pacts/` (committed); the retrieval
   service verifies it in Gradle via pact-jvm against the running Spring app
   with stubbed adapters. A broker is deployment tooling this repo doesn't
   need; the committed pact keeps the contract reviewable in diffs.
4. **Drivers**: official `neo4j` drivers on both sides, used directly (no
   Spring Data / OGM). Every query is a parameterized Cypher string with an
   explicit `tenant_id` parameter — the Section 8.5 security posture stays
   visible in the code rather than behind a mapper.

## Consequences

Local-model extraction quality bounds graph quality — acceptable and
env-upgradable (better model via `CHAT_MODEL`/provider). Re-ingesting a
document replaces its chunks' mentions and prunes orphaned entities, keeping
the graph idempotent per document version. The committed pact file must be
regenerated when the consumer expectations change (a CI check runs consumer
tests before provider verification, so drift fails visibly). Direct driver
use means hand-written Cypher, reviewed like SQL.
