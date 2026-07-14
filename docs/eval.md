# AI evaluation — methodology and results

Methodology is defined in `docs/DESIGN.md` Section 9.4. The labeled set lives
in `services/agent/eval/` (4 fictional corporate documents, 10 queries each
labeled with the document containing the answer). `scripts/run-eval.ps1`
**resets the eval tenant's corpus**, uploads it fresh, waits for indexing,
and calls the agent's `POST /eval/run`. Numbers below are pasted verbatim
from a real run — never asserted by hand.

## Results

**Retrieval (clean harness, 10 queries, k=5)** — hybrid BM25 + kNN with RRF
fusion, `nomic-embed-text` embeddings. Stable across every clean run,
re-confirmed by the final M7 run (2026-07-14): every query at rank 1.

| Metric | Value |
|---|---|
| recall@5 | **1.0** |
| MRR | **1.0** (every query hits at rank 1) |

**Generation (agent loop, 5-query subset)** — by generator/judge model:

| Run | Generator | Judge | Citation coverage | Groundedness |
|---|---|---|---|---|
| 2026-07-13 | `llama3.2:3b` (Ollama, CPU) | `llama3.2:3b` (self-judge) | **0.2** | **0.4** |
| 2026-07-14 (final M7) | `llama3.2:3b` (Ollama, CPU) | `llama3.2:3b` (self-judge) | **0.4667** | **0.0** — see judge-noise note |
| 2026-07-13 | `qwen2.5:7b` (Ollama, CPU) | `llama3.2:3b` | *infeasible on this hardware* — see note | — |
| not run | hosted API model (`LLM_PROVIDER=anthropic` or Bedrock) as generator/judge | independent local model | open improvement path — no API-model run recorded yet | — |

**Judge-noise note (2026-07-14 run):** the self-judge marked all five answers
ungrounded, including two with perfect citation coverage whose answers were
verifiably correct against the corpus. Read together with the 2026-07-13 run
(coverage 0.2, groundedness 0.4), the pair demonstrates the variance of a 3B
self-judge rather than a regression: coverage more than doubled while the
judge collapsed to zero. This is exactly why the caveats below say to track
the trend and swap in an independent, stronger judge before trusting the
groundedness number.

**qwen2.5:7b infeasibility note (honest negative result):** on this CPU the
7B model measured ~13 minutes per eval query through the loop (262s for the
tool-decision call, ~4.5 min for synthesis, plus multi-minute model loads —
a one-word warm-up prompt alone took 3m24s). Eval runs wall-clock-refused
rather than producing quality numbers; the one answer that completed under a
900s budget was correctly grounded and cited, so this is a hardware bound,
not a model-quality result. The 3B row therefore stands as the local
baseline.

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
