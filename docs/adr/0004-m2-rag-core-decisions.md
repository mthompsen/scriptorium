# ADR-0004: M2 RAG core — retrieval placement, models, pipeline execution, citations

- **Status:** Accepted
- **Date:** 2026-07-13

## Context

Milestone M2 (DESIGN.md Section 15) requires the real ingestion pipeline,
"retrieval service with hybrid search," cited answers in chat, and the LLM
layer, but leaves four things open: where hybrid search lives given that M4
names the Spring Boot service; where the M2 answer path runs given the agent
loop is M3; which local models and index layout to use; and how the pipeline
executes given the queue/outbox belongs to later milestones.

## Decision

1. **Hybrid search is implemented now in the existing Spring Boot retrieval
   service.** Section 7.3 assigns the read path to it unambiguously; M4's
   bullet adds the graph capabilities and contract tests. Building retrieval
   elsewhere and porting later would be invented scope.
2. **The M2 answer path is a single-shot RAG flow in the agent service**
   (`POST /answer`: retrieve → synthesize → cite). M3 upgrades this endpoint
   in place to the bounded tool-use loop; the BFF integration is unchanged.
3. **Local models (Ollama):** `nomic-embed-text` for embeddings (768-dim,
   cosine) and `llama3.2:3b` for generation, both env-overridable. The
   1024-dim mapping in Section 8.4 is illustrative; the index dimension is
   derived from the configured model's actual output. OpenSearch uses one
   index per tenant (`chunks-<tenant_id>`), the isolation option Section 8.4
   prefers. Bedrock adapters (Titan embeddings, Converse API) ship in
   `packages/llm` per Section 9.3; cloud wiring is exercised in M6.
4. **Pipeline execution:** `/ingest` stays the synchronous entry point, but
   parsing/chunking/embedding/indexing run on an in-process background worker
   with registry status transitions `stored → processing → indexed | failed`.
   The durable queue + transactional outbox are deferred to the event-driven
   path (M6, S3→Lambda→SQS) rather than M2 as ADR-0003 anticipated; a worker
   crash mid-job can strand a document in `processing`, an accepted M2 risk
   (re-upload recovers).
5. **Citations:** the model cites retrieved chunks as `[chunk_id]`; the agent
   strips citations that do not resolve to retrieved chunks (Section 9.2
   output validation, basic form). Chat messages persist citations in a new
   `citations jsonb` column (Section 8.1 marks the schema "extend as needed").

## Consequences

The Java service gains its real responsibility one milestone early, which M4
then extends rather than creates. Laptop mode needs a one-time ~2.3 GB model
pull (documented in the runbook; performed by a compose one-shot). Answer
latency on CPU is tens of seconds with the 3B model — acceptable for a demo,
tunable via env. The deferred queue keeps M2 focused; the ADR-0003 upload
path remains otherwise intact.
