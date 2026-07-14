"""Evaluation harness (ARCHITECTURE.md Section 9.4).

Retrieval: recall@k and MRR over a labeled query set.
Generation (M3, ADR-0005): citation coverage over answer sentences, and
LLM-as-judge groundedness on a subset (CPU inference bounds the subset size).
"""

import re
from dataclasses import dataclass

from agent_service.loop import CITATION_PATTERN

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class LabeledQuery:
    query: str
    expected_document_id: str


def evaluate_retrieval(retrieval, tenant_id: str, queries: list[LabeledQuery], k: int) -> dict:
    per_query: list[dict] = []
    hits = 0
    reciprocal_ranks: list[float] = []

    for labeled in queries:
        results = retrieval.retrieve(tenant_id, labeled.query, k)
        rank = next(
            (
                index + 1
                for index, chunk in enumerate(results)
                if chunk["document_id"] == labeled.expected_document_id
            ),
            None,
        )
        if rank is not None:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
        per_query.append(
            {
                "query": labeled.query,
                "expected_document_id": labeled.expected_document_id,
                "first_relevant_rank": rank,
            }
        )

    count = len(queries)
    return {
        "k": k,
        "query_count": count,
        "recall_at_k": round(hits / count, 4) if count else 0.0,
        "mrr": round(sum(reciprocal_ranks) / count, 4) if count else 0.0,
        "per_query": per_query,
    }


def citation_coverage(answer: str) -> float:
    """Fraction of answer sentences carrying at least one citation marker."""
    sentences = [s for s in _SENTENCE_SPLIT.split(answer.strip()) if s.strip()]
    if not sentences:
        return 0.0
    cited = sum(1 for s in sentences if CITATION_PATTERN.search(s))
    return round(cited / len(sentences), 4)


JUDGE_PROMPT = (
    "You are a strict grader. Given a question, an answer, and the excerpts "
    "the answer cites, decide whether every factual claim in the answer is "
    "supported by the excerpts. Reply with exactly one word: YES or NO."
)


def evaluate_generation(loop, llm, tenant_id: str, queries: list[LabeledQuery]) -> dict:
    """Run the agent loop per query and grade the answers."""
    per_query: list[dict] = []
    coverages: list[float] = []
    grounded_votes: list[bool] = []

    for labeled in queries:
        final = _run_to_final(loop, tenant_id, labeled.query)
        coverage = citation_coverage(final["answer"])
        coverages.append(coverage)
        excerpts = "\n".join(f"- {c['snippet']}" for c in final["citations"]) or "(none)"
        verdict = llm.chat(
            [
                {"role": "system", "content": JUDGE_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Question: {labeled.query}\n\nAnswer: {final['answer']}\n\n"
                        f"Cited excerpts:\n{excerpts}"
                    ),
                },
            ]
        )
        judged_grounded = verdict.content.strip().upper().startswith("YES")
        grounded_votes.append(judged_grounded)
        per_query.append(
            {
                "query": labeled.query,
                "citation_coverage": coverage,
                "judge_grounded": judged_grounded,
                "agent_grounded": final["grounded"],
            }
        )

    count = len(queries)
    return {
        "query_count": count,
        "citation_coverage": round(sum(coverages) / count, 4) if count else 0.0,
        "groundedness": round(sum(grounded_votes) / count, 4) if count else 0.0,
        "per_query": per_query,
    }


def _run_to_final(loop, tenant_id: str, question: str) -> dict:
    final: dict = {}
    for event in loop.run(tenant_id, question):
        if event.type == "final":
            final = event.data
    return final
