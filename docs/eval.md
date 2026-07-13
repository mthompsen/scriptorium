# AI evaluation — methodology and results

Methodology is defined in `docs/DESIGN.md` Section 9.4. The labeled set lives
in `services/agent/eval/` (4 fictional corporate documents, 10 queries each
labeled with the document containing the answer). `scripts/run-eval.ps1`
**resets the eval tenant's corpus**, uploads it fresh, waits for indexing,
and calls the agent's `POST /eval/run`. Numbers below are pasted verbatim
from a real run — never asserted by hand.

## Results

**Run: 2026-07-13 (clean harness)** — local stack, hybrid BM25 + kNN with RRF
fusion, `nomic-embed-text` embeddings; generation via the M3 agent loop with
`llama3.2:3b` on CPU, judged by the same model.

### Retrieval (10 queries, k=5)

| Metric | Value |
|---|---|
| recall@5 | **1.0** |
| MRR | **1.0** (every query hits at rank 1) |

### Generation (agent loop, 5-query subset)

| Metric | Value |
|---|---|
| Citation coverage (sentences with a resolving citation) | **0.2** |
| Groundedness (LLM-as-judge) | **0.4** |

## Honest caveats

- **Retrieval is an easy set**: four short, topically disjoint documents.
  Perfect scores prove the pipeline, not retrieval quality; a harder set is
  planned alongside the M4 graph work.
- **Eval hermeticity mattered**: before the harness reset corpus state,
  accumulated duplicate uploads pushed MRR as low as 0.27 — measuring
  contamination, not ranking. The runner now tears down and rebuilds the
  corpus per run; the underlying product gap (checksum dedup/versioning on
  upload) is in the backlog.
- **Generation numbers are a 3B-model-on-CPU baseline.** The loop's
  guardrails work (citations validate, off-corpus questions refuse — see the
  smoke), but `llama3.2:3b` frequently writes correct answers *without*
  inline citations, and the same small model judging groundedness is itself
  noisy. Improvement paths: a stronger `CHAT_MODEL` (env-switchable; Bedrock
  in cloud mode), few-shot citation examples in the prompt, and a separate
  judge model. Track the metric trend, not this absolute value.
- Generation judged on 5 of 10 queries (ADR-0005): CPU inference makes the
  full set impractically slow (~2-3 min per query).
