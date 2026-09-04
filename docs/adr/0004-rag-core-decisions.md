# ADR-0004: RAG core — retrieval placement, models, pipeline execution, citations

- **Status:** Accepted
- **Date:** 2026-07-13

## Context

The RAG core needs the real ingestion pipeline, a retrieval service with
hybrid search, cited answers in chat, and the LLM layer. Four things are open:
where hybrid search lives, given that the Spring Boot service is slated to own
the read path; where the answer path runs, given the agent loop has not been
built yet; which local models and index layout to use; and how the pipeline
executes, given the queue/outbox comes later.

## Decision

1. **Hybrid search is implemented now in the existing Spring Boot retrieval
   service.** Section 7.3 assigns the read path to it unambiguously; the graph
   capabilities and contract tests land on top of it later. Building retrieval
   elsewhere and porting it across would be work for its own sake.
2. **The answer path starts as a single-shot RAG flow in the agent service**
   (`POST /answer`: retrieve → synthesize → cite). The agent loop upgrades
   this endpoint in place; the BFF integration is unchanged.
3. **Local models (Ollama):** `nomic-embed-text` for embeddings (768-dim,
   cosine) and `llama3.2:3b` for generation, both env-overridable. The
   1024-dim mapping in Section 8.4 is illustrative; the index dimension is
   derived from the configured model's actual output. OpenSearch uses one
   index per tenant (`chunks-<tenant_id>`), the isolation option Section 8.4
   prefers. Bedrock adapters (Titan embeddings, Converse API) ship in
   `packages/llm` per Section 9.3; cloud wiring comes with the Terraform work.
4. **Pipeline execution:** `/ingest` stays the synchronous entry point, but
   parsing/chunking/embedding/indexing run on an in-process background worker
   with registry status transitions `stored → processing → indexed | failed`.
   The durable queue + transactional outbox are deferred to the event-driven
   path (S3→Lambda→SQS) rather than landing here as ADR-0003 anticipated; a
   worker crash mid-job can strand a document in `processing`, an accepted
   risk for now (re-upload recovers).
5. **Citations:** the model cites retrieved chunks as `[chunk_id]`; the agent
   strips citations that do not resolve to retrieved chunks (Section 9.2
   output validation, basic form). Chat messages persist citations in a new
   `citations jsonb` column (Section 8.1 marks the schema "extend as needed").

## Consequences

The Java service gains its real responsibility earlier than planned, and the
graph work then extends it rather than creating it. Laptop mode needs a one-time ~2.3 GB model
pull (documented in the runbook; performed by a compose one-shot). Answer
latency on CPU is tens of seconds with the 3B model — acceptable for a demo,
tunable via env. Deferring the queue keeps this change focused; the
ADR-0003 upload path remains otherwise intact.
