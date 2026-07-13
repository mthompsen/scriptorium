from agent_service.evaluation import LabeledQuery, evaluate_retrieval


class ScriptedRetrieval:
    """Returns a scripted document-id ranking per query."""

    def __init__(self, rankings: dict[str, list[str]]) -> None:
        self.rankings = rankings

    def retrieve(self, tenant_id: str, query: str, k: int) -> list[dict]:
        return [
            {"chunk_id": f"c-{i}", "document_id": doc_id, "text": "…", "score": 1.0}
            for i, doc_id in enumerate(self.rankings[query][:k])
        ]


def test_recall_and_mrr_over_labeled_queries() -> None:
    retrieval = ScriptedRetrieval(
        {
            "q1": ["doc-a", "doc-b"],  # hit at rank 1 → rr 1.0
            "q2": ["doc-x", "doc-b"],  # hit at rank 2 → rr 0.5
            "q3": ["doc-x", "doc-y"],  # miss → rr 0.0
        }
    )
    queries = [
        LabeledQuery("q1", "doc-a"),
        LabeledQuery("q2", "doc-b"),
        LabeledQuery("q3", "doc-z"),
    ]

    metrics = evaluate_retrieval(retrieval, "tenant-1", queries, k=2)

    assert metrics["query_count"] == 3
    assert metrics["recall_at_k"] == round(2 / 3, 4)
    assert metrics["mrr"] == 0.5  # (1.0 + 0.5 + 0.0) / 3
    assert metrics["per_query"][2]["first_relevant_rank"] is None


def test_k_bounds_the_scanned_results() -> None:
    retrieval = ScriptedRetrieval({"q": ["doc-x", "doc-hit"]})

    metrics = evaluate_retrieval(retrieval, "t", [LabeledQuery("q", "doc-hit")], k=1)

    assert metrics["recall_at_k"] == 0.0  # the hit sits at rank 2, beyond k=1
