# AI evaluation — methodology and results

Methodology is defined in `docs/DESIGN.md` Section 9.4: retrieval metrics
(recall@k, MRR) on a fixed labeled set, and generation metrics (citation
coverage, LLM-as-judge groundedness) arriving with the agent loop in M3.

The labeled set lives in `services/agent/eval/` (4 fictional corporate
documents, 10 queries each labeled with the document containing the answer).
`scripts/run-eval.ps1` uploads the corpus, waits for indexing, and calls the
agent's `POST /eval/run`, which executes hybrid retrieval per query and
computes the metrics. Numbers below are pasted verbatim from a real run —
never asserted by hand.

## Retrieval results

**Run: 2026-07-13** — local stack, hybrid BM25 + kNN with RRF fusion,
`nomic-embed-text` embeddings, per-tenant OpenSearch index.

| Metric | Value |
|---|---|
| recall@5 | **1.0** |
| MRR | **1.0** |
| Queries | 10 |
| First relevant rank | 1, for every query |

**Honest caveat:** this is an easy set — four short, topically disjoint
documents. Perfect scores here mean the pipeline works end to end, not that
retrieval quality is solved. A harder set (more documents, overlapping
topics, multi-hop questions) should accompany the M4 graph work; expect the
numbers to drop when it does.

## Generation spot-checks (not yet a metric)

From the same run, manually verified:

- Grounded: "How many days of PTO do employees get?" → correct answer with a
  resolving citation (`[0aa48c7a-2]` → employee-handbook chunk).
- Refusal: "What is the capital of France?" → explicit refusal, `grounded:
  false`, zero citations — the model does not answer from parametric memory.

Citation coverage and groundedness become measured metrics in M3.
