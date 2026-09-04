# ADR-0005: Agent loop — streaming, tracing, graph stub, generation eval

- **Status:** Accepted
- **Date:** 2026-07-13

## Context

The agentic layer delivers the bounded tool-use loop with guardrails, token
streaming, and full run tracing. Four things are unsettled: how streaming is
carried end to end, how a trace row links to the chat message that does not
yet exist while the run executes, what `query_knowledge_graph` does before
Neo4j has any data, and how far the generation eval goes.

## Decision

1. **Streaming.** `packages/llm` gains `chat_stream(messages, tools)`,
   yielding provider-neutral events: `content_delta`, `tool_call`, and
   `done` (with usage). Ollama implements it over NDJSON; Bedrock over
   `converse_stream`. The agent exposes `POST /answer` as Server-Sent Events
   (`run_start`, `token`, `tool`, `final`); the BFF re-emits that stream to
   the browser from its POST messages endpoint, and the frontend reads it
   with a `ReadableStream` parser (EventSource cannot POST). A `stream:
   false` JSON mode remains for the eval harness and scripts.
2. **Trace linking.** `agent_runs.message_id` is nullable. The run row is
   created when the loop starts; the BFF persists the assistant message when
   the `final` event arrives and then backfills `message_id` on the run.
   Both services already own Postgres access (Section 4 arrows).
3. **Graph tool.** `query_knowledge_graph` ships as an explicit stub
   returning empty results and a "knowledge graph not populated yet" note. A
   schema-stable stub means the real executor can be swapped in later without
   touching the loop, the trace, or the UI.
4. **Budgets.** Step budget (`AGENT_MAX_STEPS`, default 6) and wall-clock
   budget (`AGENT_TIMEOUT_S`, default 240) are enforced by the loop; hitting
   either forces a grounded refusal, recorded as a `final` step with status
   `refused`.
5. **PII hook.** A pluggable output filter runs on the final answer; the
   default implementation redacts obvious SSN/credit-card patterns and is
   env-toggled (`PII_FILTER=basic|off`). It is a hook by design — real
   deployments plug in a proper classifier.
6. **Generation eval.** `/eval/run` gains `generation: true`: citation
   coverage (fraction of answer sentences carrying a resolving citation) on
   all queries, and LLM-as-judge groundedness on a 5-query subset — CPU
   inference makes the full set impractically slow, and the subset is
   recorded as such in `docs/eval.md`.

## Consequences

Tool activity streams to the browser in real time, which is most of the
perceived value at CPU inference speeds. The nullable `message_id` admits
orphaned runs if the BFF dies between `final` and backfill — visible in the
audit trail rather than hidden, which is acceptable. The graph tool stub keeps the
tool set at four without pulling the graph work forward.
