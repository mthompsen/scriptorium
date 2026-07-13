"""Retrieval evaluation (DESIGN.md Section 9.4): recall@k and MRR over a
labeled query set. Generation metrics (citation coverage, groundedness)
arrive with the agent loop in M3."""

from dataclasses import dataclass


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
